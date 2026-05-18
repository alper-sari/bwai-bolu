"""
deploy/agent_engine.py
Deploys the agent to Vertex AI Agent Engine.

Usage:
    python deploy/agent_engine.py --project YOUR_PROJECT_ID
"""

import argparse
import vertexai
from vertexai.preview import reasoning_engines

# Import your agent
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from agent.agent import root_agent


def deploy(project_id: str, location: str = "us-central1"):
    print(f"▶ Initializing Vertex AI — project: {project_id}, location: {location}")
    vertexai.init(project=project_id, location=location)

    print("▶ Wrapping agent with AdkApp...")
    app = reasoning_engines.AdkApp(
        agent=root_agent,
        enable_tracing=True,
    )

    print("▶ Deploying to Agent Engine (this takes ~2-3 minutes)...")
    remote_agent = reasoning_engines.ReasoningEngine.create(
        app,
        requirements=["google-adk>=1.0.0", "mcp>=1.0.0", "fastmcp>=2.0.0"],
        display_name="give-your-agent-hands",
        description="Workshop agent: creates GCP VMs with nginx via MCP tools",
    )

    print("\n✅ Deployed successfully!")
    print(f"Resource name: {remote_agent.resource_name}")

    # Quick test
    print("\n▶ Running a quick test query...")
    session = remote_agent.create_session(user_id="workshop-test")
    response = remote_agent.stream_query(
        user_id="workshop-test",
        session_id=session["id"],
        message="Hello! What can you do?",
    )
    for chunk in response:
        print(chunk, end="", flush=True)
    print()

    return remote_agent.resource_name


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, help="GCP project ID")
    parser.add_argument("--location", default="us-central1", help="GCP region")
    args = parser.parse_args()

    deploy(args.project, args.location)
