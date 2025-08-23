from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from workflow import schemas
from workflow.dependencies import get_db
from workflow.doa import task_rules as task_rules_dao

router = APIRouter(tags=["task_rules"])

@router.post("/task-rules/", response_model=schemas.TaskRule)
def create_task_rule(task_rule: schemas.TaskRuleCreate, db: Session = Depends(get_db)):
    return task_rules_dao.create_task_rule(db, task_rule)
