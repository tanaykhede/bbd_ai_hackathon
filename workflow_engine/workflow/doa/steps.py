import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from workflow.db import models
from workflow import schemas
from workflow.doa.utils import save, require_found

def create_step(db: Session, processno: int, taskno: int, status_no: int, usrid: str) -> models.Step:
    return save(db, models.Step(
        processno=processno,
        taskno=taskno,
        status_no=status_no,
        usrid=usrid
    ))

def close_step(db: Session, step_id: int, request: schemas.CloseStepRequest, usrid: str) -> models.Step:
    db_step = db.query(models.Step).filter(models.Step.stepno == step_id).first()
    require_found(db_step, "Step not found", 404)

    if db_step.status_no != 1:  # Assuming 'busy' is 1
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
        default_rule = db.query(models.TaskRule).filter(
            models.TaskRule.taskno == db_step.taskno, models.TaskRule.rule == 'default'
        ).first()
        if default_rule:
            next_task_no = default_rule.next_task_no
        else:
            raise HTTPException(status_code=400, detail="No matching rule and no default task found")

    # Close current step (assuming 'completed' is statusno 2)
    completed_status_no = 2
    db_step.status_no = completed_status_no
    db_step.date_ended = datetime.datetime.utcnow()
    db.commit()

    # Create next step (assuming 'busy' is statusno 1)
    busy_status_no = 1
    return create_step(
        db=db,
        processno=db_step.processno,
        taskno=next_task_no,
        status_no=busy_status_no,
        usrid=usrid
    )
