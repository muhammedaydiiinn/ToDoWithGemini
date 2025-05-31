from fastapi import APIRouter , Depends, Path, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from models import Todo
from typing import Annotated
from sqlalchemy.orm import Session
from typing import Annotated
router = APIRouter()


def get_db():
    from database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

class TodoRequest(BaseModel):
    title: str = Field(min_length=3, max_length=1000)
    description: str | None = None
    priority: int = Field(gt=0, le=100)
    completed: bool = Field(default=False)

@router.get("/read_all")
async def read_all(db: db_dependency):
    return db.query(Todo).all()

@router.get("/get_by_id/{todo_id}",status_code=status.HTTP_200_OK)
async def get_by_id(db: db_dependency,todo_id: int = Path(gt=0)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo not found")
    return todo

@router.post("/create_todo", status_code=status.HTTP_201_CREATED)
async def create_todo(todo: TodoRequest, db: db_dependency):
    todo = Todo(**todo.dict())
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo

@router.put("/update_todo/{todo_id}", status_code=status.HTTP_200_OK)
async def update_todo( todo: TodoRequest, db: db_dependency,todo_id: int =Path(ge=0)):
    existing_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not existing_todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    for key, value in todo.dict().items():
        setattr(existing_todo, key, value)

    db.commit()
    db.refresh(existing_todo)
    return existing_todo

@router.delete("/delete_todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency, todo_id: int = Path(gt=0)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    db.delete(todo)
    db.commit()
    return {"detail": "Todo deleted successfully"}