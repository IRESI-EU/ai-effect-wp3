FROM python:3.11-slim

WORKDIR /app

COPY services/input_provider/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/input_provider/ .

CMD ["python", "server.py"]
