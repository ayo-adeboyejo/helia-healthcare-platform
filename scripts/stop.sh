#!/usr/bin/env bash
echo "🛑 Stopping Helia..."
docker compose down "$@"
echo "✅ Done. Run with -v flag to also remove volumes: ./scripts/stop.sh -v"
