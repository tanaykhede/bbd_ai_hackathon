from sqlalchemy.orm import Session
from workflow_engine.workflow import schemas
from workflow_engine.workflow.db import models
from workflow_engine.workflow.doa.utils import save, require_found

def create_process_type(db: Session, process_type: schemas.ProcessTypeCreate, usrid: str) -> models.ProcessType:
    return save(db, models.ProcessType(**process_type.dict(), usrid=usrid))

def update_process_type(db: Session, process_type_no: int, payload: schemas.ProcessTypeUpdate, usrid: str) -> models.ProcessType:
    obj = db.query(models.ProcessType).filter(models.ProcessType.process_type_no == process_type_no).first()
    require_found(obj, "Process type not found", 404)
    data = payload.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    obj.usrid = usrid
    db.commit()
    db.refresh(obj)
    return obj
