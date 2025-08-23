from sqlalchemy.orm import Session
from workflow.db import models
from workflow import schemas
from workflow.doa.utils import save, require_found

def create_task_rule(db: Session, task_rule: schemas.TaskRuleCreate, usrid: str) -> models.TaskRule:
    return save(db, models.TaskRule(**task_rule.dict(), usrid=usrid))

def update_task_rule(db: Session, taskno: int, rule: str, payload: schemas.TaskRuleUpdate, usrid: str) -> models.TaskRule:
    obj = (
        db.query(models.TaskRule)
        .filter(models.TaskRule.taskno == taskno, models.TaskRule.rule == rule)
        .first()
    )
    require_found(obj, "Task rule not found", 404)
    data = payload.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    obj.usrid = usrid
    db.commit()
    db.refresh(obj)
    return obj
