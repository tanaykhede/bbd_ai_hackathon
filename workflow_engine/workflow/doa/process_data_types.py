from sqlalchemy.orm import Session
from workflow.db import models
from workflow import schemas
from workflow.doa.utils import save, require_found

def create_process_data_type(db: Session, process_data_type: schemas.ProcessDataTypeCreate, usrid: str) -> models.ProcessDataType:
    return save(db, models.ProcessDataType(**process_data_type.dict(), usrid=usrid))

def list_all_process_data_types(db: Session) -> list[models.ProcessDataType]:
    return db.query(models.ProcessDataType).all()

def update_process_data_type(db: Session, process_data_type_no: int, payload: schemas.ProcessDataTypeUpdate, usrid: str) -> models.ProcessDataType:
    obj = db.query(models.ProcessDataType).filter(models.ProcessDataType.process_data_type_no == process_data_type_no).first()
    require_found(obj, "Process data type not found", 404)
    data = payload.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    obj.usrid = usrid
    db.commit()
    db.refresh(obj)
    return obj
