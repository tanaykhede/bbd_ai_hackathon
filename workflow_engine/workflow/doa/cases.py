from sqlalchemy.orm import Session
from fastapi import HTTPException
from workflow.db import models
from workflow import schemas

def create_case(db: Session, case: schemas.CaseCreate) -> models.Case:
    db_case = models.Case(client_id=case.client_id, client_type=case.client_type, usrid=case.usrid)
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case

def get_case(db: Session, case_id: int) -> models.Case | None:
    return db.query(models.Case).filter(models.Case.caseno == case_id).first()

def create_case_and_process(db: Session, case: schemas.CaseCreate, process_type_no: int) -> models.Case:
    # Create Case
    db_case = models.Case(client_id=case.client_id, client_type=case.client_type, usrid=case.usrid)
    db.add(db_case)
    db.commit()
    db.refresh(db_case)

    # Get Process Definition
    process_definition = db.query(models.ProcessDefinition).filter(
        models.ProcessDefinition.process_type_no == process_type_no,
        models.ProcessDefinition.is_active == True
    ).first()
    if not process_definition:
        raise HTTPException(status_code=404, detail="Active process definition for this type not found")

    # Assuming status 'busy' has statusno = 1
    busy_status_no = 1

    # Create Process
    db_process = models.Process(
        case_no=db_case.caseno,
        status_no=busy_status_no,
        process_type_no=process_type_no,
        usrid=case.usrid
    )
    db.add(db_process)
    db.commit()
    db.refresh(db_process)

    # Create Initial Step
    initial_step = models.Step(
        processno=db_process.processno,
        taskno=process_definition.start_task_no,
        status_no=busy_status_no,
        usrid=case.usrid
    )
    db.add(initial_step)
    db.commit()
    db.refresh(initial_step)

    return db_case
