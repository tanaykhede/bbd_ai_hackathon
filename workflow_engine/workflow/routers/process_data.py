from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from workflow.dependencies import get_db
from workflow import schemas
from workflow.doa import process_data as process_data_dao
from workflow.auth import roles_required, get_current_user, User

router = APIRouter(tags=["process_data"])

@router.get("/process-data", response_model=list[schemas.ProcessData], dependencies=[Depends(roles_required("user", "admin"))])
def list_process_data(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if "admin" in user.roles:
        return process_data_dao.list_all_process_data(db)
    return process_data_dao.list_process_data_for_user_cases(db, user.username)
