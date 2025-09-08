FROM python:3.11-slim

WORKDIR /app

COPY services/data_generator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/data_generator/server.py .
COPY services/data_generator/proto ./proto

# Generate protobuf files
RUN python -m grpc_tools.protoc \
    --python_out=. \
    --grpc_python_out=. \
    -I./proto \
    proto/data_generator.proto

EXPOSE 50051

CMD ["python", "server.py"]