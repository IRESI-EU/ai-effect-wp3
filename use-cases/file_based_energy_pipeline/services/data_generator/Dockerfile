FROM python:3.11-slim

WORKDIR /app

COPY services/data_generator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/data_generator/handler.py .
COPY services/data_generator/service.py .

EXPOSE 8080

CMD ["python", "service.py"]
