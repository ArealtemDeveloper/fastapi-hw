"""Integration tests using a disposable PostgreSQL database, never application data.

Run from the project root: PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
The PostgreSQL role from DATABASE_URL_SYNC must be allowed to create databases.
"""

import asyncio
import os
import subprocess
import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import httpx
import jwt
from sqlalchemy import create_engine, func, select, text, update
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]


def setUpModule():
    global app, sessions, async_engine, User, Post, create_access_token, password_hash
    # Some shells set DEBUG=release; tests always use explicit boolean settings.
    os.environ["DEBUG"] = "false"
    from core.settings import Settings

    settings = Settings()
    db_name = "fastapi_hw_test_" + uuid4().hex
    base_url = make_url(settings.database_url_sync)
    admin = create_engine(
        base_url.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    quoted_name = admin.dialect.identifier_preparer.quote(db_name)
    with admin.connect() as connection:
        connection.exec_driver_sql(f"CREATE DATABASE {quoted_name}")

    def cleanup():
        try:
            with admin.connect() as connection:
                connection.exec_driver_sql(f"DROP DATABASE {quoted_name} WITH (FORCE)")
        finally:
            admin.dispose()

    unittest.addModuleCleanup(cleanup)
    test_url = base_url.set(database=db_name)
    os.environ["DATABASE_URL_SYNC"] = test_url.render_as_string(hide_password=False)
    os.environ["DATABASE_URL"] = test_url.set(
        drivername="postgresql+asyncpg"
    ).render_as_string(hide_password=False)
    os.environ["SECRET"] = "integration-test-secret-" * 3
    os.environ["MINIMAL_POST_DEBOUNCE_TIME"] = "60"
    os.environ["TOKEN_TTL"] = "60"
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

    def migrate(*args):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    # Verify upgrade on a populated old schema, including posts without authors.
    migrate("upgrade", "f02000f0bc17")
    sync_engine = create_engine(test_url)
    try:
        with sync_engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO posts (content, created_at, updated_at, likes_count, is_deleted) VALUES ('legacy', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0, false)"
                )
            )
        migrate("upgrade", "head")
        with sync_engine.connect() as connection:
            legacy = connection.execute(
                text("SELECT author_id, parent_id FROM posts WHERE content = 'legacy'")
            ).one()
            assert legacy == (None, None), legacy
        migrate("check")
        migrate("downgrade", "f02000f0bc17")
        migrate("upgrade", "head")
    finally:
        sync_engine.dispose()

    from core.db import async_session as sessions
    from core.db import engine as async_engine
    from main import app
    from posts.model import Post
    from users.jwt import create_access_token
    from users.model import User
    from users.security import hash_password

    password_hash = hash_password("test-password")


class ApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        app.state.settings.minimal_post_debounce_time = 60
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        )
        self.addAsyncCleanup(self.client.aclose)
        self.addAsyncCleanup(async_engine.dispose)
        async with sessions() as session:
            self.user = User(
                name="Автор",
                email=f"{uuid4().hex}@example.com",
                password_hash=password_hash,
            )
            self.other = User(
                name="Другой автор",
                email=f"{uuid4().hex}@example.com",
                password_hash=password_hash,
            )
            session.add_all([self.user, self.other])
            await session.commit()
        self.headers = {"Authorization": f"Bearer {create_access_token(self.user.id)}"}
        self.other_headers = {
            "Authorization": f"Bearer {create_access_token(self.other.id)}"
        }

    async def create(self, headers=None, **body):
        return await self.client.post(
            "/v1/posts/",
            headers=headers or self.headers,
            json={"content": "Пост", **body},
        )

    async def test_authentication_and_me(self):
        for header in [
            None,
            "Basic abc",
            "Bearer broken",
            f"Bearer {create_access_token(2147483647)}",
        ]:
            response = await self.client.get(
                "/v1/users/me", headers={"Authorization": header} if header else {}
            )
            self.assertEqual(response.status_code, 401, response.text)
            self.assertEqual(response.headers["www-authenticate"], "Bearer")
        cases = [
            (
                {
                    "sub": str(self.user.id),
                    "exp": datetime.now(UTC) - timedelta(seconds=1),
                },
                "HS256",
            ),
            ({"sub": str(self.user.id)}, "HS256"),
            ({"sub": "-1", "exp": datetime.now(UTC) + timedelta(minutes=1)}, "HS256"),
            (
                {
                    "sub": str(self.user.id),
                    "exp": datetime.now(UTC) + timedelta(minutes=1),
                },
                "HS384",
            ),
        ]
        for payload, algorithm in cases:
            token = jwt.encode(payload, os.environ["SECRET"], algorithm=algorithm)
            response = await self.client.get(
                "/v1/users/me", headers={"Authorization": f"Bearer {token}"}
            )
            self.assertEqual(response.status_code, 401, response.text)
        me = await self.client.get("/v1/users/me", headers=self.headers)
        self.assertEqual(
            me.json(),
            {"id": self.user.id, "email": self.user.email, "name": self.user.name},
        )
        response = await self.client.post("/v1/posts/", json={"content": "Без токена"})
        self.assertEqual(response.status_code, 401)
        scheme = app.openapi()["components"]["securitySchemes"]["HTTPBearer"]
        self.assertEqual(scheme["scheme"], "bearer")

    async def test_author_is_saved_and_cannot_be_spoofed(self):
        response = await self.create(author_id=self.other.id, parent_id=999)
        self.assertEqual(response.status_code, 201, response.text)
        post = response.json()
        self.assertEqual(post["author_id"], self.user.id)
        self.assertIsNone(post["parent_id"])
        async with sessions() as session:
            stored = await session.get(Post, post["id"])
            self.assertEqual(stored.author_id, self.user.id)
        result = await self.client.get(f"/v1/posts/{post['id']}")
        self.assertEqual(result.json()["author_id"], self.user.id)
        self.assertEqual(result.json()["replies"], [])
        self.assertEqual(
            (
                await self.client.delete(
                    f"/v1/posts/{post['id']}", headers=self.other_headers
                )
            ).status_code,
            403,
        )
        self.assertEqual(
            (
                await self.client.patch(
                    f"/v1/posts/{post['id']}",
                    headers=self.other_headers,
                    json={"content": "Чужой", "likes_count": 0},
                )
            ).status_code,
            403,
        )
        edited = await self.client.patch(
            f"/v1/posts/{post['id']}",
            headers=self.headers,
            json={"content": "Изменён", "likes_count": 0},
        )
        self.assertEqual(edited.status_code, 200, edited.text)
        self.assertEqual(edited.json()["content"], "Изменён")
        self.assertGreaterEqual(edited.json()["updated_at"], post["updated_at"])

    async def test_direct_replies_and_soft_deletion(self):
        app.state.settings.minimal_post_debounce_time = 0
        root = (await self.create()).json()
        response = await self.client.post(
            f"/v1/posts/{root['id']}/reply",
            headers=self.other_headers,
            json={"content": "Ответ"},
        )
        self.assertEqual(response.status_code, 201, response.text)
        reply = response.json()
        self.assertEqual(reply["parent_id"], root["id"])
        self.assertEqual(reply["author_id"], self.other.id)
        nested = await self.client.post(
            f"/v1/posts/{reply['id']}/reply",
            headers=self.headers,
            json={"content": "Ответ на ответ"},
        )
        self.assertEqual(nested.status_code, 201, nested.text)
        detail = (await self.client.get(f"/v1/posts/{root['id']}")).json()
        self.assertEqual([item["id"] for item in detail["replies"]], [reply["id"]])
        self.assertNotIn("replies", detail["replies"][0])
        deleted = await self.client.delete(
            f"/v1/posts/{reply['id']}", headers=self.other_headers
        )
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(
            (await self.client.get(f"/v1/posts/{root['id']}")).json()["replies"], []
        )
        self.assertEqual(
            (await self.client.get(f"/v1/posts/{reply['id']}")).status_code, 404
        )
        self.assertEqual(
            (
                await self.client.patch(
                    f"/v1/posts/{reply['id']}/like", headers=self.headers
                )
            ).status_code,
            404,
        )
        for target in [reply["id"], 2147483647]:
            response = await self.client.post(
                f"/v1/posts/{target}/reply",
                headers=self.headers,
                json={"content": "Ответ"},
            )
            self.assertEqual(response.status_code, 404, response.text)
        listing = await self.client.get("/v1/posts/?limit=100")
        self.assertEqual(listing.status_code, 200, listing.text)
        self.assertNotIn(reply["id"], [post["id"] for post in listing.json()["posts"]])

    async def test_debounce_shared_with_replies_and_per_author(self):
        root = (await self.create()).json()
        repeat = await self.create()
        self.assertEqual(repeat.status_code, 429, repeat.text)
        self.assertGreater(int(repeat.headers["retry-after"]), 0)
        reply = await self.client.post(
            f"/v1/posts/{root['id']}/reply",
            headers=self.headers,
            json={"content": "Ответ"},
        )
        self.assertEqual(reply.status_code, 429)
        other = await self.client.post(
            f"/v1/posts/{root['id']}/reply",
            headers=self.other_headers,
            json={"content": "Ответ другого автора"},
        )
        self.assertEqual(other.status_code, 201, other.text)
        self.assertEqual(
            (await self.create(headers=self.other_headers)).status_code, 429
        )
        await self.client.delete(f"/v1/posts/{root['id']}", headers=self.headers)
        self.assertEqual((await self.create()).status_code, 429)
        # Move only test data past the interval instead of sleeping a minute.
        async with sessions() as session:
            await session.execute(
                update(Post)
                .where(Post.id == root["id"])
                .values(
                    created_at=datetime.now(UTC).replace(tzinfo=None)
                    - timedelta(seconds=61)
                )
            )
            await session.commit()
        self.assertEqual((await self.create()).status_code, 201)

    async def test_simultaneous_first_posts_do_not_bypass_debounce(self):
        responses = await asyncio.gather(self.create(), self.create())
        self.assertEqual(
            sorted(response.status_code for response in responses),
            [201, 429],
            [r.text for r in responses],
        )
        async with sessions() as session:
            count = await session.scalar(
                select(func.count())
                .select_from(Post)
                .where(Post.author_id == self.user.id)
            )
        self.assertEqual(count, 1)

    async def test_failed_creation_and_validation_do_not_consume_interval(self):
        missing = await self.client.post(
            "/v1/posts/2147483647/reply",
            headers=self.headers,
            json={"content": "Ответ"},
        )
        self.assertEqual(missing.status_code, 404)
        for content in ["   ", "x" * 281]:
            response = await self.create(content=content)
            self.assertEqual(response.status_code, 422)
        self.assertEqual((await self.create()).status_code, 201)

    async def test_registration_token_and_login(self):
        email = f"{uuid4().hex}@example.com"
        registered = await self.client.post(
            "/v1/users/register",
            json={"email": email, "name": "Новый", "password": "test-password"},
        )
        self.assertEqual(registered.status_code, 201, registered.text)
        header = {"Authorization": "Bearer " + registered.json()["token"]}
        me = await self.client.get("/v1/users/me", headers=header)
        self.assertEqual(me.status_code, 200, me.text)
        self.assertEqual(me.json()["name"], "Новый")
        self.assertEqual(me.json()["email"], email)
        login = await self.client.post(
            "/v1/users/login", json={"email": email, "password": "test-password"}
        )
        self.assertEqual(login.status_code, 200, login.text)
        bad = await self.client.post(
            "/v1/users/login", json={"email": email, "password": "incorrect"}
        )
        self.assertEqual(bad.status_code, 401)

    async def test_long_passwords_are_rejected_before_bcrypt(self):
        for password in ["a" * 73, "я" * 37]:
            for path, body in [
                (
                    "/v1/users/register",
                    {"name": "Новый", "email": self.user.email, "password": password},
                ),
                ("/v1/users/login", {"email": self.user.email, "password": password}),
            ]:
                response = await self.client.post(path, json=body)
                self.assertEqual(response.status_code, 422, response.text)

    async def test_concurrent_likes_are_not_lost(self):
        created = (await self.create()).json()
        responses = await asyncio.gather(
            *[
                self.client.patch(
                    f"/v1/posts/{created['id']}/like", headers=self.other_headers
                )
                for _ in range(5)
            ]
        )
        self.assertEqual([response.status_code for response in responses], [200] * 5)
        detail = await self.client.get(f"/v1/posts/{created['id']}")
        self.assertEqual(detail.json()["likes_count"], 5)


if __name__ == "__main__":
    unittest.main()
