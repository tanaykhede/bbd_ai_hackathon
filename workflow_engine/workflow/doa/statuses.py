from sqlalchemy.orm import Session
from workflow.db import models
from workflow import schemas
from workflow.doa.utils import save, require_found


def list_all_statuses(db: Session) -> list[models.Status]:
    return db.query(models.Status).all()


def get_status(db: Session, statusno: int) -> models.Status:
    db_status = db.query(models.Status).filter(models.Status.statusno == statusno).first()
    require_found(db_status, "Status not found", 404)
    return db_status


def create_status(db: Session, status: schemas.StatusBase, usrid: str) -> models.Status:
    return save(db, models.Status(description=status.description, usrid=usrid))

