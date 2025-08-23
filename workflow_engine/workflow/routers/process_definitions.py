from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from workflow import schemas
from workflow.dependencies import get_db
from workflow.doa import process_definitions as process_definitions_dao

router = APIRouter(tags=["process_definitions"])

@router.post("/process-definitions/", response_model=schemas.ProcessDefinition)
def create_process_definition(process_definition: schemas.ProcessDefinitionCreate, db: Session = Depends(get_db)):
    return process_definitions_dao.create_process_definition(db, process_definition)
