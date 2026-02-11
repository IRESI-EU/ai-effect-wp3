FROM python:3.12-slim

WORKDIR /app

COPY services/output_formatter/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common/ ./common/
COPY services/output_formatter/service.py .

EXPOSE 8080

CMD ["python", "service.py"]
