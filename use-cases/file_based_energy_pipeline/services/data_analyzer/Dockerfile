FROM python:3.11-slim

WORKDIR /app

COPY services/data_analyzer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/data_analyzer/handler.py .
COPY services/data_analyzer/service.py .

EXPOSE 8080

CMD ["python", "service.py"]
