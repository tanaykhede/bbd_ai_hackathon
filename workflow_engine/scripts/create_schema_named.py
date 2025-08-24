import os
import sys
from sqlalchemy import create_engine, text

if len(sys.argv) < 2:
    raise SystemExit("Usage: create_schema_named.py <schema_name> [DATABASE_URL]")

schema = sys.argv[1]
url = os.getenv("SQLALCHEMY_DATABASE_URL") or (sys.argv[2] if len(sys.argv) > 2 else None)
if not url:
    raise SystemExit("Provide SQLALCHEMY_DATABASE_URL via env or as second arg")
if url.startswith("postgres://"):
    url = "postgresql://" + url[len("postgres://"):]

engine = create_engine(url, pool_pre_ping=True)
with engine.begin() as conn:
    conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
    sp = conn.execute(text("SHOW search_path")).scalar()
    cs = conn.execute(text("SELECT current_schema()")).scalar()
    print(f"Ensured schema '{schema}'. search_path={sp}; current_schema={cs}")
