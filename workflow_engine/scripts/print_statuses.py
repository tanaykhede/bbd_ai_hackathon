import os
import sys
from sqlalchemy import create_engine, text

URL = os.getenv("SQLALCHEMY_DATABASE_URL") or (sys.argv[1] if len(sys.argv) > 1 else None)
if not URL:
    raise SystemExit("Provide DATABASE URL via env or arg1")
if URL.startswith("postgres://"):
    URL = "postgresql://" + URL[len("postgres://"):]

engine = create_engine(URL, pool_pre_ping=True)
with engine.connect() as conn:
    rows = conn.execute(text("select statusno, description from status order by statusno"))
    out = [(r[0], r[1]) for r in rows]
    print(out)
