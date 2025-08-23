from mcp.server.fastmcp import FastMCP
from typing import List, Optional
import httpx
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)

# Global variable to store the access token
access_token: Optional[str] = None

# Create MCP server
mcp = FastMCP("WorkflowAssistant")

# Tool: Login to the workflow engine
@mcp.tool()
def login(username: str, password: str) -> str:
    """Logs into the workflow engine to get an access token."""
    global access_token
    try:
        data = {"username": username, "password": password}
        response = httpx.post("http://localhost:8000/auth/token", data=data)
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data.get("access_token")
        if access_token:
            logging.info("Login successful, access token stored.")
            return "Login successful."
        else:
            logging.error("Access token not found in response.")
            return "Login failed: Access token not found in response."
    except httpx.HTTPStatusError as e:
        logging.error(f"Login failed: {e.response.status_code} - {e.response.text}")
        return f"Login failed: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        logging.error(f"Error connecting to workflow engine for login: {e}")
        return f"Error connecting to workflow engine for login: {e}"

# Tool: Get cases from workflow engine
@mcp.tool()
def get_cases() -> str:
    """Get all cases from the workflow engine. Requires login first."""
    global access_token
    if not access_token:
        return "Please login first using the login tool."
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = httpx.get("http://localhost:8000/cases", headers=headers)
        response.raise_for_status()
        cases = response.json()
        
        # Format the response for better readability
        formatted_cases = []
        for case in cases:
            formatted_cases.append(
                f"  Case Number: {case.get('caseno')}\n"
                f"  Client ID: {case.get('client_id')}\n"
                f"  Client Type: {case.get('client_type')}\n"
                f"  Created By: {case.get('usrid')}\n"
                f"  Created At: {case.get('created_at')}"
            )
        
        if not formatted_cases:
            return "No cases found."
            
        return "Found the following cases:\n" + "\n---------------------\n".join(formatted_cases)

    except httpx.HTTPStatusError as e:
        logging.error(f"Error getting cases: {e.response.status_code} - {e.response.text}")
        return f"Error getting cases: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        logging.error(f"Error connecting to workflow engine: {e}")
        return f"Error connecting to workflow engine: {e}"
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON from response.")
        return "Error: Invalid JSON response from the server."


if __name__ == "__main__":
    mcp.run()
