from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from workflow import schemas
from workflow.dependencies import get_db
from workflow.doa import process_data_types as process_data_types_dao
from workflow.auth import get_current_user, roles_required, User
from workflow.db import models

router = APIRouter(tags=["process_data_types"])

@router.get("/process-data-types", response_model=list[schemas.ProcessDataType], dependencies=[Depends(roles_required("admin"))])
def list_process_data_types(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return process_data_types_dao.list_all_process_data_types(db)

@router.get("/process-data-types/{process_data_type_no}", response_model=schemas.ProcessDataType, dependencies=[Depends(roles_required("admin"))])
def get_process_data_type(process_data_type_no: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(models.ProcessDataType).filter(models.ProcessDataType.process_data_type_no == process_data_type_no).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Process data type not found")
    return obj

@router.post("/process-data-types/", response_model=schemas.ProcessDataType, dependencies=[Depends(roles_required("admin"))])
def create_process_data_type(process_data_type: schemas.ProcessDataTypeCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return process_data_types_dao.create_process_data_type(db, process_data_type, user.username)

@router.put("/process-data-types/{process_data_type_no}", response_model=schemas.ProcessDataType, dependencies=[Depends(roles_required("admin"))])
def update_process_data_type(process_data_type_no: int, payload: schemas.ProcessDataTypeUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return process_data_types_dao.update_process_data_type(db, process_data_type_no, payload, user.username)
