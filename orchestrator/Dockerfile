FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy orchestrator source code
COPY orchestrator.py .
COPY src/ ./src/

# Create logs directory
RUN mkdir -p logs

# Entry point
ENTRYPOINT ["python", "orchestrator.py"]
