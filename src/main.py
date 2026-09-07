from fastapi import FastAPI
from posts import routes as posts_routes

app = FastAPI(
    title="Posts Api",
    description="Проект постов",
    version="0.0.1",
    openapi_tags=[{"name": "Posts", "description": "Управление постами"}],
)
app.include_router(posts_routes.router)
