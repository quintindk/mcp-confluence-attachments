FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script
COPY download_attachments.py .

# Create a non-root user to run the application
RUN useradd -m -u 1000 appuser && \
    mkdir -p /output && \
    chown -R appuser:appuser /app /output

# Set the script as executable
RUN chmod +x download_attachments.py

# Switch to non-root user
USER appuser

# Set environment variables with defaults
ENV CONFLUENCE_URL=""
ENV CONFLUENCE_PERSONAL_TOKEN=""

# Run the script by default
ENTRYPOINT ["python", "download_attachments.py"]
CMD ["--help"]
