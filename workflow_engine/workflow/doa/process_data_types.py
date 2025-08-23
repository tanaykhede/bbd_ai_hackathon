from sqlalchemy.orm import Session
from workflow.db import models
from workflow import schemas
from workflow.doa.utils import save

def create_process_data_type(db: Session, process_data_type: schemas.ProcessDataTypeCreate, usrid: str) -> models.ProcessDataType:
    return save(db, models.ProcessDataType(**process_data_type.dict(), usrid=usrid))
