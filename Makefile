# ─────────────────────────────────────────────────────────────────────────────
# Helia — Makefile
# Simple commands for common operations
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: help dev prod down logs ps clean setup

# ── Default target ─────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  Helia — Healthcare Appointment Booking Platform"
	@echo "  ─────────────────────────────────────────────────"
	@echo ""
	@echo "  make setup    Copy .env.example to .env (first time only)"
	@echo "  make dev      Start in development mode (MinIO + Mailhog, no AWS needed)"
	@echo "  make prod     Start in production mode (AWS S3 + SES + Secrets Manager)"
	@echo "  make down     Stop all containers"
	@echo "  make logs     Stream logs from all containers"
	@echo "  make ps       Show container status"
	@echo "  make clean    Stop containers and remove volumes (WARNING: deletes data)"
	@echo ""

# ── First-time setup ───────────────────────────────────────────────────────────
setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ .env created from .env.example"; \
		echo "   Review .env and update values if needed"; \
	else \
		echo "⚠️  .env already exists — not overwritten"; \
	fi

# ── Development mode ───────────────────────────────────────────────────────────
# Automatically merges docker-compose.yml + docker-compose.override.yml
# MinIO replaces S3, Mailhog catches emails, all ports exposed
dev:
	@echo "🚀 Starting Helia in development mode..."
	@echo "   MinIO console:  http://localhost:9001"
	@echo "   Mailhog UI:     http://localhost:8025"
	@echo "   App:            http://localhost"
	@echo "   API docs:       http://localhost:8001/docs"
	@echo ""
	docker compose up --build

dev-detached:
	docker compose up --build -d
	@echo "✅ Helia running in background"
	@echo "   Use 'make logs' to stream logs"
	@echo "   Use 'make down' to stop"

# ── Production mode ────────────────────────────────────────────────────────────
# Uses only docker-compose.yml — no MinIO, no Mailhog, no exposed ports
# Requires: IAM role on EC2, secrets in AWS Secrets Manager, S3 bucket
prod:
	@echo "🚀 Starting Helia in production mode..."
	@echo "   Requires AWS IAM role, Secrets Manager, and S3 bucket"
	@echo ""
	docker compose -f docker-compose.yml up --build -d
	@echo "✅ Helia running in production mode"

prod-logs:
	docker compose -f docker-compose.yml logs -f

# ── Common operations ──────────────────────────────────────────────────────────
down:
	docker compose down
	@echo "✅ All containers stopped"

logs:
	docker compose logs -f

ps:
	docker compose ps

# ── Nuclear option ─────────────────────────────────────────────────────────────
clean:
	@echo "⚠️  This will delete all containers AND volumes (all data will be lost)"
	@read -p "   Are you sure? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker compose down -v --remove-orphans; \
		echo "✅ Containers and volumes removed"; \
	else \
		echo "❌ Cancelled"; \
	fi
