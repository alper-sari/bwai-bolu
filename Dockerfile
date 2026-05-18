FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    apt-transport-https \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
       > /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg \
       | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
    && apt-get update && apt-get install -y google-cloud-cli \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

# MCP_SERVER_URL: deploy edilmiş MCP server'ın Cloud Run URL'i
# Örnek: https://gcp-mcp-server-xxx.run.app
ENV MCP_SERVER_URL=""

CMD ["adk", "web", "--host", "0.0.0.0", "--port", "8080"]
