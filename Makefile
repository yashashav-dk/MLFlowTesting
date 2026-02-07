# =============================================================================
# CI/CD Makefile - Local Development & Demonstration
# =============================================================================
#
# This Makefile demonstrates CI/CD concepts using a local Docker registry.
# It simulates what would happen in a real pipeline (GitHub Actions → Docker Hub → Server)
#
# WORKFLOW:
#   1. make ci        → Run linting and tests (Continuous Integration)
#   2. make build     → Build Docker image
#   3. make push      → Push to local registry (simulates Docker Hub)
#   4. make deploy    → Deploy from registry (Continuous Deployment)
#
# Or run everything: make all
# =============================================================================

# Configuration
IMAGE_NAME := ml-api
REGISTRY := localhost:5050
VERSION := $(shell git rev-parse --short HEAD 2>/dev/null || echo "latest")
FULL_IMAGE := $(REGISTRY)/$(IMAGE_NAME):$(VERSION)
LATEST_IMAGE := $(REGISTRY)/$(IMAGE_NAME):latest

.PHONY: all ci lint test build push deploy clean registry-start registry-stop help

# -----------------------------------------------------------------------------
# DEFAULT TARGET
# -----------------------------------------------------------------------------
help:
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║              CI/CD Demo Commands                               ║"
	@echo "╠════════════════════════════════════════════════════════════════╣"
	@echo "║  SETUP:                                                        ║"
	@echo "║    make registry-start   Start local Docker registry           ║"
	@echo "║    make registry-stop    Stop local Docker registry            ║"
	@echo "║                                                                ║"
	@echo "║  CI (Continuous Integration):                                  ║"
	@echo "║    make lint             Run code linting (ruff)               ║"
	@echo "║    make test             Run unit tests (pytest)               ║"
	@echo "║    make ci               Run lint + test                       ║"
	@echo "║                                                                ║"
	@echo "║  CD (Continuous Deployment):                                   ║"
	@echo "║    make build            Build Docker image                    ║"
	@echo "║    make push             Push image to local registry          ║"
	@echo "║    make deploy           Deploy from registry                  ║"
	@echo "║                                                                ║"
	@echo "║  FULL PIPELINE:                                                ║"
	@echo "║    make all              Run complete CI/CD pipeline           ║"
	@echo "║                                                                ║"
	@echo "║  UTILITIES:                                                    ║"
	@echo "║    make status           Show running services                 ║"
	@echo "║    make logs             Show application logs                 ║"
	@echo "║    make clean            Stop all and clean up                 ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"

# -----------------------------------------------------------------------------
# LOCAL REGISTRY (Simulates Docker Hub)
# -----------------------------------------------------------------------------
registry-start:
	@echo "🐳 Starting local Docker registry on port 5050..."
	@docker run -d -p 5050:5000 --restart=always --name local-registry registry:2 2>/dev/null || \
		(docker start local-registry && echo "Registry already exists, started it")
	@echo "✅ Registry running at localhost:5050"
	@echo ""
	@echo "📦 This simulates Docker Hub / ECR / GCR for local development"

registry-stop:
	@echo "🛑 Stopping local registry..."
	@docker stop local-registry 2>/dev/null || true
	@docker rm local-registry 2>/dev/null || true
	@echo "✅ Registry stopped"

# -----------------------------------------------------------------------------
# CI: CONTINUOUS INTEGRATION
# -----------------------------------------------------------------------------
lint:
	@echo "══════════════════════════════════════════════════════════════════"
	@echo "🔍 STEP 1: LINTING - Checking code style..."
	@echo "══════════════════════════════════════════════════════════════════"
	cd ml_api && pip install -q ruff && ruff check . && ruff format --check .
	@echo "✅ Linting passed!"
	@echo ""

test:
	@echo "══════════════════════════════════════════════════════════════════"
	@echo "🧪 STEP 2: TESTING - Running unit tests..."
	@echo "══════════════════════════════════════════════════════════════════"
	cd ml_api && pip install -q -r requirements.txt && pytest tests/ -v --tb=short
	@echo "✅ All tests passed!"
	@echo ""

ci: lint test
	@echo "══════════════════════════════════════════════════════════════════"
	@echo "✅ CI COMPLETE - Code is ready for deployment!"
	@echo "══════════════════════════════════════════════════════════════════"
	@echo ""

# -----------------------------------------------------------------------------
# CD: CONTINUOUS DEPLOYMENT
# -----------------------------------------------------------------------------
build:
	@echo "══════════════════════════════════════════════════════════════════"
	@echo "🐳 STEP 3: BUILD - Building Docker image..."
	@echo "   Image: $(FULL_IMAGE)"
	@echo "══════════════════════════════════════════════════════════════════"
	docker build -t $(FULL_IMAGE) -t $(LATEST_IMAGE) ./ml_api
	@echo "✅ Image built successfully!"
	@echo ""

push:
	@echo "══════════════════════════════════════════════════════════════════"
	@echo "📤 STEP 4: PUSH - Pushing image to registry..."
	@echo "   Registry: $(REGISTRY)"
	@echo "   Image: $(FULL_IMAGE)"
	@echo "══════════════════════════════════════════════════════════════════"
	@docker push $(FULL_IMAGE)
	@docker push $(LATEST_IMAGE)
	@echo "✅ Image pushed to registry!"
	@echo ""
	@echo "📋 Images in registry:"
	@curl -s http://localhost:5050/v2/_catalog | python3 -m json.tool 2>/dev/null || echo "   (registry catalog)"

deploy:
	@echo "══════════════════════════════════════════════════════════════════"
	@echo "🚀 STEP 5: DEPLOY - Deploying from registry..."
	@echo "══════════════════════════════════════════════════════════════════"
	@echo "📥 Pulling latest image from registry..."
	docker pull $(LATEST_IMAGE)
	@echo ""
	@echo "🔄 Restarting services with new image..."
	IMAGE=$(LATEST_IMAGE) docker-compose up -d --force-recreate ml-api
	@echo ""
	@echo "⏳ Waiting for services to be healthy..."
	@sleep 5
	@echo ""
	@echo "🔍 Checking deployment health..."
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "⚠️  Health check pending..."
	@echo ""
	@echo "══════════════════════════════════════════════════════════════════"
	@echo "✅ DEPLOYMENT COMPLETE!"
	@echo "══════════════════════════════════════════════════════════════════"
	@echo ""
	@echo "🌐 Services available at:"
	@echo "   • ML API:      http://localhost:8000"
	@echo "   • API Docs:    http://localhost:8000/docs"
	@echo "   • Prometheus:  http://localhost:9090"
	@echo "   • Grafana:     http://localhost:3000 (admin/admin)"
	@echo ""

# -----------------------------------------------------------------------------
# FULL PIPELINE
# -----------------------------------------------------------------------------
all: ci build push deploy
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║         🎉 FULL CI/CD PIPELINE COMPLETE! 🎉                    ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"

# -----------------------------------------------------------------------------
# UTILITIES
# -----------------------------------------------------------------------------
status:
	@echo "📊 Service Status:"
	@echo ""
	@docker-compose ps
	@echo ""
	@echo "📦 Registry contents:"
	@curl -s http://localhost:5050/v2/_catalog 2>/dev/null | python3 -m json.tool || echo "   Registry not running"

logs:
	docker-compose logs -f ml-api

clean:
	@echo "🧹 Cleaning up..."
	docker-compose down -v
	@docker stop local-registry 2>/dev/null || true
	@docker rm local-registry 2>/dev/null || true
	@echo "✅ Cleanup complete"
