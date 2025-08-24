from typing import Generator
from workflow_engine.workflow.db.database import SessionLocal

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
