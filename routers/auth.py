from fastapi import APIRouter

router = APIRouter()

@router.get("/read_user")
async def get_user():
    return {"message": "User data retrieved successfully"}
