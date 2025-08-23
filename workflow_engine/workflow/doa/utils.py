from fastapi import HTTPException
from sqlalchemy.orm import Session

def save(db: Session, instance):
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance

def require_found(obj, detail: str = "Not found", status_code: int = 404):
    if not obj:
        raise HTTPException(status_code=status_code, detail=detail)
    return obj

def ensure_task_exists(db: Session, taskno: int, process_definition_no: int, description: str, usrid: str, reference: str | None = None):
    from workflow.db import models
    task = db.query(models.Task).filter(models.Task.taskno == taskno).first()
    if task:
        return task
    task = models.Task(
        taskno=taskno,
        process_definition_no=process_definition_no,
        description=description,
        reference=reference,
        usrid=usrid,
    )
    return save(db, task)

def ensure_default_task_rule(db: Session, taskno: int, usrid: str, next_task_no: int | None = None):
    from workflow.db import models
    rule = db.query(models.TaskRule).filter(
        models.TaskRule.taskno == taskno,
        models.TaskRule.rule == "default",
    ).first()
    if rule:
        return rule
    rule = models.TaskRule(
        taskno=taskno,
        rule="default",
        next_task_no=next_task_no if next_task_no is not None else taskno,
        usrid=usrid,
    )
    return save(db, rule)
