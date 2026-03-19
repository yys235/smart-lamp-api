.PHONY: help build dev prod up down restart logs shell test lint format clean

# Default target
help:
	@echo "Smart Lamp API - Docker Commands"
	@echo ""
	@echo "Development:"
	@echo "  make build      - Build development image"
	@echo "  make dev        - Run development server with hot reload"
	@echo "  make up         - Start production containers"
	@echo "  make down       - Stop all containers"
	@echo "  make restart    - Restart production containers"
	@echo "  make logs       - View container logs"
	@echo "  make shell      - Open shell in running container"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linter (ruff)"
	@echo "  make format     - Format code (black)"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean      - Remove containers, images, and volumes"

# Build development image
build:
	docker-compose build api-dev

# Run development server
dev:
	docker-compose --profile dev up

# Start production containers
up:
	docker-compose up -d

# Stop all containers
down:
	docker-compose down

# Restart production containers
restart:
	docker-compose restart

# View container logs
logs:
	docker-compose logs -f api

# Open shell in container
shell:
	docker-compose exec api bash

# Run tests
test:
	docker-compose exec api pytest -v

# Run linter
lint:
	docker-compose exec api ruff check app/

# Format code
format:
	docker-compose exec api black app/

# Clean up
clean:
	docker-compose down -v
	docker system prune -f
