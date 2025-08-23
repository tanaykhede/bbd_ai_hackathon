from sqlalchemy.orm import Session
from workflow.db import models
from workflow import schemas

def create_process_type(db: Session, process_type: schemas.ProcessTypeCreate) -> models.ProcessType:
    db_process_type = models.ProcessType(**process_type.dict(), usrid="user")
    db.add(db_process_type)
    db.commit()
    db.refresh(db_process_type)
    return db_process_type
