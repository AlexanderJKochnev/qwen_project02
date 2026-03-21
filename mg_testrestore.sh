#!/bin/bash
# восстановление mongodb
BACKUP_NAME="mg_backup.gz"

# docker exec -i имя_контейнера mongorestore --archive --gzip --db имя_базы < backup.gz
# docker exec -i mongo mongorestore --archive --gzip --nsInclude='wine_database.*' < backup/$BACKUP_NAME
docker exec -i test-mongo-1 mongorestore \
  --username=admin \
  --password=admin \
  --authenticationDatabase=admin \
  --archive \
  --gzip \
  --drop \
  --nsInclude="wine_database.*" < backup/mg_backup.gz
