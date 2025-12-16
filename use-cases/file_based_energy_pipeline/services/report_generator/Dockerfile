FROM python:3.11-slim

WORKDIR /app

COPY services/report_generator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/report_generator/handler.py .
COPY services/report_generator/service.py .

EXPOSE 8080

CMD ["python", "service.py"]
