from fastapi import FastAPI
from posts import routes as posts_routes
from core.settings import Settings


def create_app():
    settings = Settings()  # type: ignore[call-arg]
    app = FastAPI(
        title="Posts Api",
        description="Проект постов",
        version="0.0.1",
        openapi_tags=[{"name": "Posts", "description": "Управление постами"}],
    )

    app.state.settings = settings
    app.include_router(posts_routes.router)
    return app


app = create_app()
