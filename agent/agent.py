"""
ADK Agent: GCP Infrastructure Assistant

Lokal geliştirme:
  MCP_SERVER_URL set edilmezse agent stdio ile mcp_server/server.py'yi başlatır.

Deploy:
  MCP_SERVER_URL=https://gcp-mcp-server-xxx.run.app olarak set edilirse
  agent uzaktaki MCP server'a SSE üzerinden bağlanır.
"""

import os
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

_MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "")

_MCP_SERVER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "mcp_server",
    "server.py",
)

if _MCP_SERVER_URL:
    _tools = [
        MCPToolset(
            connection_params=SseConnectionParams(
                url=f"{_MCP_SERVER_URL.rstrip('/')}/sse",
            )
        )
    ]
else:
    _tools = [
        MCPToolset(
            connection_params=StdioServerParameters(
                command="python",
                args=[_MCP_SERVER_PATH],
            )
        )
    ]

_INSTRUCTION = """
You are a GCP infrastructure assistant with full access to Compute Engine tools.

When a user asks you to create a VM:
1. Ask for project_id if not provided.
2. Suggest instance_name if not specified (e.g. 'workshop-vm-1').
3. Use zone 'europe-west1-b' and machine type 'e2-micro' as defaults.
4. After creation, remind the user to check status with get_vm_status.
5. Remind the user nginx takes ~60 seconds via startup-script.

When asked to check a VM: use get_vm_status, report state and URL.
When asked to delete a VM: confirm instance name and project, then delete.

Be concise and confirm every action you take.
"""

root_agent = Agent(
    name="gcp_infra_agent",
    model="gemini-2.5-flash",
    description=(
        "A GCP infrastructure assistant that can create and manage "
        "Compute Engine VMs with nginx installed."
    ),
    instruction=_INSTRUCTION,
    tools=_tools,
)
