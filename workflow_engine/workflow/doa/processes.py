from sqlalchemy.orm import Session
from workflow_engine.workflow.db import models
from workflow_engine.workflow import schemas
from workflow_engine.workflow.doa.utils import save, require_found
from workflow_engine.workflow.doa import process_data as process_data_dao

def create_process(db: Session, process: schemas.ProcessCreate, usrid: str) -> models.Process:
    return save(db, models.Process(**process.dict(), usrid=usrid))

def create_process_data_for_process(
    db: Session,
    process_no: int,
    process_data: schemas.ProcessDataCreate,
    usrid: str,
) -> models.ProcessData:
    db_process = db.query(models.Process).filter(models.Process.processno == process_no).first()
    require_found(db_process, "Process not found", 404)
    return process_data_dao.create_process_data(db, processno=process_no, process_data=process_data, usrid=usrid)

def complete_process(db: Session, process_no: int, usrid: str) -> models.Process:
    import datetime
    from fastapi import HTTPException

    db_process = db.query(models.Process).filter(models.Process.processno == process_no).first()
    require_found(db_process, "Process not found", 404)

    completed_status = db.query(models.Status).filter(models.Status.description.ilike("complete")).first()
    if not completed_status:
        raise HTTPException(status_code=500, detail="Required status 'complete' not configured")

    db_process.status_no = completed_status.statusno
    db_process.date_ended = datetime.datetime.utcnow()
    db.commit()
    db.refresh(db_process)
    return db_process

def list_all_processes(db: Session) -> list[models.Process]:
    return db.query(models.Process).all()

