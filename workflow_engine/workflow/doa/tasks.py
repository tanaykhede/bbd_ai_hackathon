from sqlalchemy.orm import Session
from workflow.db import models
from workflow import schemas
from workflow.doa.utils import save, require_found

def create_task(db: Session, task: schemas.TaskCreate, usrid: str) -> models.Task:
    return save(db, models.Task(**task.dict(), usrid=usrid))

def update_task(db: Session, taskno: int, payload: schemas.TaskUpdate, usrid: str) -> models.Task:
    obj = db.query(models.Task).filter(models.Task.taskno == taskno).first()
    require_found(obj, "Task not found", 404)
    data = payload.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    obj.usrid = usrid
    db.commit()
    db.refresh(obj)
    return obj
