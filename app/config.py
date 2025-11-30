import os

class Settings:
    def __init__(self):
        self.minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "minio-service:9000")
        self.minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.minio_bucket: str = os.getenv("MINIO_BUCKET", "mlops")
        self.clearml_api_host: str = os.getenv("CLEARML_API_HOST", "http://localhost:8008")
        self.clearml_web_host: str = os.getenv("CLEARML_WEB_HOST", "http://localhost:8080")
        self.clearml_files_host: str = os.getenv("CLEARML_FILES_HOST", "http://localhost:8081")
        self.models_dir: str = os.getenv("MODELS_DIR", "/app/models")
        self.datasets_dir: str = os.getenv("DATASETS_DIR", "/app/datasets")
        self.dvc_remote: str = os.getenv("DVC_REMOTE", "s3://mlops/datasets")
        self.grpc_port: int = int(os.getenv("GRPC_PORT", "50051"))
        self.rest_port: int = int(os.getenv("REST_PORT", "8000"))

settings = Settings()

