from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from workflow import schemas
from workflow.db import models
from workflow.dependencies import get_db

router = APIRouter(tags=["tasks"])

@router.post("/tasks/", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    db_task = models.Task(**task.dict(), usrid="user")
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task
