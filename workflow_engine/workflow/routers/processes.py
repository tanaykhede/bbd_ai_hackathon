from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from workflow import schemas
from workflow.db import models
from workflow.dependencies import get_db

router = APIRouter(tags=["processes"])

@router.post("/processes/", response_model=schemas.Process)
def create_process(process: schemas.ProcessCreate, db: Session = Depends(get_db)):
    db_process = models.Process(**process.dict(), usrid="user")
    db.add(db_process)
    db.commit()
    db.refresh(db_process)
    return db_process

@router.post("/processes/{process_no}/data/", response_model=schemas.ProcessData)
def create_process_data_for_process(
    process_no: int,
    process_data: schemas.ProcessDataCreate,
    db: Session = Depends(get_db),
):
    db_process = db.query(models.Process).filter(models.Process.processno == process_no).first()
    if not db_process:
        raise HTTPException(status_code=404, detail="Process not found")

    db_process_data = models.ProcessData(**process_data.dict(), processno=process_no, usrid="user")
    db.add(db_process_data)
    db.commit()
    db.refresh(db_process_data)
    return db_process_data
