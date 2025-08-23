from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from workflow import schemas
from workflow.dependencies import get_db
from workflow.doa import process_data_types as process_data_types_dao
from workflow.auth import get_current_user, roles_required, User

router = APIRouter(tags=["process_data_types"])

@router.get("/process-data-types", response_model=list[schemas.ProcessDataType], dependencies=[Depends(roles_required("admin"))])
def list_process_data_types(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return process_data_types_dao.list_all_process_data_types(db)

@router.post("/process-data-types/", response_model=schemas.ProcessDataType, dependencies=[Depends(roles_required("admin"))])
def create_process_data_type(process_data_type: schemas.ProcessDataTypeCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return process_data_types_dao.create_process_data_type(db, process_data_type, user.username)
