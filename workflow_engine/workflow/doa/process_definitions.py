from sqlalchemy.orm import Session
from workflow.db import models
from workflow import schemas
from workflow.doa.utils import save, ensure_task_exists, ensure_default_task_rule, require_found

def create_process_definition(db: Session, process_definition: schemas.ProcessDefinitionCreate, usrid: str) -> models.ProcessDefinition:
    # Persist only fields that belong to ProcessDefinition. We will create the start task and set its number after.
    pd_data = {
        "process_type_no": process_definition.process_type_no,
        "start_task_no": None,
        "version": process_definition.version,
        "is_active": process_definition.is_active,
    }
    db_process_definition = save(db, models.ProcessDefinition(**pd_data, usrid=usrid))

    # Create the start task for this process definition using the provided description
    new_task = models.Task(
        process_definition_no=db_process_definition.process_definition_no,
        description=process_definition.start_task_description,
        reference='',
        usrid=usrid,
    )
    new_task = save(db, new_task)

    # Update the process definition with the created task number
    db_process_definition.start_task_no = new_task.taskno
    db.add(db_process_definition)
    db.commit()
    db.refresh(db_process_definition)

    start_task_no = new_task.taskno

    # Ensure a default task rule exists for the start task
    ensure_default_task_rule(db, taskno=start_task_no, usrid=usrid, next_task_no=start_task_no)

    return db_process_definition

def update_process_definition(db: Session, pd_no: int, payload: schemas.ProcessDefinitionUpdate, usrid: str) -> models.ProcessDefinition:
    obj = db.query(models.ProcessDefinition).filter(models.ProcessDefinition.process_definition_no == pd_no).first()
    require_found(obj, "Process definition not found", 404)
    data = payload.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    obj.usrid = usrid
    db.commit()
    db.refresh(obj)
    return obj
