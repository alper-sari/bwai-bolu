<!--markdownlint-disable MD024 MD033 MD036 MD041 -->
<walkthrough-metadata>
  <meta name="title" content="Give Your Agent Hands: Building Tool-Enabled AI with ADK and MCP" />
  <meta name="description" content="Deploy an MCP server to Cloud Run and connect it to a Google ADK agent that can create and manage GCP virtual machines." />
  <meta name="keywords" content="ADK, MCP, Model Context Protocol, Google Agent Development Kit, Cloud Run, Compute Engine, Gemini" />
</walkthrough-metadata>

# Give Your Agent Hands

## Let's get started

In this lab, you will build a tool-enabled AI agent that can **create, monitor, and delete GCP virtual machines** on your behalf.

The architecture is simple but powerful:

```
You ──▶ ADK Agent (Gemini) ──▶ MCP Server (Cloud Run) ──▶ gcloud ──▶ GCP
```

- **MCP Server**: A lightweight Cloud Run service that exposes `create_vm`, `get_vm_status`, and `delete_vm` as tools.
- **ADK Agent**: A Gemini-powered agent that understands your intent and calls the right tools.

The two services are deployed independently. This means the instructor can deploy the MCP server once and all participants connect their own agents to it.

<walkthrough-tutorial-difficulty difficulty="2"></walkthrough-tutorial-difficulty>

Estimated time:
<walkthrough-tutorial-duration duration="30"></walkthrough-tutorial-duration>

Click **Start** to begin.

## Project Setup

Select the GCP project you want to use for this lab.

<walkthrough-project-setup billing="true"></walkthrough-project-setup>

Enable the APIs we'll need:

<walkthrough-enable-apis apis="run.googleapis.com,cloudbuild.googleapis.com,compute.googleapis.com,containerregistry.googleapis.com"></walkthrough-enable-apis>

## Get a Gemini API Key

The ADK agent uses Gemini 2.5 Flash. You need an API key from Google AI Studio.

1. Go to [aistudio.google.com](https://aistudio.google.com) and sign in.
2. Click **Get API key** → **Create API key**.
3. Copy the key — you will need it in the deploy step.

Store it in a shell variable for convenience:

```bash
export GOOGLE_API_KEY="your_api_key_here"
```

## IAM: Grant Compute Permissions

The Compute Engine default service account needs permission to create and delete VMs. Run:

```bash
PROJECT_ID=$(gcloud config get-value project)

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:$(gcloud iam service-accounts list \
      --project "${PROJECT_ID}" \
      --filter="email:compute@" \
      --format="value(email)")" \
  --role="roles/compute.instanceAdmin.v1"
```

This is the service account both Cloud Run services will run as.

## Deploy the MCP Server

> **Workshop note:** If the instructor has already deployed a shared MCP server and given you a URL, skip this step and use that URL in the next section.

Deploy the MCP server to Cloud Run. This service wraps `gcloud compute` commands and exposes them as MCP tools over SSE:

```bash
bash deploy/mcp_server.sh "${PROJECT_ID}"
```

The script will:
1. Build the container image from `mcp_server/`
2. Deploy it to Cloud Run in `europe-west1`
3. Print the service URL when done

Copy the URL from the output — it looks like:

```
✅ MCP server hazır: https://gcp-mcp-server-XXXXXXXXXX-ew.a.run.app
```

Store it:

```bash
export MCP_SERVER_URL="https://gcp-mcp-server-XXXXXXXXXX-ew.a.run.app"
```

### What's inside the MCP server?

The server (`mcp_server/server.py`) uses [FastMCP](https://github.com/jlowin/fastmcp) and exposes three tools:

| Tool | Description |
|------|-------------|
| `create_vm` | Creates an `e2-micro` Debian VM with nginx startup script |
| `get_vm_status` | Returns the VM's state and external IP |
| `delete_vm` | Deletes the VM |

When deployed, it runs with `MCP_TRANSPORT=sse` and serves requests at `/sse`.

## Deploy the ADK Agent

Now deploy your personal ADK agent and connect it to the MCP server:

```bash
bash deploy/cloud_run.sh "${PROJECT_ID}" "${MCP_SERVER_URL}" "${GOOGLE_API_KEY}"
```

The script will:
1. Build the container image from the repo root
2. Deploy it to Cloud Run with `MCP_SERVER_URL` and `GOOGLE_API_KEY` set as environment variables
3. Print the agent URL when done

Open the printed URL in your browser — you should see the **ADK Web UI**.

### How the connection works

The agent (`agent/agent.py`) checks `MCP_SERVER_URL` at startup:

- If set → connects to the remote MCP server via **SSE** (`MCP_SERVER_URL/sse`)
- If not set → starts a local MCP server subprocess via **stdio** (useful for local development)

## Test the Agent

In the ADK Web UI, try the following prompts one by one:

**1. Create a VM:**
```
Create a VM in project YOUR_PROJECT_ID
```

The agent will ask for confirmation details if needed, then call `create_vm`. Because VM creation is asynchronous (`gcloud ... --async`), it returns immediately with status `provisioning`.

**2. Check the status:**
```
Check the status of that VM
```

The agent calls `get_vm_status`. Repeat until you see `RUNNING` and an external IP address.

**3. Visit nginx:**

Once the VM is `RUNNING`, open `http://EXTERNAL_IP` in your browser. The nginx welcome page appears after ~60 seconds (startup script installs it in the background).

**4. Delete the VM:**
```
Delete the VM
```

The agent confirms the instance name and project, then calls `delete_vm`.

## How the ADK ↔ MCP Connection Works

It's worth understanding what happens under the hood when the agent calls a tool.

```
Agent (Gemini)
  │
  │  "I need to call create_vm"
  ▼
MCPToolset (ADK)
  │
  │  POST /sse  ← MCP protocol over SSE
  ▼
MCP Server (Cloud Run)
  │
  │  subprocess.Popen(["gcloud", "compute", "instances", "create", ...])
  ▼
GCP Compute Engine API
```

The MCP server is just a Python process. It runs `gcloud` as a subprocess using the Cloud Run service account credentials. No SDK calls, no API keys for compute — just `gcloud`.

## Congratulations!

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

You've built and deployed a tool-enabled AI agent that can manage real GCP infrastructure.

### What we covered

- Deploying an MCP server to Cloud Run with SSE transport
- Connecting a Google ADK agent to a remote MCP server
- Using async `gcloud` commands to avoid MCP protocol timeouts
- The stdio → SSE transport switch for local vs. production deployments

<walkthrough-inline-feedback></walkthrough-inline-feedback>

## Clean Up

To avoid ongoing charges, delete the Cloud Run services and any VMs created during the lab.

**Delete Cloud Run services:**

```bash
gcloud run services delete give-your-agent-hands --region europe-west1 --quiet
gcloud run services delete gcp-mcp-server --region europe-west1 --quiet
```

**Delete any remaining VMs:**

```bash
gcloud compute instances list --project "${PROJECT_ID}"
# Then for each VM:
gcloud compute instances delete VM_NAME --zone europe-west1-b --quiet
```
