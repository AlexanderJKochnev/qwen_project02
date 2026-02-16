#!/bin/bash
# создание trigram-indexes
# Определяем путь к директории скрипта
# НЕ НУЖЕН!!!!
docker exec -i wine_host psql -U wine -d wine_db < scripts/create_index.sql
