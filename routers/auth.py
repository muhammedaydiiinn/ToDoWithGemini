from fastapi import APIRouter, Depends
from pydantic import BaseModel

from models import User
from typing import Annotated
from sqlalchemy.orm import Session
from passlib.context import CryptContext
router = APIRouter()

def get_db():
    from database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str


@router.post("/register")
async def register(create_user_request: CreateUserRequest, db: db_dependency):
    user = User(
        username=create_user_request.username,
        email=create_user_request.email,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        role=create_user_request.role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User created successfully", "user_id": user.id}



