from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from workflow_engine.workflow import schemas
from workflow_engine.workflow.dependencies import get_db
from workflow_engine.workflow.doa import processes as processes_dao
from workflow_engine.workflow.auth import get_current_user, roles_required, User

router = APIRouter(tags=["processes"])

@router.get("/processes", response_model=list[schemas.Process], dependencies=[Depends(roles_required("admin"))])
def list_processes(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return processes_dao.list_all_processes(db)

@router.post("/processes/", response_model=schemas.Process, dependencies=[Depends(roles_required("admin"))])
def create_process(process: schemas.ProcessCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return processes_dao.create_process(db, process, user.username)

@router.post("/processes/{process_no}/data/", response_model=schemas.ProcessData, dependencies=[Depends(roles_required("user", "admin"))])
def create_process_data_for_process(
    process_no: int,
    process_data: schemas.ProcessDataCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return processes_dao.create_process_data_for_process(db, process_no, process_data, user.username)
