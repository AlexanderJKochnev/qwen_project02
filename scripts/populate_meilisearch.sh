#!/bin/bash
# Script to populate Meilisearch index with existing data

echo "Populating Meilisearch index with existing data..."
cd /workspace
python3 populate_meilisearch.py
echo "Meilisearch index population completed!"