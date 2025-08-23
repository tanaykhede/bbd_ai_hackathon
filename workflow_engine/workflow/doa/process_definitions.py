from sqlalchemy.orm import Session
from workflow.db import models
from workflow import schemas

def create_process_definition(db: Session, process_definition: schemas.ProcessDefinitionCreate) -> models.ProcessDefinition:
    db_process_definition = models.ProcessDefinition(**process_definition.dict(), usrid="user")
    db.add(db_process_definition)
    db.commit()
    db.refresh(db_process_definition)
    return db_process_definition
