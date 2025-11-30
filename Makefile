.PHONY: help build push deploy clean start stop minikube-start minikube-stop

help:
	@echo "Available targets:"
	@echo "  make build          - Build Docker images"
	@echo "  make deploy         - Deploy to minikube"
	@echo "  make start          - Start ClearML services"
	@echo "  make stop           - Stop ClearML services"
	@echo "  make clean          - Clean up resources"
	@echo "  make minikube-start - Start minikube"
	@echo "  make minikube-stop  - Stop minikube"

minikube-start:
	minikube start --driver=docker
	minikube addons enable ingress
	eval $$(minikube docker-env)

minikube-stop:
	minikube stop

build:
	@if [ "$(shell uname -s)" = "Linux" ] || [ "$(shell uname -s)" = "Darwin" ]; then \
		eval $$(minikube docker-env) && \
		docker build -t mlops-service:latest -f Dockerfile . && \
		docker build -t mlops-dashboard:latest -f Dockerfile.dashboard .; \
	else \
		echo "For Windows, please use PowerShell script: .\setup.ps1"; \
		echo "Or configure Docker environment manually:"; \
		echo "  minikube docker-env | Invoke-Expression"; \
		echo "  docker build -t mlops-service:latest -f Dockerfile ."; \
		echo "  docker build -t mlops-dashboard:latest -f Dockerfile.dashboard ."; \
	fi

deploy:
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/minio.yaml
	kubectl apply -f k8s/mlops-service.yaml
	kubectl apply -f k8s/dashboard.yaml
	@echo "Waiting for services to be ready..."
	kubectl wait --for=condition=available --timeout=300s deployment/mlops-service -n mlops
	kubectl wait --for=condition=available --timeout=300s deployment/mlops-dashboard -n mlops
	@echo "Services deployed!"
	@echo "Dashboard URL: $$(minikube service mlops-dashboard -n mlops --url)"

start:
	docker-compose up -d
	@echo "ClearML services started"
	@echo "ClearML Web UI: http://localhost:8080"
	@echo "ClearML API: http://localhost:8008"

stop:
	docker-compose down

clean:
	kubectl delete namespace mlops --ignore-not-found=true
	docker-compose down -v

all:
	@if [ "$(shell uname -s)" = "Linux" ] || [ "$(shell uname -s)" = "Darwin" ]; then \
		$(MAKE) minikube-start && \
		$(MAKE) build && \
		$(MAKE) deploy && \
		$(MAKE) start && \
		echo "Everything is set up!" && \
		echo "Dashboard: $$(minikube service mlops-dashboard -n mlops --url)" && \
		echo "ClearML: http://localhost:8080"; \
	else \
		echo "For Windows, please use PowerShell script: .\setup.ps1"; \
		echo "Or run commands manually:"; \
		echo "  1. minikube start --driver=docker"; \
		echo "  2. minikube docker-env | Invoke-Expression"; \
		echo "  3. docker build -t mlops-service:latest -f Dockerfile ."; \
		echo "  4. docker build -t mlops-dashboard:latest -f Dockerfile.dashboard ."; \
		echo "  5. kubectl apply -f k8s/"; \
		echo "  6. docker-compose up -d"; \
	fi

