from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from workflow.db import models, database
from workflow import schemas
import datetime

#models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/cases/", response_model=schemas.Case)
def create_case(case: schemas.CaseCreate, db: Session = Depends(get_db)):
    db_case = models.Case(client_id=case.client_id, client_type=case.client_type)
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case

@app.get("/cases/{case_id}", response_model=schemas.Case)
def read_case(case_id: int, db: Session = Depends(get_db)):
    db_case = db.query(models.Case).filter(models.Case.caseno == case_id).first()
    if db_case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return db_case

@app.post("/processes/", response_model=schemas.Process)
def create_process(process: schemas.ProcessCreate, db: Session = Depends(get_db)):
    db_process = models.Process(**process.dict())
    db.add(db_process)
    db.commit()
    db.refresh(db_process)
    return db_process

# Admin Endpoints
@app.post("/tasks/", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    db_task = models.Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.post("/process-definitions/", response_model=schemas.ProcessDefinition)
def create_process_definition(process_definition: schemas.ProcessDefinitionCreate, db: Session = Depends(get_db)):
    db_process_definition = models.ProcessDefinition(**process_definition.dict())
    db.add(db_process_definition)
    db.commit()
    db.refresh(db_process_definition)
    return db_process_definition

@app.post("/process-types/", response_model=schemas.ProcessType)
def create_process_type(process_type: schemas.ProcessTypeCreate, db: Session = Depends(get_db)):
    db_process_type = models.ProcessType(**process_type.dict())
    db.add(db_process_type)
    db.commit()
    db.refresh(db_process_type)
    return db_process_type

@app.post("/process-data-types/", response_model=schemas.ProcessDataType)
def create_process_data_type(process_data_type: schemas.ProcessDataTypeCreate, db: Session = Depends(get_db)):
    db_process_data_type = models.ProcessDataType(**process_data_type.dict())
    db.add(db_process_data_type)
    db.commit()
    db.refresh(db_process_data_type)
    return db_process_data_type

@app.post("/task-rules/", response_model=schemas.TaskRule)
def create_task_rule(task_rule: schemas.TaskRuleCreate, db: Session = Depends(get_db)):
    db_task_rule = models.TaskRule(**task_rule.dict())
    db.add(db_task_rule)
    db.commit()
    db.refresh(db_task_rule)
    return db_task_rule

@app.post("/processes/{process_no}/data/", response_model=schemas.ProcessData)
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

# User Case Creation with Process and Initial Step
@app.post("/create-case-and-process/", response_model=schemas.Case)
def create_case_and_process(case: schemas.CaseCreate, process_type_no: int, db: Session = Depends(get_db)):
    # Create Case
    db_case = models.Case(client_id=case.client_id, client_type=case.client_type, usrid="user") # Assuming a user
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
        usrid="user"
    )
    db.add(db_process)
    db.commit()
    db.refresh(db_process)

    # Create Initial Step
    initial_step = models.Step(
        processno=db_process.processno,
        taskno=process_definition.start_task_no,
        status_no=busy_status_no,
        usrid="user"
    )
    db.add(initial_step)
    db.commit()
    db.refresh(initial_step)

    return db_case

@app.post("/steps/{step_id}/close", response_model=schemas.Step)
def close_step(step_id: int, request: schemas.CloseStepRequest, db: Session = Depends(get_db)):
    db_step = db.query(models.Step).filter(models.Step.stepno == step_id).first()
    if not db_step:
        raise HTTPException(status_code=404, detail="Step not found")

    if db_step.status_no != 1: # Assuming 'busy' is 1
        raise HTTPException(status_code=400, detail="Step is not busy")

    task_rules = db.query(models.TaskRule).filter(models.TaskRule.taskno == db_step.taskno).all()

    next_task_no = None
    for rule in task_rules:
        # Simple rule evaluation: check if rule (as a key) exists in the request data
        if rule.rule in request.rule_data:
            next_task_no = rule.next_task_no
            break
    
    if next_task_no is None:
        # Default next task if no rules match
        # This part of the logic needs to be more robust based on actual requirements.
        # For now, we'll assume a 'default' rule must exist if no other rules match.
        default_rule = db.query(models.TaskRule).filter(models.TaskRule.taskno == db_step.taskno, models.TaskRule.rule == 'default').first()
        if default_rule:
            next_task_no = default_rule.next_task_no
        else:
            raise HTTPException(status_code=400, detail="No matching rule and no default task found")


    # Close current step (assuming 'completed' is statusno 2)
    completed_status_no = 2
    db_step.status_no = completed_status_no
    db_step.date_ended = datetime.datetime.utcnow()
    db.commit()

    # Create next step
    # Assuming 'busy' is statusno 1
    busy_status_no = 1
    new_step = models.Step(
        processno=db_step.processno,
        taskno=next_task_no,
        status_no=busy_status_no,
        usrid="user" # assuming a user
    )
    db.add(new_step)
    db.commit()
    db.refresh(new_step)

    return new_step
