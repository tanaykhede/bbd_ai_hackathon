from sqlalchemy.orm import Session
from workflow.db import models
from workflow import schemas
from workflow.doa.utils import save, ensure_task_exists, ensure_default_task_rule

def create_process_definition(db: Session, process_definition: schemas.ProcessDefinitionCreate, usrid: str) -> models.ProcessDefinition:
    # Persist only fields that belong to ProcessDefinition
    pd_data = {
        "process_type_no": process_definition.process_type_no,
        "start_task_no": process_definition.start_task_no,
        "version": process_definition.version,
        "is_active": process_definition.is_active,
    }
    db_process_definition = save(db, models.ProcessDefinition(**pd_data, usrid=usrid))

    # Ensure the start task exists for this process definition, with user-provided description
    start_task_no = process_definition.start_task_no
    ensure_task_exists(
        db=db,
        taskno=start_task_no,
        process_definition_no=db_process_definition.process_definition_no,
        description=process_definition.start_task_description,
        usrid=usrid,
        reference=None,
    )

    # Ensure a default task rule exists for the start task
    ensure_default_task_rule(db, taskno=start_task_no, usrid=usrid, next_task_no=start_task_no)

    return db_process_definition
