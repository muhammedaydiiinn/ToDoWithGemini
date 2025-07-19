from symtable import Class

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel
from starlette import status

from models import User
from typing import Annotated
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import timedelta, datetime, timezone

router = APIRouter()

SECRET_KEY = "0ec9r60e2ial90i1ccl2sp4y03wce77szm36ixa7b0vv64raukgnxjfmkwnd0x89"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    to_encode = {
        "sub": username,
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + expires_delta
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


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

class Token(BaseModel):
    access_token: str
    token_type: str

def authanticate_user(username: str, password: str, db):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

outh_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_current_user(token: Annotated[str, Depends(outh_bearer)], db: db_dependency):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user_id = payload.get("user_id")
        role = payload.get("role")
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
        user = db.query(User).filter(User.username == username, User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
        return {"username": username, "user_id": user_id, "role": role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

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


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: db_dependency):
    user = authanticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token(
        username=user.username,
        user_id=user.id,
        role=user.role,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}
