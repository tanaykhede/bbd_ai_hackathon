from sqlalchemy.orm import Session
from workflow.db import models
from workflow import schemas
from workflow.doa.utils import save

def create_status(db: Session, status: schemas.StatusCreate, usrid: str) -> models.Status:
    return save(db, models.Status(statusno=status.statusno, description=status.description, usrid=usrid))

def list_all_statuses(db: Session) -> list[models.Status]:
    return db.query(models.Status).all()
