from sqlalchemy.orm import Session
from workflow.db import models
from workflow import schemas
from workflow.doa.utils import save

def create_process_data(db: Session, processno: int, process_data: schemas.ProcessDataCreate, usrid: str) -> models.ProcessData:
    return save(db, models.ProcessData(**process_data.dict(), processno=processno, usrid=usrid))

def list_all_process_data(db: Session) -> list[models.ProcessData]:
    return db.query(models.ProcessData).all()

def list_process_data_for_user_cases(db: Session, usrid: str) -> list[models.ProcessData]:
    # Join ProcessData -> Process -> Case and filter by case.usrid
    return (
        db.query(models.ProcessData)
        .join(models.Process, models.ProcessData.processno == models.Process.processno)
        .join(models.Case, models.Process.case_no == models.Case.caseno)
        .filter(models.Case.usrid == usrid)
        .all()
    )

def list_process_data_for_case(db: Session, case_no: int) -> list[models.ProcessData]:
    # All process data for a given case (admin scope)
    return (
        db.query(models.ProcessData)
        .join(models.Process, models.ProcessData.processno == models.Process.processno)
        .filter(models.Process.case_no == case_no)
        .all()
    )

def list_process_data_for_case_and_user(db: Session, case_no: int, usrid: str) -> list[models.ProcessData]:
    # Process data for a given case limited to the requesting user (non-admin scope)
    return (
        db.query(models.ProcessData)
        .join(models.Process, models.ProcessData.processno == models.Process.processno)
        .join(models.Case, models.Process.case_no == models.Case.caseno)
        .filter(models.Process.case_no == case_no, models.Case.usrid == usrid)
        .all()
    )
