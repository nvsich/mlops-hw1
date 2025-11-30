FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. app/api/grpc_api.proto

EXPOSE 8000 50051

CMD ["python", "main.py"]

