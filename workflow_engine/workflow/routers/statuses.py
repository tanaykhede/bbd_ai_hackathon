from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy.orm import Session

from workflow import schemas
from workflow.dependencies import get_db
from workflow.auth import get_current_user, roles_required, User
from workflow.doa import statuses as statuses_dao

router = APIRouter(tags=["status"])


@router.get("/statuses", response_model=list[schemas.Status], dependencies=[Depends(roles_required("user", "admin"))])
def list_statuses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return statuses_dao.list_all_statuses(db)


@router.get("/statuses/{statusno}", response_model=schemas.Status, dependencies=[Depends(roles_required("user", "admin"))])
def get_status(statusno: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return statuses_dao.get_status(db, statusno)


@router.post("/statuses/", response_model=schemas.Status, status_code=http_status.HTTP_201_CREATED, dependencies=[Depends(roles_required("admin"))])
def create_status(payload: schemas.StatusBase, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return statuses_dao.create_status(db, payload, user.username)


