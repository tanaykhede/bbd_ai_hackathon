from sqlalchemy.orm import Session
from workflow.db import models
from workflow import schemas

def create_process_data_type(db: Session, process_data_type: schemas.ProcessDataTypeCreate) -> models.ProcessDataType:
    db_process_data_type = models.ProcessDataType(**process_data_type.dict(), usrid="user")
    db.add(db_process_data_type)
    db.commit()
    db.refresh(db_process_data_type)
    return db_process_data_type
