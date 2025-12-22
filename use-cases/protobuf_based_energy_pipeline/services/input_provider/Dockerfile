FROM python:3.11-slim

WORKDIR /app

COPY services/input_provider/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/input_provider/handler.py .
COPY services/input_provider/service.py .

ENV HOST=0.0.0.0
ENV PORT=8080

EXPOSE 8080

CMD ["python", "service.py"]
