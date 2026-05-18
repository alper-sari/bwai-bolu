FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

ENV MCP_SERVER_URL=""

CMD ["adk", "web", "--host", "0.0.0.0", "--port", "8080"]
