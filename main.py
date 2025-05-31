from fastapi import FastAPI
from models import Base
from database import engine

from routers.auth import router as auth
from routers.todo import router as todo

app = FastAPI()
app.include_router(auth, prefix="/auth", tags=["auth"])
app.include_router(todo, prefix="/todo", tags=["todo"])

Base.metadata.create_all(bind=engine)