#!/bin/bash
# Docker Cleanup Script

set -euo pipefail

echo "Removing stopped containers..."
docker container prune -f

echo "Removing dangling images..."
docker image prune -f

echo "Removing unused images..."
docker image prune -a -f

echo "Removing unused networks..."
docker network prune -f

echo "Removing unused volumes..."
docker volume prune -f

echo "Removing build cache..."
docker builder prune -f

echo "Docker cleanup complete."
