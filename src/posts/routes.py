from fastapi import APIRouter, Depends
from .schemas import PostPath, CreatePostRequest, UpdatePostRequest, UpdatePostResponse

router = APIRouter(prefix="/posts")

@router.get("/{post_id}")
def get_post(path: PostPath = Depends()):
    return { "content": path.post_id}

@router.post("/")
def create_post(data: CreatePostRequest):
    return data

@router.patch("/{post_id}", response_model=UpdatePostResponse)
def update_post(data: UpdatePostRequest, path: PostPath = Depends()):
    return UpdatePostResponse(
        id=path.post_id,
        content=data.content
    )

@router.delete("/{post_id}")
def delete_post(path: PostPath = Depends()):
    return { "removed_post": path.post_id }