import os
import random
import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
url = os.getenv("SQLALCHEMY_DATABASE_URL")
if not url:
    raise SystemExit("SQLALCHEMY_DATABASE_URL not set")
if url.startswith("postgres://"):
    url = "postgresql://" + url[len("postgres://"):]
# Force search_path to workflow_db for seeding
if "options=-csearch_path=workflow_db" not in url:
    sep = '&' if '?' in url else '?'
    url = f"{url}{sep}options=-csearch_path=workflow_db"

engine = create_engine(url, pool_pre_ping=True)

# Deterministic-ish seeds for reproducibility
random.seed(42)
now = datetime.datetime.utcnow()

PT_PROCUREMENT = "Procurement"
PT_DISPUTE = "Dispute"

with engine.begin() as conn:
    # Seed statuses (ensure three basic ones)
    statuses = ["busy", "inprogress", "complete"]
    for desc in statuses:
        conn.execute(text("INSERT INTO status (statusno, description, tmstamp, usrid) VALUES ((SELECT COALESCE(MAX(statusno),0)+1 FROM status), :d, :ts, 'seed') ON CONFLICT DO NOTHING"), {"d": desc, "ts": now})

    # Seed process types
    def insert_pt(desc):
        row = conn.execute(text("INSERT INTO process_types (process_type_no, description, tmstamp, usrid) VALUES ((SELECT COALESCE(MAX(process_type_no),0)+1 FROM process_types), :d, :ts, 'seed') RETURNING process_type_no"), {"d": desc, "ts": now}).first()
        return row[0]
    pt_map = {}
    for d in [PT_PROCUREMENT, PT_DISPUTE]:
        # Try fetch existing by description
        row = conn.execute(text("SELECT process_type_no FROM process_types WHERE description=:d"), {"d": d}).first()
        pt_map[d] = row[0] if row else insert_pt(d)

    # Helper to create a process definition with a start task and default rule
    def create_process_definition(process_type_no, version):
        pdno = conn.execute(text("INSERT INTO process_definitions (process_definition_no, process_type_no, start_task_no, version, is_active, tmstamp, usrid) VALUES ((SELECT COALESCE(MAX(process_definition_no),0)+1 FROM process_definitions), :pt, NULL, :v, true, :ts, 'seed') RETURNING process_definition_no"), {"pt": process_type_no, "v": version, "ts": now}).scalar()
        start_task_no = conn.execute(text("INSERT INTO tasks (taskno, process_definition_no, description, reference, tmstamp, usrid) VALUES ((SELECT COALESCE(MAX(taskno),0)+1 FROM tasks), :pd, 'Start', NULL, :ts, 'seed') RETURNING taskno"), {"pd": pdno, "ts": now}).scalar()
        conn.execute(text("UPDATE process_definitions SET start_task_no=:t WHERE process_definition_no=:pd"), {"t": start_task_no, "pd": pdno})
        # default rule
        conn.execute(text("INSERT INTO task_rules (taskruleno, taskno, rule, next_task_no, tmstamp, usrid) VALUES ((SELECT COALESCE(MAX(taskruleno),0)+1 FROM task_rules), :t, 'default', NULL, :ts, 'seed') ON CONFLICT DO NOTHING"), {"t": start_task_no, "ts": now})
        return pdno, start_task_no

    # Create up to 10 sample definitions per type
    for d in [PT_PROCUREMENT, PT_DISPUTE]:
        ptno = pt_map[d]
        count = random.randint(2, 4)  # small set
        for i in range(1, count + 1):
            version = f"v{1+i}"
            pdno, start_task = create_process_definition(ptno, version)
            # Add a couple more tasks and rules
            prev = start_task
            for tix in range(random.randint(1, 3)):
                tno = conn.execute(text("INSERT INTO tasks (taskno, process_definition_no, description, reference, tmstamp, usrid) VALUES ((SELECT COALESCE(MAX(taskno),0)+1 FROM tasks), :pd, :desc, :ref, :ts, 'seed') RETURNING taskno"), {"pd": pdno, "desc": f"Task {tix+1}", "ref": f"REF-{random.randint(100,999)}", "ts": now}).scalar()
                conn.execute(text("INSERT INTO task_rules (taskruleno, taskno, rule, next_task_no, tmstamp, usrid) VALUES ((SELECT COALESCE(MAX(taskruleno),0)+1 FROM task_rules), :prev, :rule, :next, :ts, 'seed') ON CONFLICT DO NOTHING"), {"prev": prev, "rule": f"cond_{tix+1}", "next": tno, "ts": now})
                prev = tno

    # Create a few cases and processes with steps and process data
    # Collect some ids
    status_ids = [r[0] for r in conn.execute(text("SELECT statusno FROM status ORDER BY statusno LIMIT 10"))]
    pd_ids = [r[0] for r in conn.execute(text("SELECT process_definition_no FROM process_definitions ORDER BY process_definition_no LIMIT 10"))]

    # data types
    pdtype_descs = ["string", "number", "date", "currency"]
    for d in pdtype_descs:
        conn.execute(text("INSERT INTO process_data_types (process_data_type_no, description, tmstamp, usrid) VALUES ((SELECT COALESCE(MAX(process_data_type_no),0)+1 FROM process_data_types), :d, :ts, 'seed') ON CONFLICT DO NOTHING"), {"d": d, "ts": now})
    pdtype_ids = [r[0] for r in conn.execute(text("SELECT process_data_type_no FROM process_data_types ORDER BY process_data_type_no LIMIT 10"))]

    # create up to 10 cases
    for cix in range(random.randint(6, 10)):
        case_no = conn.execute(text("INSERT INTO cases (caseno, client_id, client_type, date_created, tmstamp, usrid) VALUES ((SELECT COALESCE(MAX(caseno),0)+1 FROM cases), :cid, :ctype, :ts, :ts, 'seed') RETURNING caseno"), {"cid": f"C-{random.randint(1000,9999)}", "ctype": random.choice(["company", "person"]), "ts": now}).scalar()
        # processes per case
        for _ in range(random.randint(1, 2)):
            pdno = random.choice(pd_ids)
            status_no = random.choice(status_ids)
            proc_no = conn.execute(text("INSERT INTO processes (processno, case_no, status_no, process_type_no, date_started, date_ended, tmstamp, usrid) SELECT (SELECT COALESCE(MAX(processno),0)+1 FROM processes), :case, :status, pd.process_type_no, :ts, NULL, :ts, 'seed' FROM process_definitions pd WHERE pd.process_definition_no=:pd RETURNING processno"), {"case": case_no, "status": status_no, "pd": pdno, "ts": now}).scalar()
            # steps: follow chain from start task using task_rules
            start_task = conn.execute(text("SELECT start_task_no FROM process_definitions WHERE process_definition_no=:pd"), {"pd": pdno}).scalar()
            current = start_task
            for six in range(random.randint(1, 4)):
                st_status = random.choice(status_ids)
                step_no = conn.execute(text("INSERT INTO steps (stepno, processno, taskno, status_no, date_started, date_ended, tmstamp, usrid) VALUES ((SELECT COALESCE(MAX(stepno),0)+1 FROM steps), :p, :t, :s, :ts, NULL, :ts, 'seed') RETURNING stepno"), {"p": proc_no, "t": current, "s": st_status, "ts": now}).scalar()
                # next via rule if exists
                nx = conn.execute(text("SELECT next_task_no FROM task_rules WHERE taskno=:t AND next_task_no IS NOT NULL ORDER BY taskruleno LIMIT 1"), {"t": current}).scalar()
                if not nx:
                    break
                current = nx

            # attach some process data rows
            for _ in range(random.randint(1, 3)):
                dtype = random.choice(pdtype_ids)
                fname = random.choice(["amount", "date", "reason", "supplier", "invoice_no", "case_id"]) 
                val = random.choice([
                    f"{random.randint(100, 9999)}",
                    now.date().isoformat(),
                    random.choice(["approved", "pending", "escalated", "rejected"]),
                    random.choice(["Acme", "Globex", "Initech", "Umbrella"]),
                    f"INV-{random.randint(10000,99999)}",
                    f"C-{random.randint(1000,9999)}",
                ])
                conn.execute(text("INSERT INTO process_data (process_data_no, processno, process_data_type_no, fieldname, value, tmstamp, usrid) VALUES ((SELECT COALESCE(MAX(process_data_no),0)+1 FROM process_data), :p, :dt, :fn, :val, :ts, 'seed')"), {"p": proc_no, "dt": dtype, "fn": fname, "val": val, "ts": now})

print("Seeded demo data for Procurement and Dispute.")
