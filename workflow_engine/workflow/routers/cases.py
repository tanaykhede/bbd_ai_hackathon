from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from workflow import schemas
from workflow.db import models
from workflow.dependencies import get_db

router = APIRouter(tags=["cases"])

@router.post("/cases/", response_model=schemas.Case)
def create_case(case: schemas.CaseCreate, db: Session = Depends(get_db)):
    db_case = models.Case(client_id=case.client_id, client_type=case.client_type, usrid=case.usrid)
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case

@router.get("/cases/{case_id}", response_model=schemas.Case)
def read_case(case_id: int, db: Session = Depends(get_db)):
    db_case = db.query(models.Case).filter(models.Case.caseno == case_id).first()
    if db_case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return db_case

# User Case Creation with Process and Initial Step
@router.post("/create-case-and-process/", response_model=schemas.Case)
def create_case_and_process(case: schemas.CaseCreate, process_type_no: int, db: Session = Depends(get_db)):
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
