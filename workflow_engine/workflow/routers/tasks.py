from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from workflow import schemas
from workflow.dependencies import get_db
from workflow.doa import tasks as tasks_dao

router = APIRouter(tags=["tasks"])

@router.post("/tasks/", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    return tasks_dao.create_task(db, task)
