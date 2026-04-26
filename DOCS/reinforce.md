docker compose -f docker-compose.xeon.yaml build --no-cache preact_front && docker compose -f docker-compose.xeon.yaml up -d preact_front

docker builder prune -a -f
