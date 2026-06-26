#!/usr/bin/env bash
set -e
echo "🚀 Starting Helia..."
docker compose up --build "$@"
