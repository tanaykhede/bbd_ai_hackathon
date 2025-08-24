import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
url = os.getenv("SQLALCHEMY_DATABASE_URL")
if not url:
    raise SystemExit("SQLALCHEMY_DATABASE_URL not set")
if url.startswith("postgres://"):
    url = "postgresql://" + url[len("postgres://"):]

# Connect without forcing search_path so we can drop/recreate the schema safely
engine = create_engine(url, pool_pre_ping=True)

SCHEMA = "workflow_db"

with engine.connect() as conn:
    conn = conn.execution_options(isolation_level="AUTOCOMMIT")
    conn.execute(text(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE"))
    conn.execute(text(f"CREATE SCHEMA {SCHEMA}"))
    # Verify
    r = conn.execute(text("SELECT schema_name FROM information_schema.schemata WHERE schema_name=:s"), {"s": SCHEMA}).scalar()
    if r != SCHEMA:
        raise SystemExit("Failed to recreate schema")
    print(f"Reset schema '{SCHEMA}' successfully.")
