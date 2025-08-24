from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from workflow import schemas
from workflow.dependencies import get_db
from workflow.doa import steps as steps_dao
from workflow.auth import get_current_user, roles_required, User

router = APIRouter(tags=["steps"])

@router.get("/steps", response_model=list[schemas.Step], dependencies=[Depends(roles_required("admin"))])
def list_steps(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return steps_dao.list_all_steps(db)

@router.post("/steps/{step_id}/close", response_model=schemas.Step, dependencies=[Depends(roles_required("user", "admin"))])
def close_step(step_id: int, request: schemas.CloseStepRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return steps_dao.close_step(db, step_id, request, user.username)

@router.get("/cases/{case_no}/current-step", response_model=schemas.Step, dependencies=[Depends(roles_required("user", "admin"))])
def get_current_step_for_case(case_no: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from fastapi import HTTPException
    from workflow.db import models
    busy_status = db.query(models.Status).filter(models.Status.description.ilike("busy")).first()
    if not busy_status:
        raise HTTPException(status_code=500, detail="Required status 'busy' not configured")
    busy_status_no = busy_status.statusno
    step = (
        db.query(models.Step)
        .join(models.Process, models.Step.processno == models.Process.processno)
        .filter(models.Process.case_no == case_no, models.Step.status_no == busy_status_no)
        .order_by(models.Step.stepno.desc())
        .first()
    )
    if not step:
        raise HTTPException(status_code=404, detail="No current step for this case")
    return step

@router.get("/cases/{case_no}/steps", response_model=list[schemas.Step], dependencies=[Depends(roles_required("user", "admin"))])
def list_steps_for_case(case_no: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from workflow.db import models
    q = (
        db.query(models.Step)
        .join(models.Process, models.Step.processno == models.Process.processno)
        .filter(models.Process.case_no == case_no)
        .order_by(models.Step.date_started.asc())
    )
    # Non-admin users can only see their own cases' steps
    if "admin" not in user.roles:
        q = (
            q.join(models.Case, models.Process.case_no == models.Case.caseno)
             .filter(models.Case.usrid == user.username)
        )
    return q.all()
