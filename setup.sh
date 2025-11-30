#!/bin/bash

echo "Starting MLOps HW1 setup..."

echo ""
echo "1. Starting minikube..."
minikube start --driver=docker
if [ $? -ne 0 ]; then
    echo "Failed to start minikube"
    exit 1
fi

minikube addons enable ingress

echo ""
echo "2. Configuring Docker environment..."
eval $(minikube docker-env)

echo ""
echo "3. Building Docker images..."
docker build -t mlops-service:latest -f Dockerfile .
if [ $? -ne 0 ]; then
    echo "Failed to build mlops-service image"
    exit 1
fi

docker build -t mlops-dashboard:latest -f Dockerfile.dashboard .
if [ $? -ne 0 ]; then
    echo "Failed to build mlops-dashboard image"
    exit 1
fi

echo ""
echo "4. Deploying to Kubernetes..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/minio.yaml
kubectl apply -f k8s/mlops-service.yaml
kubectl apply -f k8s/dashboard.yaml

echo ""
echo "5. Waiting for services to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/mlops-service -n mlops
kubectl wait --for=condition=available --timeout=300s deployment/mlops-dashboard -n mlops

echo ""
echo "6. Starting ClearML services..."
docker-compose up -d

echo ""
echo "Setup complete!"
echo ""
echo "Dashboard URL:"
minikube service mlops-dashboard -n mlops --url
echo ""
echo "ClearML Web UI: http://localhost:8080"
echo "ClearML API: http://localhost:8008"
