from fastapi import FastAPI
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
app.include_router(statuses.router)


