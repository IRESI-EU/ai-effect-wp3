FROM python:3.11-slim

WORKDIR /app

COPY services/data_generator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy needed protos (no input_provider - config comes inline)
COPY shared/proto/common.proto ./proto/
COPY services/data_generator/proto/ ./proto/

# Compile protos (with gRPC stubs)
RUN python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. proto/common.proto
RUN python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. proto/data_generator.proto

COPY services/data_generator/handler.py .
COPY services/data_generator/service.py .

ENV HOST=0.0.0.0
ENV PORT=8080
ENV GRPC_PORT=50051

EXPOSE 8080 50051

CMD ["python", "service.py"]
