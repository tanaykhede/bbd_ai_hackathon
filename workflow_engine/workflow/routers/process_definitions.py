from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from workflow_engine.workflow import schemas
from workflow_engine.workflow.dependencies import get_db
from workflow_engine.workflow.doa import process_definitions as process_definitions_dao
from workflow_engine.workflow.auth import get_current_user, roles_required, User
from workflow_engine.workflow.db import models

router = APIRouter(tags=["process_definitions"])

@router.get("/process-definitions", response_model=list[schemas.ProcessDefinition], dependencies=[Depends(roles_required("admin"))])
def list_process_definitions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(models.ProcessDefinition).all()

@router.get("/process-definitions/{process_definition_no}", response_model=schemas.ProcessDefinition, dependencies=[Depends(roles_required("admin"))])
def get_process_definition(process_definition_no: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(models.ProcessDefinition).filter(models.ProcessDefinition.process_definition_no == process_definition_no).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Process definition not found")
    return obj

@router.post("/process-definitions/", response_model=schemas.ProcessDefinition, dependencies=[Depends(roles_required("admin"))])
def create_process_definition(process_definition: schemas.ProcessDefinitionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return process_definitions_dao.create_process_definition(db, process_definition, user.username)

@router.put("/process-definitions/{process_definition_no}", response_model=schemas.ProcessDefinition, dependencies=[Depends(roles_required("admin"))])
def update_process_definition(process_definition_no: int, payload: schemas.ProcessDefinitionUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return process_definitions_dao.update_process_definition(db, process_definition_no, payload, user.username)
