from sqlalchemy.orm import Session
from workflow.db import models
from workflow import schemas

def create_task(db: Session, task: schemas.TaskCreate) -> models.Task:
    db_task = models.Task(**task.dict(), usrid="user")
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task
