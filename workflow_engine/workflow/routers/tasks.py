from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from workflow import schemas
from workflow.dependencies import get_db
from workflow.doa import tasks as tasks_dao
from workflow.auth import get_current_user, roles_required, User
from workflow.db import models

router = APIRouter(tags=["tasks"])

@router.get("/tasks", response_model=list[schemas.Task], dependencies=[Depends(roles_required("admin"))])
def list_tasks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(models.Task).all()

@router.post("/tasks/", response_model=schemas.Task, dependencies=[Depends(roles_required("admin"))])
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return tasks_dao.create_task(db, task, user.username)
