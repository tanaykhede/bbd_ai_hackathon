from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from workflow_engine.workflow import schemas
from workflow_engine.workflow.dependencies import get_db
from workflow_engine.workflow.doa import steps as steps_dao
from workflow_engine.workflow.auth import get_current_user, roles_required, User

router = APIRouter(tags=["steps"])

@router.get("/steps", response_model=list[schemas.Step], dependencies=[Depends(roles_required("admin"))])
def list_steps(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return steps_dao.list_all_steps(db)

@router.post("/steps/{step_id}/close", response_model=schemas.Step, dependencies=[Depends(roles_required("user", "admin"))])
def close_step(step_id: int, request: schemas.CloseStepRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return steps_dao.close_step(db, step_id, request, user.username)
