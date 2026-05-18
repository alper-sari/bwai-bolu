#!/bin/bash
# deploy/cloud_run.sh
#
# ADK agent'ı Cloud Run'a deploy eder ve MCP server URL'ini bağlar.
#
# Kullanım:
#   bash deploy/cloud_run.sh YOUR_PROJECT_ID MCP_SERVER_URL GOOGLE_API_KEY
#
# Örnek:
#   bash deploy/cloud_run.sh my-project https://gcp-mcp-server-xxx.run.app AIzaSy...

set -e

PROJECT_ID=${1:?"Usage: $0 <project_id> <mcp_server_url> <google_api_key>"}
MCP_SERVER_URL=${2:?"Usage: $0 <project_id> <mcp_server_url> <google_api_key>"}
GOOGLE_API_KEY=${3:?"Usage: $0 <project_id> <mcp_server_url> <google_api_key>"}
REGION="europe-west1"
SERVICE_NAME="give-your-agent-hands"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "▶ Building container image..."
gcloud builds submit \
  --tag "${IMAGE}" \
  --project "${PROJECT_ID}"

echo "▶ Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},MCP_SERVER_URL=${MCP_SERVER_URL},GOOGLE_API_KEY=${GOOGLE_API_KEY}" \
  --service-account "$(gcloud iam service-accounts list \
      --project "${PROJECT_ID}" \
      --filter="email:compute@" \
      --format="value(email)")"

AGENT_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --format="value(status.url)")

echo ""
echo "✅ Agent deployed!"
echo "   Agent URL : ${AGENT_URL}"
echo "   MCP server: ${MCP_SERVER_URL}/sse"
