from fastapi import FastAPI
from workflow.routers import (
    cases,
    processes,
    tasks,
    process_definitions,
    process_types,
    process_data_types,
    task_rules,
    steps,
)

app = FastAPI()

# Register routers
app.include_router(cases.router)
app.include_router(processes.router)
app.include_router(tasks.router)
app.include_router(process_definitions.router)
app.include_router(process_types.router)
app.include_router(process_data_types.router)
app.include_router(task_rules.router)
app.include_router(steps.router)
