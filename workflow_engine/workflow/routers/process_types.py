from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from workflow_engine.workflow import schemas
from workflow_engine.workflow.dependencies import get_db
from workflow_engine.workflow.doa import process_types as process_types_dao
from workflow_engine.workflow.auth import get_current_user, roles_required, User
from workflow_engine.workflow.db import models

router = APIRouter(tags=["process_types"])

@router.get("/process-types", response_model=list[schemas.ProcessType], dependencies=[Depends(roles_required("admin"))])
def list_process_types(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(models.ProcessType).all()

@router.get("/process-types/{process_type_no}", response_model=schemas.ProcessType, dependencies=[Depends(roles_required("admin"))])
def get_process_type(process_type_no: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(models.ProcessType).filter(models.ProcessType.process_type_no == process_type_no).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Process type not found")
    return obj

@router.post("/process-types/", response_model=schemas.ProcessType, dependencies=[Depends(roles_required("admin"))])
def create_process_type(process_type: schemas.ProcessTypeCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return process_types_dao.create_process_type(db, process_type, user.username)
