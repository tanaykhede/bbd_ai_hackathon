from sqlalchemy.orm import Session
from fastapi import HTTPException
from workflow.db import models
from workflow import schemas

def create_process(db: Session, process: schemas.ProcessCreate) -> models.Process:
    db_process = models.Process(**process.dict(), usrid="user")
    db.add(db_process)
    db.commit()
    db.refresh(db_process)
    return db_process

def create_process_data_for_process(
    db: Session,
    process_no: int,
    process_data: schemas.ProcessDataCreate,
) -> models.ProcessData:
    db_process = db.query(models.Process).filter(models.Process.processno == process_no).first()
    if not db_process:
        raise HTTPException(status_code=404, detail="Process not found")

    db_process_data = models.ProcessData(**process_data.dict(), processno=process_no, usrid="user")
    db.add(db_process_data)
    db.commit()
    db.refresh(db_process_data)
    return db_process_data
