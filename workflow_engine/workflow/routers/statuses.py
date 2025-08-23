from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from workflow.dependencies import get_db
from workflow import schemas
from workflow.doa import statuses as statuses_dao
from workflow.auth import roles_required, get_current_user, User

router = APIRouter(tags=["statuses"])

@router.get("/statuses", response_model=list[schemas.Status], dependencies=[Depends(roles_required("admin"))])
def list_statuses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return statuses_dao.list_all_statuses(db)

@router.post("/statuses/", response_model=schemas.Status, dependencies=[Depends(roles_required("admin"))])
def create_status(status: schemas.StatusCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return statuses_dao.create_status(db, status, user.username)
