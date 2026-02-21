#!/bin/bash

# миграции в postgersql после обновления структуры models
docker compose -f docker-compose.test.yaml exec app_test alembic revision --autogenerate -m 'Restart revision'
docker compose -f docker-compose.test.yaml exec app_test alembic upgrade head
# alembic revision --autogenerate -m 'Restart revision'
# alembic upgrade head