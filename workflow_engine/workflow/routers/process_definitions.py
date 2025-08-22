from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from workflow import schemas
from workflow.db import models
from workflow.dependencies import get_db

router = APIRouter(tags=["process_definitions"])

@router.post("/process-definitions/", response_model=schemas.ProcessDefinition)
def create_process_definition(process_definition: schemas.ProcessDefinitionCreate, db: Session = Depends(get_db)):
    db_process_definition = models.ProcessDefinition(**process_definition.dict(), usrid="user")
    db.add(db_process_definition)
    db.commit()
    db.refresh(db_process_definition)
    return db_process_definition
