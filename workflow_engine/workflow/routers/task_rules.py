from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from workflow import schemas
from workflow.db import models
from workflow.dependencies import get_db

router = APIRouter(tags=["task_rules"])

@router.post("/task-rules/", response_model=schemas.TaskRule)
def create_task_rule(task_rule: schemas.TaskRuleCreate, db: Session = Depends(get_db)):
    db_task_rule = models.TaskRule(**task_rule.dict(), usrid="user")
    db.add(db_task_rule)
    db.commit()
    db.refresh(db_task_rule)
    return db_task_rule
