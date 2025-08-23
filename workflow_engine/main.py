from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from workflow.routers import (
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

# Serve static frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
def root():
    return FileResponse("static/index.html")

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


