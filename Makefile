# Makefile for Multi-tenant Platform
# Usage: make [command]

.PHONY: help
help: ## Show this help message
	@echo "Usage: make [command]"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Docker commands
.PHONY: build
build: ## Build all Docker images
	docker-compose build --parallel

.PHONY: build-no-cache
build-no-cache: ## Build all Docker images without cache
	docker-compose build --no-cache --parallel

.PHONY: up
up: ## Start all services
	docker-compose up -d

.PHONY: down
down: ## Stop all services
	docker-compose down

.PHONY: restart
restart: down up ## Restart all services

.PHONY: clean
clean: ## Stop and remove all containers, volumes, and images
	docker-compose down -v --rmi all

.PHONY: reset
reset: clean build up init-db ## Complete reset: clean, rebuild, and initialize

# Service management
.PHONY: start-infra
start-infra: ## Start only infrastructure services (DB, Redis, RabbitMQ)
	docker-compose up -d postgres redis rabbitmq

.PHONY: start-services
start-services: ## Start only application services
	docker-compose up -d auth-service tenant-service business-service system-service api-gateway

.PHONY: start-frontend
start-frontend: ## Start frontend service
	docker-compose up -d frontend nginx

.PHONY: start-workers
start-workers: ## Start Celery workers and beat
	docker-compose up -d celery-worker celery-beat flower

# Database commands
.PHONY: init-db
init-db: ## Initialize database with admin user and demo data
	docker-compose exec -T auth-service python /app/scripts/init_admin.py || echo "Database already initialized"

.PHONY: migrate
migrate: ## Run database migrations
	docker-compose exec -T system-service alembic upgrade head

.PHONY: db-shell
db-shell: ## Access PostgreSQL shell
	docker-compose exec postgres psql -U postgres multitenant_db

.PHONY: db-backup
db-backup: ## Backup database to file
	@mkdir -p backups
	docker-compose exec -T postgres pg_dump -U postgres multitenant_db | gzip > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql.gz
	@echo "Database backed up to backups/backup_$(shell date +%Y%m%d_%H%M%S).sql.gz"

.PHONY: db-restore
db-restore: ## Restore database from latest backup
	@if [ -z "$(FILE)" ]; then \
		FILE=$$(ls -t backups/*.sql.gz 2>/dev/null | head -1); \
	fi; \
	if [ -z "$$FILE" ]; then \
		echo "No backup file found. Use: make db-restore FILE=path/to/backup.sql.gz"; \
		exit 1; \
	fi; \
	gunzip -c $$FILE | docker-compose exec -T postgres psql -U postgres multitenant_db; \
	echo "Database restored from $$FILE"

# Logs commands
.PHONY: logs
logs: ## Show logs for all services
	docker-compose logs -f

.PHONY: logs-auth
logs-auth: ## Show logs for auth service
	docker-compose logs -f auth-service

.PHONY: logs-tenant
logs-tenant: ## Show logs for tenant service
	docker-compose logs -f tenant-service

.PHONY: logs-business
logs-business: ## Show logs for business service
	docker-compose logs -f business-service

.PHONY: logs-system
logs-system: ## Show logs for system service
	docker-compose logs -f system-service

.PHONY: logs-gateway
logs-gateway: ## Show logs for API gateway
	docker-compose logs -f api-gateway

# Testing commands
.PHONY: test
test: ## Run all tests
	@echo "Running authentication tests..."
	docker-compose exec -T auth-service python /app/tests/test_auth.py

.PHONY: test-auth
test-auth: ## Test authentication service
	docker-compose exec -T auth-service python /app/tests/test_auth.py

.PHONY: test-integration
test-integration: ## Run integration tests
	docker-compose exec -T api-gateway pytest tests/integration/

.PHONY: test-unit
test-unit: ## Run unit tests
	docker-compose exec -T auth-service pytest tests/unit/

# Development commands
.PHONY: shell-auth
shell-auth: ## Access auth service shell
	docker-compose exec auth-service /bin/bash

.PHONY: shell-tenant
shell-tenant: ## Access tenant service shell
	docker-compose exec tenant-service /bin/bash

.PHONY: shell-postgres
shell-postgres: ## Access PostgreSQL container shell
	docker-compose exec postgres /bin/bash

.PHONY: shell-redis
shell-redis: ## Access Redis CLI
	docker-compose exec redis redis-cli

.PHONY: python-auth
python-auth: ## Access Python shell in auth service
	docker-compose exec auth-service python

.PHONY: python-tenant
python-tenant: ## Access Python shell in tenant service
	docker-compose exec tenant-service python

# Status commands
.PHONY: ps
ps: ## Show status of all services
	docker-compose ps

.PHONY: health
health: ## Check health of all services
	@echo "Checking service health..."
	@docker-compose ps | grep -E "(healthy|unhealthy)" || echo "Services are starting..."

.PHONY: stats
stats: ## Show container resource usage
	docker stats --no-stream

# Code quality
.PHONY: format
format: ## Format Python code with black
	docker-compose exec -T auth-service black .
	docker-compose exec -T tenant-service black .
	docker-compose exec -T business-service black .
	docker-compose exec -T system-service black .

.PHONY: lint
lint: ## Run linting checks
	docker-compose exec -T auth-service flake8 .
	docker-compose exec -T tenant-service flake8 .
	docker-compose exec -T business-service flake8 .
	docker-compose exec -T system-service flake8 .

.PHONY: type-check
type-check: ## Run type checking with mypy
	docker-compose exec -T auth-service mypy .
	docker-compose exec -T tenant-service mypy .

# Documentation
.PHONY: docs
docs: ## Generate API documentation
	@echo "Opening API documentation..."
	@open http://localhost:8001/docs || xdg-open http://localhost:8001/docs || echo "Visit http://localhost:8001/docs"

.PHONY: swagger
swagger: docs ## Alias for docs

# Quick actions
.PHONY: quick-start
quick-start: start-infra ## Quick start with minimal services
	@echo "Waiting for infrastructure..."
	@sleep 10
	docker-compose up -d auth-service api-gateway frontend nginx
	@echo "Services started. Visit http://localhost:3000"

.PHONY: dev
dev: ## Start development environment
	docker-compose up

.PHONY: prod
prod: ## Start production environment
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Maintenance
.PHONY: cleanup-logs
cleanup-logs: ## Clean up log files
	@echo "Cleaning up logs..."
	@find . -name "*.log" -type f -delete
	@find . -name "*.log.*" -type f -delete
	@echo "Logs cleaned"

.PHONY: cleanup-pyc
cleanup-pyc: ## Remove Python cache files
	@echo "Removing Python cache files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@echo "Python cache cleaned"

.PHONY: cleanup-all
cleanup-all: cleanup-logs cleanup-pyc ## Clean all temporary files

# Monitoring
.PHONY: monitor
monitor: ## Open monitoring dashboards
	@echo "Opening monitoring dashboards..."
	@echo "RabbitMQ: http://localhost:15672 (admin/admin123)"
	@echo "Flower: http://localhost:5555"

.PHONY: rabbitmq
rabbitmq: ## Open RabbitMQ management console
	@open http://localhost:15672 || xdg-open http://localhost:15672 || echo "Visit http://localhost:15672"

.PHONY: flower
flower: ## Open Flower (Celery monitoring)
	@open http://localhost:5555 || xdg-open http://localhost:5555 || echo "Visit http://localhost:5555"

# Default target
.DEFAULT_GOAL := help
