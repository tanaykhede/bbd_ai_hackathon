from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from workflow import schemas
from workflow.dependencies import get_db
from workflow.doa import task_rules as task_rules_dao
from workflow.auth import get_current_user, roles_required, User
from workflow.db import models

router = APIRouter(tags=["task_rules"])

@router.get("/task-rules", response_model=list[schemas.TaskRule], dependencies=[Depends(roles_required("admin"))])
def list_task_rules(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(models.TaskRule).all()

@router.post("/task-rules/", response_model=schemas.TaskRule, dependencies=[Depends(roles_required("admin"))])
def create_task_rule(task_rule: schemas.TaskRuleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return task_rules_dao.create_task_rule(db, task_rule, user.username)
