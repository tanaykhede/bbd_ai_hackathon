import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from pathlib import Path

load_dotenv()
url = os.getenv("SQLALCHEMY_DATABASE_URL")
if not url:
    raise SystemExit("SQLALCHEMY_DATABASE_URL not set")
if url.startswith("postgres://"):
    url = "postgresql://" + url[len("postgres://"):]
# Ensure search_path=workflow_db
if "options=-csearch_path=workflow_db" not in url:
    sep = '&' if '?' in url else '?'
    url = f"{url}{sep}options=-csearch_path=workflow_db"

engine = create_engine(url, pool_pre_ping=True)

TABLES = [
    'status', 'process_types', 'process_definitions', 'tasks', 'task_rules',
    'cases', 'processes', 'steps', 'process_data_types', 'process_data'
]

report_lines = []
with engine.begin() as conn:
    for t in TABLES:
        cnt = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        line = f"{t}: {cnt}"
        print(line)
        report_lines.append(line)

    pts = [r[0] for r in conn.execute(text("SELECT description FROM process_types ORDER BY process_type_no"))]
    line = "process_types: " + ", ".join(pts)
    print(line)
    report_lines.append(line)

# Write report next to workflow_engine as seed_report.txt
report_path = Path(__file__).resolve().parents[1] / 'seed_report.txt'
report_path.write_text("\n".join(report_lines), encoding='utf-8')
print(f"Wrote report to {report_path}")
