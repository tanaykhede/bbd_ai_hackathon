from sqlalchemy.orm import Session
from fastapi import HTTPException
from workflow.db import models
from workflow import schemas
from workflow.doa.utils import save
from workflow.doa import processes as processes_dao, steps as steps_dao


def get_case(db: Session, case_id: int) -> models.Case | None:
    return db.query(models.Case).filter(models.Case.caseno == case_id).first()

def list_cases_by_user(db: Session, usrid: str) -> list[models.Case]:
    return db.query(models.Case).filter(models.Case.usrid == usrid).all()

def list_all_cases(db: Session) -> list[models.Case]:
    return db.query(models.Case).all()

def create_case(db: Session, case: schemas.CaseCreate, process_type_no: int, usrid: str) -> models.Case:
    # Create Case
    db_case = models.Case(client_id=case.client_id, client_type=case.client_type, usrid=usrid)
    db.add(db_case)
    db.flush()  # assign caseno

    # Get Process Definition
    process_definition = db.query(models.ProcessDefinition).filter(
        models.ProcessDefinition.process_type_no == process_type_no,
        models.ProcessDefinition.is_active == True
    ).first()
    if not process_definition:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Active process definition for this type not found")

    # Resolve 'busy' status from the Status table
    busy_status = db.query(models.Status).filter(models.Status.description.ilike("busy")).first()
    if not busy_status:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Required status 'busy' not configured")
    busy_status_no = busy_status.statusno

    # Create Process
    db_process = models.Process(
        case_no=db_case.caseno,
        status_no=busy_status_no,
        process_type_no=process_type_no,
        usrid=usrid,
    )
    db.add(db_process)
    db.flush()  # assign processno

    # Create Initial Step
    initial_step = models.Step(
        processno=db_process.processno,
        taskno=process_definition.start_task_no,
        status_no=busy_status_no,
        usrid=usrid,
    )
    db.add(initial_step)

    # Commit once to keep the whole operation atomic
    db.commit()

    # Refresh and return created case after commit
    db.refresh(db_case)
    return db_case
