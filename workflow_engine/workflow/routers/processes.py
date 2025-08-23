from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from workflow import schemas
from workflow.dependencies import get_db
from workflow.doa import processes as processes_dao

router = APIRouter(tags=["processes"])

@router.post("/processes/", response_model=schemas.Process)
def create_process(process: schemas.ProcessCreate, db: Session = Depends(get_db)):
    return processes_dao.create_process(db, process)

@router.post("/processes/{process_no}/data/", response_model=schemas.ProcessData)
def create_process_data_for_process(
    process_no: int,
    process_data: schemas.ProcessDataCreate,
    db: Session = Depends(get_db),
):
    return processes_dao.create_process_data_for_process(db, process_no, process_data)
