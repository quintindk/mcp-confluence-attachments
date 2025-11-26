FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the MCP server files
COPY config.py .
COPY confluence_client.py .
COPY confluence_mcp_server.py .
COPY download_attachments.py .

# Create a non-root user to run the application
RUN useradd -m -u 1000 appuser && \
    mkdir -p /output && \
    chown -R appuser:appuser /app /output

# Set scripts as executable
RUN chmod +x confluence_mcp_server.py download_attachments.py

# Switch to non-root user
USER appuser

# Set environment variables with defaults
ENV CONFLUENCE_URL=""
ENV CONFLUENCE_PERSONAL_TOKEN=""
ENV MCP_TRANSPORT="sse"
ENV MCP_HOST="0.0.0.0"
ENV MCP_PORT="8080"
ENV MCP_DEBUG="false"
ENV LOG_LEVEL="INFO"

# Expose MCP server port
EXPOSE 8080

# Run the MCP server by default
ENTRYPOINT ["python", "confluence_mcp_server.py"]
