from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from workflow_engine.workflow import schemas
from workflow_engine.workflow.dependencies import get_db
from workflow_engine.workflow.doa import task_rules as task_rules_dao
from workflow_engine.workflow.auth import get_current_user, roles_required, User
from workflow_engine.workflow.db import models

router = APIRouter(tags=["task_rules"])

@router.get("/task-rules", response_model=list[schemas.TaskRule], dependencies=[Depends(roles_required("admin"))])
def list_task_rules(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(models.TaskRule).all()

@router.get("/task-rules/{taskruleno}", response_model=schemas.TaskRule, dependencies=[Depends(roles_required("admin"))])
def get_task_rule(taskruleno: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(models.TaskRule).filter(models.TaskRule.taskruleno == taskruleno).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task rule not found")
    return obj

@router.post("/task-rules/", response_model=schemas.TaskRule, dependencies=[Depends(roles_required("admin"))])
def create_task_rule(task_rule: schemas.TaskRuleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return task_rules_dao.create_task_rule(db, task_rule, user.username)

@router.put("/task-rules/{taskruleno}", response_model=schemas.TaskRule, dependencies=[Depends(roles_required("admin"))])
def update_task_rule(taskruleno: int, payload: schemas.TaskRuleUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return task_rules_dao.update_task_rule(db, taskruleno, payload, user.username)
