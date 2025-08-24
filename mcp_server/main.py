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
            r = c.post("http://localhost:8000/auth/token", data={"username": u, "password": p})
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
            r = c.get("http://localhost:8000/cases", headers={"Authorization": f"Bearer {authorization_token}"})
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
            r = c.get("http://localhost:8000/process-data", headers={"Authorization": f"Bearer {authorization_token}"})
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
            r = c.get(f"http://localhost:8000/cases/{case_no}/process-data", headers={"Authorization": f"Bearer {authorization_token}"})
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
]

# Chat endpoint
@app.post("/chat")
async def chat(req: ChatRequest):
    if not anthropic_client:
        return {"error": "Anthropic client not configured"}

    # Build messages list for Anthropic
    messages = []
    if req.history:
        # Expect history already in Anthropic shape (role/content)
        messages.extend(req.history)
    messages.append({"role": "user", "content": req.message})

    try:
        # First model call
        resp = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=messages,
            tools=ANTHROPIC_TOOLS,
        )

        # Scan for tool_use blocks (Anthropic may return multiple content blocks)
        tool_uses = [c for c in resp.content if getattr(c, "type", None) == "tool_use"]
        if not tool_uses:
            # Plain answer, append assistant message to history
            assistant_blocks = []
            for c in resp.content:
                if hasattr(c, "text"):
                    assistant_blocks.append({"type": "text", "text": c.text})
                elif getattr(c, "type", None) == "tool_use":
                    # Shouldn't happen here but include defensively
                    assistant_blocks.append(c.model_dump())
            messages.append({"role": "assistant", "content": assistant_blocks})
            final_text = "\n".join([b["text"] for b in assistant_blocks if b.get("type") == "text"]).strip()
            return {"response": final_text, "history": messages}

        # Execute each tool serially
        tool_result_blocks = []
        for tu in tool_uses:
            if tu.name == "get_cases":
                result = get_cases()
            elif tu.name == "get_process_data_for_user":
                result = get_process_data_for_user()
            elif tu.name == "get_process_data_for_case":
                case_no = None
                try:
                    # Anthropic tool_use objects expose an input dict
                    case_no = int(getattr(tu, "input", {}) or {}.get("case_no") or tu.input.get("case_no"))  # type: ignore
                except Exception:
                    # Fallback attempt
                    inp = getattr(tu, "input", {})
                    case_no = inp.get("case_no") if isinstance(inp, dict) else None
                if case_no is None:
                    result = "Missing required parameter case_no."
                else:
                    result = get_process_data_for_case(case_no)
            else:
                result = f"Unknown tool {tu.name}"
            tool_result_blocks.append({
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": result,
            })

        # Append tool_use messages + results to conversation and call again
        # Represent assistant tool_use as assistant role content object list
        messages.append({
            "role": "assistant",
            "content": [cu.model_dump() for cu in resp.content],
        })
        # User message providing tool results
        messages.append({
            "role": "user",
            "content": tool_result_blocks,
        })

        follow = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=messages,
            tools=ANTHROPIC_TOOLS,
        )
        follow_text = "\n".join([c.text for c in follow.content if hasattr(c, "text")]).strip()
        return {"response": follow_text, "history": messages}
    except Exception as e:
        logging.exception("Chat failure")
        return {"error": str(e)}

if __name__ == "__main__":
    initial_login()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
