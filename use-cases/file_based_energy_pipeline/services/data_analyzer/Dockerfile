FROM python:3.11-slim

WORKDIR /app

COPY services/data_analyzer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/data_analyzer/server.py .
COPY services/data_analyzer/proto ./proto

# Generate protobuf files
RUN python -m grpc_tools.protoc \
    --python_out=. \
    --grpc_python_out=. \
    -I./proto \
    proto/data_analyzer.proto

EXPOSE 50052

CMD ["python", "server.py"]