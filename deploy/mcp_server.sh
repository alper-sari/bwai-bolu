#!/bin/bash
# deploy/mcp_server.sh
#
# MCP server'ı Cloud Run'a ayrıca deploy eder.
# Katılımcılar bu URL'i ADK agent'a MCP_SERVER_URL olarak verir.
#
# Kullanım:
#   bash deploy/mcp_server.sh YOUR_PROJECT_ID

set -e

PROJECT_ID=${1:?"Usage: $0 <project_id>"}
REGION="europe-west1"
SERVICE_NAME="gcp-mcp-server"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "▶ Building MCP server image..."
gcloud builds submit mcp_server/ \
  --tag "${IMAGE}" \
  --project "${PROJECT_ID}"

echo "▶ Deploying MCP server to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --allow-unauthenticated \
  --set-env-vars "MCP_TRANSPORT=sse,GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --service-account "$(gcloud iam service-accounts list \
      --project "${PROJECT_ID}" \
      --filter="email:compute@" \
      --format="value(email)")"

MCP_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --format="value(status.url)")

echo ""
echo "✅ MCP server hazır: ${MCP_URL}"
echo ""
echo "ADK agent'ı bu sunucuya bağlamak için:"
echo "  bash deploy/cloud_run.sh ${PROJECT_ID} --mcp-url ${MCP_URL}"
