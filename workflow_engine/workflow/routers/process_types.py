from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from workflow import schemas
from workflow.dependencies import get_db
from workflow.doa import process_types as process_types_dao
from workflow.auth import get_current_user, roles_required, User

router = APIRouter(tags=["process_types"])

@router.post("/process-types/", response_model=schemas.ProcessType, dependencies=[Depends(roles_required("admin"))])
def create_process_type(process_type: schemas.ProcessTypeCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return process_types_dao.create_process_type(db, process_type, user.username)
