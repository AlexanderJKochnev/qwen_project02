#!/bin/bash
# Script to populate Meilisearch index with existing data переделать нахрен что б работало

echo "Populating Meilisearch index with existing data..."
docker compose exec app python -m populate_meilisearch
echo "Meilisearch index population completed!"