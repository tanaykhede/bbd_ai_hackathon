from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from workflow import schemas
from workflow.db import models
from workflow.dependencies import get_db

router = APIRouter(tags=["process_types"])

@router.post("/process-types/", response_model=schemas.ProcessType)
def create_process_type(process_type: schemas.ProcessTypeCreate, db: Session = Depends(get_db)):
    db_process_type = models.ProcessType(**process_type.dict(), usrid="user")
    db.add(db_process_type)
    db.commit()
    db.refresh(db_process_type)
    return db_process_type
