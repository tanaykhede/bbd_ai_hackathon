from sqlalchemy.orm import Session
from workflow.db import models
from workflow import schemas

def create_task_rule(db: Session, task_rule: schemas.TaskRuleCreate) -> models.TaskRule:
    db_task_rule = models.TaskRule(**task_rule.dict(), usrid="user")
    db.add(db_task_rule)
    db.commit()
    db.refresh(db_task_rule)
    return db_task_rule
