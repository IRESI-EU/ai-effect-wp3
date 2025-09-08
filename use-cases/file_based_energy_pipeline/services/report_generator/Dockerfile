FROM python:3.11-slim

WORKDIR /app

COPY services/report_generator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/report_generator/server.py .
COPY services/report_generator/proto ./proto

# Generate protobuf files
RUN python -m grpc_tools.protoc \
    --python_out=. \
    --grpc_python_out=. \
    -I./proto \
    proto/report_generator.proto

EXPOSE 50053

CMD ["python", "server.py"]