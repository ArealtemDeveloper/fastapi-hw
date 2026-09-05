from fastapi import FastAPI
from posts import routes as posts_routes

app = FastAPI()
app.include_router(posts_routes.router)
