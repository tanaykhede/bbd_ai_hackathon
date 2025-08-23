from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from workflow import schemas
from workflow.dependencies import get_db
from workflow.doa import process_definitions as process_definitions_dao
from workflow.auth import get_current_user, roles_required, User
from workflow.db import models

router = APIRouter(tags=["process_definitions"])

@router.get("/process-definitions", response_model=list[schemas.ProcessDefinition], dependencies=[Depends(roles_required("admin"))])
def list_process_definitions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(models.ProcessDefinition).all()

@router.post("/process-definitions/", response_model=schemas.ProcessDefinition, dependencies=[Depends(roles_required("admin"))])
def create_process_definition(process_definition: schemas.ProcessDefinitionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return process_definitions_dao.create_process_definition(db, process_definition, user.username)
