FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../.. /workspace
WORKDIR /workspace/gami-protocol-mcp/backend

ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/gcp-service-account.json \
    QUEST_AGENT_URL=http://quest_agent:8001 \
    ECONOMY_AGENT_URL=http://economy_agent:8002 \
    SECURITY_AGENT_URL=http://security_agent:8003 \
    MCP_SUPERVISOR_URL=http://mcp_supervisor:8800/mcp \
    BACKEND_HOST=0.0.0.0 \
    BACKEND_PORT=9000 \
    SSE_CHANNEL=agent-events

EXPOSE 9000 9300

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
