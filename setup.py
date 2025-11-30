from setuptools import setup, find_packages

setup(
    name="mlops-hw1",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "pydantic==2.5.0",
        "grpcio==1.60.0",
        "grpcio-tools==1.60.0",
        "protobuf==4.25.1",
        "scikit-learn==1.3.2",
        "pandas==2.1.4",
        "numpy==1.26.2",
        "streamlit==1.29.0",
        "clearml==1.14.0",
        "dvc==3.9.0",
        "dvc-s3==3.1.0",
        "boto3==1.34.0",
        "python-multipart==0.0.6",
        "aiofiles==23.2.1",
        "pyyaml==6.0.1",
        "requests==2.31.0",
    ],
)

