from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic
import httpx
import json
import logging
import os
from dotenv import load_dotenv
from typing import List, Optional

# Load env
dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'workflow_engine', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Base URL for workflow engine (override via env WORKFLOW_ENGINE_BASE_URL)
WORKFLOW_ENGINE_BASE_URL = os.getenv("WORKFLOW_ENGINE_BASE_URL", "http://localhost:8000")

logging.basicConfig(level=logging.INFO)

# FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth cache
authorization_token: Optional[str] = None

# Models
class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = None

# Anthropic client
try:
    anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
except Exception as e:  # pragma: no cover
    logging.error(f"Anthropic init failed: {e}")
    anthropic_client = None

# Initial login
def initial_login():
    global authorization_token
    u = os.getenv("WORKFLOW_ENGINE_USERNAME")
    p = os.getenv("WORKFLOW_ENGINE_PASSWORD")
    if not u or not p:
        logging.warning("Workflow creds missing")
        return
    try:
        with httpx.Client() as c:
            r = c.post(f"{WORKFLOW_ENGINE_BASE_URL}/auth/token", data={"username": u, "password": p})
            r.raise_for_status()
            authorization_token = r.json().get("access_token")
            logging.info("Workflow login ok" if authorization_token else "Workflow login missing token")
    except Exception as e:
        logging.error(f"Workflow login failed: {e}")

# Business helper
def get_cases() -> str:
    global authorization_token
    if not authorization_token:
        return "Not logged in to workflow engine."
    try:
        with httpx.Client() as c:
            r = c.get(f"{WORKFLOW_ENGINE_BASE_URL}/cases", headers={"Authorization": f"Bearer {authorization_token}"})
            r.raise_for_status()
            cases = r.json()
        if not cases:
            return "No cases found."
        # Improve readability: sort by created_at desc if present
        try:
            cases_sorted = sorted(
                cases,
                key=lambda x: x.get('created_at') or '',
                reverse=True
            )
        except Exception:
            cases_sorted = cases

        DISPLAY_LIMIT = 50
        truncated = len(cases_sorted) > DISPLAY_LIMIT
        display_cases = cases_sorted[:DISPLAY_LIMIT]

        # Determine column widths (with caps)
        def strv(item, key):
            v = item.get(key)
            return '' if v is None else str(v)
        case_w = min(max((len(strv(c, 'caseno')) for c in display_cases), default=4), 12)
        client_w = min(max((len(strv(c, 'client_id')) for c in display_cases), default=6), 16)
        ctype_w = min(max((len(strv(c, 'client_type')) for c in display_cases), default=5), 12)
        user_w = min(max((len(strv(c, 'usrid')) for c in display_cases), default=4), 12)

        header_summary = f"Cases Summary: {len(cases)} total (showing {len(display_cases)} newest)"
        lines = [header_summary]
        for c in display_cases:
            lines.append(
                f"- Case {strv(c,'caseno')}: Client {strv(c,'client_id')} ({strv(c,'client_type')}) "
                f"User {strv(c,'usrid')} Created {strv(c,'created_at')}"
            )
            lines.append("")  # blank line after each case
        if truncated:
            lines.append(f"... truncated {len(cases_sorted)-DISPLAY_LIMIT} older cases ...")
        return "\n".join(lines)
    except httpx.HTTPStatusError as e:
        return f"Workflow error {e.response.status_code}: {e.response.text}"
    except json.JSONDecodeError:
        return "Invalid JSON from workflow engine"
    except Exception as e:
        return f"Error retrieving cases: {e}"

def get_process_data_for_user() -> str:
    """Fetch process data associated with the current user's cases.

    Leverages /process-data which returns either all (admin) or user-specific data.
    """
    global authorization_token
    if not authorization_token:
        return "Not logged in to workflow engine."
    try:
        with httpx.Client() as c:
            r = c.get(f"{WORKFLOW_ENGINE_BASE_URL}/process-data", headers={"Authorization": f"Bearer {authorization_token}"})
            r.raise_for_status()
            pdata = r.json()
        if not pdata:
            return "No process data found."
        # Sort global list by processno then fieldname for stable grouping
        try:
            pdata_sorted = sorted(pdata, key=lambda x: (x.get('processno'), x.get('fieldname'), x.get('process_data_no')))
        except Exception:
            pdata_sorted = pdata

        DISPLAY_LIMIT = 250  # overall entries to display across all processes
        truncated = len(pdata_sorted) > DISPLAY_LIMIT
        display_items = pdata_sorted[:DISPLAY_LIMIT]

        # Group by process
        grouped: dict[int, list[dict]] = {}
        for item in display_items:
            pno = item.get('processno')
            grouped.setdefault(pno, []).append(item)

        # Simple grouped bullet list formatting
        def sval(it, key):
            v = it.get(key)
            return '' if v is None else str(v)

        total_processes = len({i.get('processno') for i in pdata})
        header = (
            f"Process Data Summary: {len(pdata)} total entries across {total_processes} processes "
            f"(showing {len(display_items)})"
        )
        lines = [header]
        for pno, items in grouped.items():
            lines.append(f"\nProcess {pno} ({len(items)} entries):")
            for it in items:
                lines.append(
                    "  - "
                    f"data#{sval(it,'process_data_no')} type {sval(it,'process_data_type_no')} "
                    f"{sval(it,'fieldname')} = {sval(it,'value')}"
                )
                lines.append("")  # blank line after each process data entry
        if truncated:
            lines.append(f"\n... truncated {len(pdata_sorted)-DISPLAY_LIMIT} additional entries ...")
        return "\n".join(lines)
    except httpx.HTTPStatusError as e:
        return f"Workflow error {e.response.status_code}: {e.response.text}"
    except json.JSONDecodeError:
        return "Invalid JSON from workflow engine"
    except Exception as e:
        return f"Error retrieving process data: {e}"

def get_process_data_for_case(case_no: int) -> str:
    """Fetch process data for a specific case number via /cases/{case_no}/process-data."""
    global authorization_token
    if not authorization_token:
        return "Not logged in to workflow engine."
    try:
        with httpx.Client() as c:
            r = c.get(f"{WORKFLOW_ENGINE_BASE_URL}/cases/{case_no}/process-data", headers={"Authorization": f"Bearer {authorization_token}"})
            if r.status_code == 404:
                return f"Case {case_no} not found or no data."
            r.raise_for_status()
            pdata = r.json()
        if not pdata:
            return f"No process data found for case {case_no}."
        lines = []
        for item in pdata[:100]:
            lines.append(
                f"Case {case_no} Proc {item.get('processno')} Data#{item.get('process_data_no')} "
                f"{item.get('fieldname')}={item.get('value')} (Type {item.get('process_data_type_no')})"
            )
            lines.append("")  # blank line after each entry
        if len(pdata) > 100:
            lines.append(f"... truncated {len(pdata)-100} more entries ...")
        return "\n".join(lines)
    except httpx.HTTPStatusError as e:
        return f"Workflow error {e.response.status_code}: {e.response.text}"
    except json.JSONDecodeError:
        return "Invalid JSON from workflow engine"
    except Exception as e:
        return f"Error retrieving case process data: {e}"

def list_process_data_for_case(case_no: int) -> str:
    """Alias for get_process_data_for_case to mirror workflow_engine router naming."""
    return get_process_data_for_case(case_no)

# ---- Steps helper functions ----
def list_steps() -> str:
    """List all steps (admin only)."""
    global authorization_token
    if not authorization_token:
        return "Not logged in to workflow engine."
    try:
        with httpx.Client() as c:
            r = c.get(f"{WORKFLOW_ENGINE_BASE_URL}/steps", headers={"Authorization": f"Bearer {authorization_token}"})
            if r.status_code == 403:
                return "Not authorized to list all steps (admin only)."
            r.raise_for_status()
            steps = r.json()
        if not steps:
            return "No steps found."
        lines = [f"Steps Summary: {len(steps)} total (showing up to 100)"]
        for s in steps[:100]:
            lines.append(
                f"- Step {s.get('stepno')} Proc {s.get('processno')} Task {s.get('taskno')} "
                f"Status {s.get('status_no')} Started {s.get('date_started')} Ended {s.get('date_ended')}"
            )
            lines.append("")
        if len(steps) > 100:
            lines.append(f"... truncated {len(steps)-100} older steps ...")
        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving steps: {e}"

def get_current_step_for_case_tool(case_no: int) -> str:
    """Fetch current (busy) step for a case."""
    global authorization_token
    if not authorization_token:
        return "Not logged in to workflow engine."
    try:
        with httpx.Client() as c:
            r = c.get(f"{WORKFLOW_ENGINE_BASE_URL}/cases/{case_no}/current-step", headers={"Authorization": f"Bearer {authorization_token}"})
            if r.status_code == 404:
                return f"No current step for case {case_no}."
            r.raise_for_status()
            s = r.json()
        return (
            f"Current Step for Case {case_no}: Step {s.get('stepno')} Proc {s.get('processno')} "
            f"Task {s.get('taskno')} Status {s.get('status_no')} Started {s.get('date_started')}"
        )
    except Exception as e:
        return f"Error retrieving current step: {e}"

def list_steps_for_case(case_no: int) -> str:
    global authorization_token
    if not authorization_token:
        return "Not logged in to workflow engine."
    try:
        with httpx.Client() as c:
            r = c.get(f"{WORKFLOW_ENGINE_BASE_URL}/cases/{case_no}/steps", headers={"Authorization": f"Bearer {authorization_token}"})
            if r.status_code == 404:
                return f"No steps for case {case_no}."
            r.raise_for_status()
            steps = r.json()
        if not steps:
            return f"No steps for case {case_no}."
        lines = [f"Steps for Case {case_no}: {len(steps)} total (showing up to 100)"]
        for s in steps[:100]:
            lines.append(
                f"- Step {s.get('stepno')} Task {s.get('taskno')} Status {s.get('status_no')} "
                f"Started {s.get('date_started')} Ended {s.get('date_ended')}"
            )
            lines.append("")
        if len(steps) > 100:
            lines.append(f"... truncated {len(steps)-100} older steps ...")
        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving steps for case {case_no}: {e}"

def close_step(step_id: int, rule_data: dict | None = None) -> str:
    global authorization_token
    if not authorization_token:
        return "Not logged in to workflow engine."
    try:
        payload = {"rule_data": rule_data or {}}
        with httpx.Client() as c:
            r = c.post(
                f"{WORKFLOW_ENGINE_BASE_URL}/steps/{step_id}/close",
                headers={"Authorization": f"Bearer {authorization_token}"},
                json=payload,
            )
            if r.status_code == 404:
                return f"Step {step_id} not found."
            if r.status_code == 403:
                return f"Not authorized to close step {step_id}."
            r.raise_for_status()
            s = r.json()
        return (
            f"Closed Step {s.get('stepno')} Proc {s.get('processno')} Task {s.get('taskno')} "
            f"Status {s.get('status_no')} Ended {s.get('date_ended')}"
        )
    except Exception as e:
        return f"Error closing step {step_id}: {e}"

# ---- Statuses helper functions ----
def list_statuses() -> str:
    global authorization_token
    if not authorization_token:
        return "Not logged in to workflow engine."
    try:
        with httpx.Client() as c:
            r = c.get(f"{WORKFLOW_ENGINE_BASE_URL}/statuses", headers={"Authorization": f"Bearer {authorization_token}"})
            if r.status_code == 403:
                return "Not authorized to list statuses."
            r.raise_for_status()
            statuses = r.json()
        if not statuses:
            return "No statuses found."
        lines = [f"Statuses ({len(statuses)} total):"]
        for st in statuses[:100]:
            lines.append(f"- {st.get('statusno')} : {st.get('description')}")
        if len(statuses) > 100:
            lines.append(f"... truncated {len(statuses)-100} more ...")
        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving statuses: {e}"

def get_status_tool(statusno: int) -> str:
    global authorization_token
    if not authorization_token:
        return "Not logged in to workflow engine."
    try:
        with httpx.Client() as c:
            r = c.get(f"{WORKFLOW_ENGINE_BASE_URL}/statuses/{statusno}", headers={"Authorization": f"Bearer {authorization_token}"})
            if r.status_code == 404:
                return f"Status {statusno} not found."
            r.raise_for_status()
            st = r.json()
        return f"Status {st.get('statusno')}: {st.get('description')}"
    except Exception as e:
        return f"Error retrieving status {statusno}: {e}"



# ---- Task Rules helper functions (admin endpoints) ----
def list_task_rules() -> str:
    global authorization_token
    if not authorization_token:
        return "Not logged in to workflow engine."
    try:
        with httpx.Client() as c:
            r = c.get(f"{WORKFLOW_ENGINE_BASE_URL}/task-rules", headers={"Authorization": f"Bearer {authorization_token}"})
            if r.status_code == 403:
                return "Not authorized to list task rules (admin only)."
            r.raise_for_status()
            rules = r.json()
        if not rules:
            return "No task rules found."
        lines = [f"Task Rules ({len(rules)} total, showing up to 100):"]
        for tr in rules[:100]:
            lines.append(
                f"- Rule {tr.get('taskruleno')} Task {tr.get('taskno')} -> Next {tr.get('next_task_no')} : {tr.get('rule')}"
            )
        if len(rules) > 100:
            lines.append(f"... truncated {len(rules)-100} more ...")
        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving task rules: {e}"

def get_task_rule_tool(taskruleno: int) -> str:
    global authorization_token
    if not authorization_token:
        return "Not logged in to workflow engine."
    try:
        with httpx.Client() as c:
            r = c.get(f"{WORKFLOW_ENGINE_BASE_URL}/task-rules/{taskruleno}", headers={"Authorization": f"Bearer {authorization_token}"})
            if r.status_code == 404:
                return f"Task rule {taskruleno} not found."
            if r.status_code == 403:
                return "Not authorized to get task rule (admin only)."
            r.raise_for_status()
            tr = r.json()
        return (
            f"Task Rule {tr.get('taskruleno')}: Task {tr.get('taskno')} Rule '{tr.get('rule')}' Next {tr.get('next_task_no')}"
        )
    except Exception as e:
        return f"Error retrieving task rule {taskruleno}: {e}"



# ---- Tasks helper functions (admin endpoints) ----
def list_tasks() -> str:
    global authorization_token
    if not authorization_token:
        return "Not logged in to workflow engine."
    try:
        with httpx.Client() as c:
            r = c.get(f"{WORKFLOW_ENGINE_BASE_URL}/tasks", headers={"Authorization": f"Bearer {authorization_token}"})
            if r.status_code == 403:
                return "Not authorized to list tasks (admin only)."
            r.raise_for_status()
            tasks = r.json()
        if not tasks:
            return "No tasks found."
        lines = [f"Tasks ({len(tasks)} total, showing up to 100):"]
        for t in tasks[:100]:
            lines.append(
                f"- Task {t.get('taskno')} Def {t.get('process_definition_no')} Desc '{t.get('description')}' Ref {t.get('reference')}"
            )
        if len(tasks) > 100:
            lines.append(f"... truncated {len(tasks)-100} more ...")
        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving tasks: {e}"

def get_task_tool(taskno: int) -> str:
    global authorization_token
    if not authorization_token:
        return "Not logged in to workflow engine."
    try:
        with httpx.Client() as c:
            r = c.get(f"{WORKFLOW_ENGINE_BASE_URL}/tasks/{taskno}", headers={"Authorization": f"Bearer {authorization_token}"})
            if r.status_code == 404:
                return f"Task {taskno} not found."
            if r.status_code == 403:
                return "Not authorized to get task (admin only)."
            r.raise_for_status()
            t = r.json()
        return (
            f"Task {t.get('taskno')} Def {t.get('process_definition_no')} Desc '{t.get('description')}' Ref {t.get('reference')}"
        )
    except Exception as e:
        return f"Error retrieving task {taskno}: {e}"



# ---- Processes helper functions (admin + user create data) ----
def list_processes() -> str:
    global authorization_token
    if not authorization_token:
        return "Not logged in to workflow engine."
    try:
        with httpx.Client() as c:
            r = c.get(f"{WORKFLOW_ENGINE_BASE_URL}/processes", headers={"Authorization": f"Bearer {authorization_token}"})
            if r.status_code == 403:
                return "Not authorized to list processes (admin only)."
            r.raise_for_status()
            processes = r.json()
        if not processes:
            return "No processes found."
        lines = [f"Processes ({len(processes)} total, showing up to 100):"]
        for p in processes[:100]:
            lines.append(
                f"- Proc {p.get('processno')} Case {p.get('case_no')} Status {p.get('status_no')} Type {p.get('process_type_no')} Started {p.get('date_started')} Ended {p.get('date_ended')}"
            )
        if len(processes) > 100:
            lines.append(f"... truncated {len(processes)-100} more ...")
        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving processes: {e}"


# ---- Process Types helper functions ----
def list_process_types() -> str:
    global authorization_token
    if not authorization_token:
        return "Not logged in to workflow engine."
    try:
        with httpx.Client() as c:
            r = c.get(f"{WORKFLOW_ENGINE_BASE_URL}/process-types", headers={"Authorization": f"Bearer {authorization_token}"})
            if r.status_code == 403:
                return "Not authorized to list process types."
            r.raise_for_status()
            types_ = r.json()
        if not types_:
            return "No process types found."
        lines = [f"Process Types ({len(types_)} total, showing up to 100):"]
        for pt in types_[:100]:
            lines.append(f"- Type {pt.get('process_type_no')}: {pt.get('description')}")
        if len(types_) > 100:
            lines.append(f"... truncated {len(types_)-100} more ...")
        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving process types: {e}"

def get_process_type_tool(process_type_no: int) -> str:
    global authorization_token
    if not authorization_token:
        return "Not logged in to workflow engine."
    try:
        with httpx.Client() as c:
            r = c.get(
                f"{WORKFLOW_ENGINE_BASE_URL}/process-types/{process_type_no}",
                headers={"Authorization": f"Bearer {authorization_token}"},
            )
            if r.status_code == 404:
                return f"Process type {process_type_no} not found."
            if r.status_code == 403:
                return "Not authorized to get process type."
            r.raise_for_status()
            pt = r.json()
        return f"Process Type {pt.get('process_type_no')}: {pt.get('description')}"
    except Exception as e:
        return f"Error retrieving process type {process_type_no}: {e}"


# ---- Process Definitions helper functions (admin only) ----
def list_process_definitions() -> str:
    global authorization_token
    if not authorization_token:
        return "Not logged in to workflow engine."
    try:
        with httpx.Client() as c:
            r = c.get(f"{WORKFLOW_ENGINE_BASE_URL}/process-definitions", headers={"Authorization": f"Bearer {authorization_token}"})
            if r.status_code == 403:
                return "Not authorized to list process definitions (admin only)."
            r.raise_for_status()
            defs = r.json()
        if not defs:
            return "No process definitions found."
        lines = [f"Process Definitions ({len(defs)} total, showing up to 100):"]
        for d in defs[:100]:
            lines.append(
                f"- Def {d.get('process_definition_no')} Type {d.get('process_type_no')} StartTask {d.get('start_task_no')} Version {d.get('version')} Active {d.get('is_active')}"
            )
        if len(defs) > 100:
            lines.append(f"... truncated {len(defs)-100} more ...")
        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving process definitions: {e}"

def get_process_definition_tool(process_definition_no: int) -> str:
    global authorization_token
    if not authorization_token:
        return "Not logged in to workflow engine."
    try:
        with httpx.Client() as c:
            r = c.get(
                f"{WORKFLOW_ENGINE_BASE_URL}/process-definitions/{process_definition_no}",
                headers={"Authorization": f"Bearer {authorization_token}"},
            )
            if r.status_code == 404:
                return f"Process definition {process_definition_no} not found."
            if r.status_code == 403:
                return "Not authorized to get process definition."
            r.raise_for_status()
            d = r.json()
        return (
            f"Process Definition {d.get('process_definition_no')} Type {d.get('process_type_no')} StartTask {d.get('start_task_no')} Version {d.get('version')} Active {d.get('is_active')}"
        )
    except Exception as e:
        return f"Error retrieving process definition {process_definition_no}: {e}"



# ---- Process Data Types helper functions ----
def list_process_data_types() -> str:
    global authorization_token
    if not authorization_token:
        return "Not logged in to workflow engine."
    try:
        with httpx.Client() as c:
            r = c.get(f"{WORKFLOW_ENGINE_BASE_URL}/process-data-types", headers={"Authorization": f"Bearer {authorization_token}"})
            if r.status_code == 403:
                return "Not authorized to list process data types."
            r.raise_for_status()
            types_ = r.json()
        if not types_:
            return "No process data types found."
        lines = [f"Process Data Types ({len(types_)} total, showing up to 100):"]
        for t in types_[:100]:
            lines.append(f"- PDT {t.get('process_data_type_no')}: {t.get('description')}")
        if len(types_) > 100:
            lines.append(f"... truncated {len(types_)-100} more ...")
        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving process data types: {e}"

def get_process_data_type_tool(process_data_type_no: int) -> str:
    global authorization_token
    if not authorization_token:
        return "Not logged in to workflow engine."
    try:
        with httpx.Client() as c:
            r = c.get(
                f"{WORKFLOW_ENGINE_BASE_URL}/process-data-types/{process_data_type_no}",
                headers={"Authorization": f"Bearer {authorization_token}"},
            )
            if r.status_code == 404:
                return f"Process data type {process_data_type_no} not found."
            if r.status_code == 403:
                return "Not authorized to get process data type."
            r.raise_for_status()
            t = r.json()
        return f"Process Data Type {t.get('process_data_type_no')}: {t.get('description')}"
    except Exception as e:
        return f"Error retrieving process data type {process_data_type_no}: {e}"



# Tool spec (manual)
ANTHROPIC_TOOLS = [
    {
        "name": "get_cases",
        "description": "Return a formatted list of workflow cases (no input params).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_process_data_for_user",
        "description": "Return process data entries (fieldname/value) for processes belonging to the user's cases.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_process_data_for_case",
        "description": "Return process data entries for the specified case number (case_no).",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_no": {"type": "integer", "description": "Case number to retrieve process data for"}
            },
            "required": ["case_no"],
        },
    },
    {
        "name": "list_process_data_for_case",
        "description": "Alias of get_process_data_for_case; returns process data entries for a single case.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_no": {"type": "integer", "description": "Case number to retrieve process data for"}
            },
            "required": ["case_no"],
        },
    },
    {
        "name": "list_steps",
        "description": "List all steps (admin only).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_current_step_for_case",
        "description": "Get the current active (busy) step for a case.",
        "input_schema": {
            "type": "object",
            "properties": {"case_no": {"type": "integer"}},
            "required": ["case_no"],
        },
    },
    {
        "name": "list_steps_for_case",
        "description": "List all steps for a given case.",
        "input_schema": {
            "type": "object",
            "properties": {"case_no": {"type": "integer"}},
            "required": ["case_no"],
        },
    },
    {
        "name": "close_step",
        "description": "Close a step by step_id providing optional rule_data (dict).",
        "input_schema": {
            "type": "object",
            "properties": {
                "step_id": {"type": "integer"},
                "rule_data": {"type": "object", "description": "Rule data map (key/value)"}
            },
            "required": ["step_id"],
        },
    },
    {
        "name": "list_statuses",
        "description": "List all statuses (user or admin).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_status",
        "description": "Get a status by status number (statusno).",
        "input_schema": {
            "type": "object",
            "properties": {"statusno": {"type": "integer"}},
            "required": ["statusno"],
        },
    },
    {
        "name": "list_task_rules",
        "description": "List task rules (admin only).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_task_rule",
        "description": "Get a task rule by its taskruleno (admin only).",
        "input_schema": {
            "type": "object",
            "properties": {"taskruleno": {"type": "integer"}},
            "required": ["taskruleno"],
        },
    },
    {
        "name": "list_tasks",
        "description": "List tasks (admin only).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_task",
        "description": "Get a task by task number (admin only).",
        "input_schema": {
            "type": "object",
            "properties": {"taskno": {"type": "integer"}},
            "required": ["taskno"],
        },
    },
    {
        "name": "list_processes",
        "description": "List processes (admin only).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_process_types",
        "description": "List process types (user or admin).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_process_type",
        "description": "Get a process type by its number (user or admin).",
        "input_schema": {
            "type": "object",
            "properties": {"process_type_no": {"type": "integer"}},
            "required": ["process_type_no"],
        },
    },
    {
        "name": "list_process_definitions",
        "description": "List process definitions (admin only).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_process_definition",
        "description": "Get a process definition by its number (admin only).",
        "input_schema": {
            "type": "object",
            "properties": {"process_definition_no": {"type": "integer"}},
            "required": ["process_definition_no"],
        },
    },
    {
        "name": "list_process_data_types",
        "description": "List process data types (user or admin).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_process_data_type",
        "description": "Get a process data type by its number (user or admin).",
        "input_schema": {
            "type": "object",
            "properties": {"process_data_type_no": {"type": "integer"}},
            "required": ["process_data_type_no"],
        },
    },
]

SYSTEM_PROMPT = (
    "You are the Workflow Agent. You have access to tools that retrieve workflow data. "
    "Reason step-by-step about what information is missing. If the user request requires data, "
    "call the minimal set of tools needed (you may call tools in multiple rounds). After each tool result, "
    "decide if another tool call is necessary. When you have enough information, provide a concise answer. "
    "Never guess values that can be fetched. If parameters are missing, ask the user for them instead of fabricating."
)

MAX_TOOL_ITERATIONS = 8  # safeguard

# Chat endpoint with iterative tool reasoning
@app.post("/chat")
async def chat(req: ChatRequest):
    if not anthropic_client:
        return {"error": "Anthropic client not configured"}

    # Start conversation context
    messages: List[dict] = []
    if req.history:
        messages.extend(req.history)
    messages.append({"role": "user", "content": req.message})

    iteration = 0
    final_text_segments: List[str] = []
    try:
        while iteration < MAX_TOOL_ITERATIONS:
            iteration += 1
            resp = anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=800,
                messages=messages,
                tools=ANTHROPIC_TOOLS,
                system=SYSTEM_PROMPT,
            )

            tool_uses = [c for c in resp.content if getattr(c, "type", None) == "tool_use"]

            # Collect any textual content from this assistant turn (reasoning or partial answer)
            text_chunks = [c.text for c in resp.content if hasattr(c, "text") and getattr(c, "text", None)]
            if text_chunks:
                final_text_segments.append("\n".join(t.strip() for t in text_chunks if t))

            if not tool_uses:
                # Pure answer; record and stop
                messages.append({
                    "role": "assistant",
                    "content": [c.model_dump() if hasattr(c, "model_dump") else {"type": "text", "text": getattr(c, 'text', '')} for c in resp.content],
                })
                break

            # Execute tools
            tool_result_blocks = []
            for tu in tool_uses:
                if tu.name == "get_cases":
                    result = get_cases()
                elif tu.name == "get_process_data_for_user":
                    result = get_process_data_for_user()
                elif tu.name in ("get_process_data_for_case", "list_process_data_for_case"):
                    case_no = None
                    try:
                        case_no = int(getattr(tu, "input", {}) or {}.get("case_no") or tu.input.get("case_no"))  # type: ignore
                    except Exception:
                        inp = getattr(tu, "input", {})
                        case_no = inp.get("case_no") if isinstance(inp, dict) else None
                    if case_no is None:
                        result = "Missing required parameter case_no."
                    else:
                        result = get_process_data_for_case(case_no)
                elif tu.name == "list_steps":
                    result = list_steps()
                elif tu.name == "get_current_step_for_case":
                    case_no = None
                    try:
                        case_no = int(getattr(tu, "input", {}) or {}.get("case_no") or tu.input.get("case_no"))  # type: ignore
                    except Exception:
                        inp = getattr(tu, "input", {})
                        case_no = inp.get("case_no") if isinstance(inp, dict) else None
                    result = "Missing required parameter case_no." if case_no is None else get_current_step_for_case_tool(case_no)
                elif tu.name == "list_steps_for_case":
                    case_no = None
                    try:
                        case_no = int(getattr(tu, "input", {}) or {}.get("case_no") or tu.input.get("case_no"))  # type: ignore
                    except Exception:
                        inp = getattr(tu, "input", {})
                        case_no = inp.get("case_no") if isinstance(inp, dict) else None
                    result = "Missing required parameter case_no." if case_no is None else list_steps_for_case(case_no)
                elif tu.name == "close_step":
                    step_id = None
                    rule_data = {}
                    try:
                        inp = getattr(tu, "input", {}) or {}
                        step_id = inp.get("step_id") if isinstance(inp, dict) else None
                        if step_id is not None:
                            step_id = int(step_id)
                        if isinstance(inp, dict):
                            rule_data = inp.get("rule_data") or {}
                    except Exception:
                        pass
                    result = "Missing required parameter step_id." if step_id is None else close_step(step_id, rule_data if isinstance(rule_data, dict) else {})
                elif tu.name == "list_statuses":
                    result = list_statuses()
                elif tu.name == "get_status":
                    statusno = None
                    try:
                        statusno = int(getattr(tu, "input", {}) or {}.get("statusno") or tu.input.get("statusno"))  # type: ignore
                    except Exception:
                        inp = getattr(tu, "input", {})
                        statusno = inp.get("statusno") if isinstance(inp, dict) else None
                    result = "Missing required parameter statusno." if statusno is None else get_status_tool(statusno)
                elif tu.name == "list_task_rules":
                    result = list_task_rules()
                elif tu.name == "get_task_rule":
                    taskruleno = None
                    try:
                        taskruleno = int(getattr(tu, "input", {}) or {}.get("taskruleno") or tu.input.get("taskruleno"))  # type: ignore
                    except Exception:
                        inp = getattr(tu, "input", {})
                        taskruleno = inp.get("taskruleno") if isinstance(inp, dict) else None
                    result = "Missing required parameter taskruleno." if taskruleno is None else get_task_rule_tool(taskruleno)
                elif tu.name == "list_tasks":
                    result = list_tasks()
                elif tu.name == "get_task":
                    taskno = None
                    try:
                        taskno = int(getattr(tu, "input", {}) or {}.get("taskno") or tu.input.get("taskno"))  # type: ignore
                    except Exception:
                        inp = getattr(tu, "input", {})
                        taskno = inp.get("taskno") if isinstance(inp, dict) else None
                    result = "Missing required parameter taskno." if taskno is None else get_task_tool(taskno)
                elif tu.name == "list_processes":
                    result = list_processes()
                elif tu.name == "list_process_types":
                    result = list_process_types()
                elif tu.name == "get_process_type":
                    ptype_no = None
                    try:
                        ptype_no = int(getattr(tu, "input", {}) or {}.get("process_type_no") or tu.input.get("process_type_no"))  # type: ignore
                    except Exception:
                        inp = getattr(tu, "input", {})
                        ptype_no = inp.get("process_type_no") if isinstance(inp, dict) else None
                    result = "Missing required parameter process_type_no." if ptype_no is None else get_process_type_tool(ptype_no)
                elif tu.name == "list_process_definitions":
                    result = list_process_definitions()
                elif tu.name == "get_process_definition":
                    pdef_no = None
                    try:
                        pdef_no = int(getattr(tu, "input", {}) or {}.get("process_definition_no") or tu.input.get("process_definition_no"))  # type: ignore
                    except Exception:
                        inp = getattr(tu, "input", {})
                        pdef_no = inp.get("process_definition_no") if isinstance(inp, dict) else None
                    result = "Missing required parameter process_definition_no." if pdef_no is None else get_process_definition_tool(pdef_no)
                elif tu.name == "list_process_data_types":
                    result = list_process_data_types()
                elif tu.name == "get_process_data_type":
                    pdt_no = None
                    try:
                        pdt_no = int(getattr(tu, "input", {}) or {}.get("process_data_type_no") or tu.input.get("process_data_type_no"))  # type: ignore
                    except Exception:
                        inp = getattr(tu, "input", {})
                        pdt_no = inp.get("process_data_type_no") if isinstance(inp, dict) else None
                    result = "Missing required parameter process_data_type_no." if pdt_no is None else get_process_data_type_tool(pdt_no)
                else:
                    result = f"Unknown tool {tu.name}"

                tool_result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": result,
                })

            # Append assistant tool_use turn and subsequent user tool results
            messages.append({
                "role": "assistant",
                "content": [c.model_dump() if hasattr(c, "model_dump") else {"type": "text", "text": getattr(c, 'text', '')} for c in resp.content],
            })
            messages.append({
                "role": "user",
                "content": tool_result_blocks,
            })
            # Loop continues for another iteration letting model decide further tool calls

        final_answer = "\n\n".join(seg for seg in final_text_segments if seg).strip()
        return {"response": final_answer, "history": messages, "iterations": iteration}
    except Exception as e:
        logging.exception("Chat failure")
        return {"error": str(e)}

if __name__ == "__main__":
    initial_login()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
