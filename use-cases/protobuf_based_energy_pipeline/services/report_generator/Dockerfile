FROM python:3.11-slim

WORKDIR /app

COPY services/report_generator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared proto and service proto
COPY shared/proto/common.proto ./proto/
COPY services/report_generator/proto/ ./proto/

# Compile protos (common first, then service proto that imports it)
RUN python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. proto/common.proto
RUN python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. proto/report_generator.proto

COPY services/report_generator/server.py .

ENV GRPC_PORT=50051

EXPOSE 50051

CMD ["python", "server.py"]