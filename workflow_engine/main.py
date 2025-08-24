from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from workflow_engine.workflow.routers import (
    auth,
    cases,
    processes,
    tasks,
    process_definitions,
    process_types,
    process_data_types,
    task_rules,
    steps,
    statuses,
    process_data,
)

app = FastAPI()

# Serve static frontend if present
_static_dir = Path(__file__).resolve().parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

@app.get("/", include_in_schema=False)
def root():
    index_path = _static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse({"status": "ok", "message": "Workflow Engine API"})

# Register routers
app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(processes.router)
app.include_router(tasks.router)
app.include_router(process_definitions.router)
app.include_router(process_types.router)
app.include_router(process_data_types.router)
app.include_router(task_rules.router)
app.include_router(steps.router)
app.include_router(statuses.router)
app.include_router(process_data.router)


