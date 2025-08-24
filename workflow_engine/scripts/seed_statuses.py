import datetime
from workflow_engine.workflow.db.database import SessionLocal
from workflow_engine.workflow.db import models


def main():
    db = SessionLocal()
    try:
        existing = {s.description for s in db.query(models.Status).all()}
        for desc in ["busy", "inprogress", "complete"]:
            if desc not in existing:
                db.add(models.Status(description=desc, usrid="system", tmstamp=datetime.datetime.utcnow()))
        db.commit()
        print("Seeded statuses (busy, inprogress, complete)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
