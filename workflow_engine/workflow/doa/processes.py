from sqlalchemy.orm import Session
from workflow.db import models
from workflow import schemas
from workflow.doa.utils import save, require_found
from workflow.doa import process_data as process_data_dao

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
