from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from workflow import schemas
from workflow.dependencies import get_db
from workflow.doa import process_data_types as process_data_types_dao

router = APIRouter(tags=["process_data_types"])

@router.post("/process-data-types/", response_model=schemas.ProcessDataType)
def create_process_data_type(process_data_type: schemas.ProcessDataTypeCreate, db: Session = Depends(get_db)):
    return process_data_types_dao.create_process_data_type(db, process_data_type)
