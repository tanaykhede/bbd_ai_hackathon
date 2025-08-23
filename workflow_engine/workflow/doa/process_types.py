from sqlalchemy.orm import Session
from workflow.db import models
from workflow import schemas
from workflow.doa.utils import save

def create_process_type(db: Session, process_type: schemas.ProcessTypeCreate, usrid: str) -> models.ProcessType:
    return save(db, models.ProcessType(**process_type.dict(), usrid=usrid))
