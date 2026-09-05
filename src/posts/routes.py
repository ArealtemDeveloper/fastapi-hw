from fastapi import APIRouter, Request

router = APIRouter(prefix="/posts")

@router.get("/{post_id}")
def get_post(post_id: int):
    pass

@router.post("/")
def create_post(request: Request):
    pass

@router.patch("/{post_id}")
def update_post(post_id: int, request: Request):
    pass

@router.delete("/{post_id}")
def delete_post(post_id: int):
    pass