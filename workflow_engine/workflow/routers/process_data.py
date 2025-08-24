from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from workflow.dependencies import get_db
from workflow import schemas
from workflow.doa import process_data as process_data_dao
from workflow.auth import roles_required, get_current_user, User
from workflow.db import models

router = APIRouter(tags=["process_data"])

@router.get("/process-data", response_model=list[schemas.ProcessData], dependencies=[Depends(roles_required("user", "admin"))])
def list_process_data(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if "admin" in user.roles:
        return process_data_dao.list_all_process_data(db)
    return process_data_dao.list_process_data_for_user_cases(db, user.username)

@router.get("/cases/{case_no}/process-data", response_model=list[schemas.ProcessData], dependencies=[Depends(roles_required("user", "admin"))])
def list_process_data_for_case(case_no: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if "admin" in user.roles:
        return process_data_dao.list_process_data_for_case(db, case_no)
    return process_data_dao.list_process_data_for_case_and_user(db, case_no, user.username)

@router.put("/process-data/{process_data_no}", response_model=schemas.ProcessData, dependencies=[Depends(roles_required("user", "admin"))])
def update_process_data(process_data_no: int, payload: schemas.ProcessDataUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Authorize: non-admin users can only update data in their own cases
    q = (
        db.query(models.ProcessData)
        .join(models.Process, models.ProcessData.processno == models.Process.processno)
        .join(models.Case, models.Process.case_no == models.Case.caseno)
        .filter(models.ProcessData.process_data_no == process_data_no)
    )
    if "admin" not in user.roles:
        q = q.filter(models.Case.usrid == user.username)
    pd = q.first()
    if not pd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Process data not found")
    return process_data_dao.update_process_data(db, process_data_no, payload, user.username)
