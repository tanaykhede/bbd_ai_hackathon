from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from workflow_engine.workflow import schemas
from workflow_engine.workflow.db import models
from workflow_engine.workflow.dependencies import get_db
from workflow_engine.workflow.doa import tasks as tasks_dao
from workflow_engine.workflow.auth import get_current_user, roles_required, User

router = APIRouter(tags=["tasks"])

@router.get("/tasks", response_model=list[schemas.Task], dependencies=[Depends(roles_required("admin"))])
def list_tasks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(models.Task).all()

@router.get("/tasks/{taskno}", response_model=schemas.Task, dependencies=[Depends(roles_required("admin"))])
def get_task(taskno: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(models.Task).filter(models.Task.taskno == taskno).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return obj

@router.post("/tasks/", response_model=schemas.Task, dependencies=[Depends(roles_required("admin"))])
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return tasks_dao.create_task(db, task, user.username)

@router.put("/tasks/{taskno}", response_model=schemas.Task, dependencies=[Depends(roles_required("admin"))])
def update_task(taskno: int, payload: schemas.TaskUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return tasks_dao.update_task(db, taskno, payload, user.username)
