from sqlalchemy.orm import Session
from workflow.db import models
from workflow import schemas
from workflow.doa.utils import save

def create_process_data(db: Session, processno: int, process_data: schemas.ProcessDataCreate, usrid: str) -> models.ProcessData:
    return save(db, models.ProcessData(**process_data.dict(), processno=processno, usrid=usrid))
