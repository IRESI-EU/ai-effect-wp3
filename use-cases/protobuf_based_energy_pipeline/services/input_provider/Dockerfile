FROM python:3.11-slim

WORKDIR /app

COPY services/input_provider/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy proto and compile (with gRPC stubs)
COPY services/input_provider/proto/ ./proto/
RUN python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. proto/input_provider.proto

COPY services/input_provider/handler.py .
COPY services/input_provider/service.py .

ENV HOST=0.0.0.0
ENV PORT=8080
ENV GRPC_PORT=50051

EXPOSE 8080 50051

CMD ["python", "service.py"]
