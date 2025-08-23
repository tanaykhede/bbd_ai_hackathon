from sqlalchemy.orm import Session
from workflow.db import models
from workflow import schemas
from workflow.doa.utils import save

def create_task(db: Session, task: schemas.TaskCreate, usrid: str) -> models.Task:
    return save(db, models.Task(**task.dict(), usrid=usrid))
