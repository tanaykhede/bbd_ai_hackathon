from fastapi import APIRouter, Depends, HTTPException, status
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

@router.get("/task-rules/{taskno}/{rule}", response_model=schemas.TaskRule, dependencies=[Depends(roles_required("admin"))])
def get_task_rule(taskno: int, rule: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = (
        db.query(models.TaskRule)
        .filter(models.TaskRule.taskno == taskno, models.TaskRule.rule == rule)
        .first()
    )
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task rule not found")
    return obj

@router.post("/task-rules/", response_model=schemas.TaskRule, dependencies=[Depends(roles_required("admin"))])
def create_task_rule(task_rule: schemas.TaskRuleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return task_rules_dao.create_task_rule(db, task_rule, user.username)

@router.put("/task-rules/{taskno}/{rule}", response_model=schemas.TaskRule, dependencies=[Depends(roles_required("admin"))])
def update_task_rule(taskno: int, rule: str, payload: schemas.TaskRuleUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return task_rules_dao.update_task_rule(db, taskno, rule, payload, user.username)
