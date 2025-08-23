from sqlalchemy.orm import Session
from fastapi import HTTPException
from workflow.db import models
from workflow import schemas
from workflow.doa.utils import save
from workflow.doa import processes as processes_dao, steps as steps_dao

def create_case(db: Session, case: schemas.CaseCreate, usrid: str) -> models.Case:
    return save(db, models.Case(client_id=case.client_id, client_type=case.client_type, usrid=usrid))

def get_case(db: Session, case_id: int) -> models.Case | None:
    return db.query(models.Case).filter(models.Case.caseno == case_id).first()

def create_case_and_process(db: Session, case: schemas.CaseCreate, process_type_no: int, usrid: str) -> models.Case:
    # Create Case
    db_case = save(db, models.Case(client_id=case.client_id, client_type=case.client_type, usrid=usrid))

    # Get Process Definition
    process_definition = db.query(models.ProcessDefinition).filter(
        models.ProcessDefinition.process_type_no == process_type_no,
        models.ProcessDefinition.is_active == True
    ).first()
    if not process_definition:
        raise HTTPException(status_code=404, detail="Active process definition for this type not found")

    # Assuming status 'busy' has statusno = 1
    busy_status_no = 1

    # Create Process via DAO
    db_process = processes_dao.create_process(
        db,
        schemas.ProcessCreate(
            case_no=db_case.caseno,
            status_no=busy_status_no,
            process_type_no=process_type_no,
        ),
        usrid,
    )

    # Create Initial Step via DAO
    steps_dao.create_step(
        db=db,
        processno=db_process.processno,
        taskno=process_definition.start_task_no,
        status_no=busy_status_no,
        usrid=usrid,
    )

    return db_case
