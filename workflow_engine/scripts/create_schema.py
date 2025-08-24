import os
import sys
from sqlalchemy import create_engine, text

URL = os.getenv("SQLALCHEMY_DATABASE_URL") or (sys.argv[1] if len(sys.argv) > 1 else None)
if not URL:
    raise SystemExit("SQLALCHEMY_DATABASE_URL not set and no URL provided. Pass it as arg 1.")

# Normalize scheme if needed
if URL.startswith("postgres://"):
    URL = "postgresql://" + URL[len("postgres://"):]

engine = create_engine(URL, pool_pre_ping=True)

with engine.begin() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS workflow_db"))
    # Optional: ensure public remains accessible after
    # conn.execute(text("ALTER ROLE CURRENT_USER IN DATABASE CURRENT_DATABASE SET search_path TO workflow_db, public"))
    sp = conn.execute(text("SHOW search_path")).scalar()
    cs = conn.execute(text("SELECT current_schema()"))
    current_schema = cs.scalar() if cs else None
    print(f"Created/ensured schema. search_path={sp}; current_schema={current_schema}")
