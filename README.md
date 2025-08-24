Setup Instructions: Run Frontend, MCP Server, and Workflow Engine (No Docker)
============================================================

1. Install dependencies
----------------------

# Backend (Python)
Open a terminal in the repo root and run:

python -m pip install --upgrade pip
pip install -r workflow_engine/requirements.txt
pip install -r mcp_server/requirements.txt

# Frontend (Angular)
Open a terminal in the 'frontend' folder:

cd frontend
npm install

2. Start Workflow Engine API
---------------------------
Open a terminal in 'workflow_engine' folder:

cd workflow_engine
uvicorn main:app --reload

3. Start MCP Server
-------------------
Open a terminal in 'mcp_server' folder:

cd mcp_server
python main.py 

4. Start Frontend (Angular)
---------------------------
Open a terminal in the 'frontend' folder:

cd frontend
npm run start

5. Access the apps
------------------
- Workflow Engine API: http://localhost:8000 (docs at /docs)
- MCP Server: http://localhost:8001 (docs at /docs)
- Frontend: http://localhost:4200

Notes:
------
- Ensure you have Python 3.11+ and Node.js 20+ installed.
- You may need to set environment variables for DB and secrets in workflow_engine/.env and mcp_server/.env.
- Start each service in its own terminal window.
- If you need to change ports, update the uvicorn command accordingly.