#!/bin/bash
# deploy/cloud_run.sh
#
# Kullanım:
#   bash deploy/cloud_run.sh PROJECT_ID GOOGLE_API_KEY

set -e

PROJECT_ID=${1:?"Usage: $0 <project_id> <google_api_key>"}
GOOGLE_API_KEY=${2:?"Usage: $0 <project_id> <google_api_key>"}
REGION="europe-west1"
MCP_SERVICE="gcp-mcp-server"
AGENT_SERVICE="give-your-agent-hands"
MCP_IMAGE="gcr.io/${PROJECT_ID}/${MCP_SERVICE}"
AGENT_IMAGE="gcr.io/${PROJECT_ID}/${AGENT_SERVICE}"
SA=$(gcloud iam service-accounts list \
    --project "${PROJECT_ID}" \
    --filter="email:compute@" \
    --format="value(email)")

echo "▶ Building MCP server image..."
gcloud builds submit mcp_server/ \
  --tag "${MCP_IMAGE}" \
  --project "${PROJECT_ID}"

echo "▶ Deploying MCP server to Cloud Run..."
gcloud run deploy "${MCP_SERVICE}" \
  --image "${MCP_IMAGE}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --allow-unauthenticated \
  --service-account "${SA}"

MCP_URL=$(gcloud run services describe "${MCP_SERVICE}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --format="value(status.url)")

echo "▶ Building agent image..."
gcloud builds submit \
  --tag "${AGENT_IMAGE}" \
  --project "${PROJECT_ID}"

echo "▶ Deploying agent to Cloud Run..."
gcloud run deploy "${AGENT_SERVICE}" \
  --image "${AGENT_IMAGE}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},MCP_SERVER_URL=${MCP_URL},GOOGLE_API_KEY=${GOOGLE_API_KEY}" \
  --service-account "${SA}"

AGENT_URL=$(gcloud run services describe "${AGENT_SERVICE}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --format="value(status.url)")

echo ""
echo "✅ Done!"
echo "   Agent     : ${AGENT_URL}"
echo "   MCP server: ${MCP_URL}"
