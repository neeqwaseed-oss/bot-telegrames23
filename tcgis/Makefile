# TCGIS Makefile

.PHONY: help install dev build up down logs test clean

help:
	@echo "TCGIS - Telegram Country Group Indexing System"
	@echo ""
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make dev        - Start development environment"
	@echo "  make build      - Build Docker images"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make logs       - View logs"
	@echo "  make test       - Run tests"
	@echo "  make clean      - Clean up"

install:
	pip install -r requirements.txt

dev:
	docker-compose -f docker-compose.yml up --build

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

test:
	pytest src/ -v

clean:
	docker-compose down -v
	docker system prune -f
