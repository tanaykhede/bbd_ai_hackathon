from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from workflow import schemas
from workflow.db import models
from workflow.dependencies import get_db

router = APIRouter(tags=["process_data_types"])

@router.post("/process-data-types/", response_model=schemas.ProcessDataType)
def create_process_data_type(process_data_type: schemas.ProcessDataTypeCreate, db: Session = Depends(get_db)):
    db_process_data_type = models.ProcessDataType(**process_data_type.dict(), usrid="user")
    db.add(db_process_data_type)
    db.commit()
    db.refresh(db_process_data_type)
    return db_process_data_type
