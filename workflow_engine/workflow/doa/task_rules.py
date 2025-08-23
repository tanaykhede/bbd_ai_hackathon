from sqlalchemy.orm import Session
from workflow.db import models
from workflow import schemas
from workflow.doa.utils import save

def create_task_rule(db: Session, task_rule: schemas.TaskRuleCreate, usrid: str) -> models.TaskRule:
    return save(db, models.TaskRule(**task_rule.dict(), usrid=usrid))
