.PHONY: help build run stop clean test dev logs shell

help:
	@echo "OrcaSlicer API - Available commands:"
	@echo ""
	@echo "  make build       - Build Docker image"
	@echo "  make run         - Run with docker-compose"
	@echo "  make stop        - Stop docker-compose"
	@echo "  make clean       - Remove containers and volumes"
	@echo "  make test        - Run tests"
	@echo "  make dev         - Run in development mode (local)"
	@echo "  make logs        - View container logs"
	@echo "  make shell       - Open shell in container"
	@echo ""

build:
	docker build -t orcaslicer-api:latest .

run:
	docker-compose up -d
	@echo "API running at http://localhost:8000"
	@echo "Docs available at http://localhost:8000/docs"

stop:
	docker-compose down

clean:
	docker-compose down -v
	rm -rf data/

test:
	pytest tests/ -v

dev:
	python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

logs:
	docker-compose logs -f

shell:
	docker exec -it orcaslicer-api /bin/bash
