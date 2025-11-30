# PowerShell script for Windows setup

Write-Host "Starting MLOps HW1 setup..." -ForegroundColor Green

Write-Host "`n1. Starting minikube..." -ForegroundColor Yellow
minikube start --driver=docker
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to start minikube" -ForegroundColor Red
    exit 1
}

minikube addons enable ingress

Write-Host "`n2. Configuring Docker environment..." -ForegroundColor Yellow
$dockerEnv = minikube docker-env
if ($dockerEnv) {
    Invoke-Expression $dockerEnv
}

Write-Host "`n3. Building Docker images..." -ForegroundColor Yellow
docker build -t mlops-service:latest -f Dockerfile .
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to build mlops-service image" -ForegroundColor Red
    exit 1
}

docker build -t mlops-dashboard:latest -f Dockerfile.dashboard .
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to build mlops-dashboard image" -ForegroundColor Red
    exit 1
}

Write-Host "`n4. Deploying to Kubernetes..." -ForegroundColor Yellow
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/minio.yaml
kubectl apply -f k8s/mlops-service.yaml
kubectl apply -f k8s/dashboard.yaml

Write-Host "`n5. Waiting for services to be ready..." -ForegroundColor Yellow
kubectl wait --for=condition=available --timeout=300s deployment/mlops-service -n mlops
kubectl wait --for=condition=available --timeout=300s deployment/mlops-dashboard -n mlops

Write-Host "`n6. Starting ClearML services..." -ForegroundColor Yellow
docker-compose up -d

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "`nDashboard URL:" -ForegroundColor Cyan
minikube service mlops-dashboard -n mlops --url
Write-Host "`nClearML Web UI: http://localhost:8080" -ForegroundColor Cyan
Write-Host "ClearML API: http://localhost:8008" -ForegroundColor Cyan

