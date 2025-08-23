from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from workflow import schemas
from workflow.dependencies import get_db
from workflow.doa import cases as cases_dao
from workflow.auth import get_current_user, roles_required, User

router = APIRouter(tags=["cases"])

@router.post("/cases/", response_model=schemas.Case, dependencies=[Depends(roles_required("user", "admin"))])
def create_case(case: schemas.CaseCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return cases_dao.create_case(db, case, user.username)

@router.get("/cases/{case_id}", response_model=schemas.Case, dependencies=[Depends(roles_required("user", "admin"))])
def read_case(case_id: int, db: Session = Depends(get_db)):
    db_case = cases_dao.get_case(db, case_id)
    if db_case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return db_case

# User Case Creation with Process and Initial Step
@router.post("/create-case-and-process/", response_model=schemas.Case, dependencies=[Depends(roles_required("user", "admin"))])
def create_case_and_process(case: schemas.CaseCreate, process_type_no: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return cases_dao.create_case_and_process(db, case, process_type_no, user.username)
