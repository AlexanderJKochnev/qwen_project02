### alembic hints

1. потряны ревизии: (ОБРАЩАЙ ВНИМАНИЕ НА НАЗВАНИЕ СЕРВИСОВ prod-wine_host1 ИЛИ test-wine_host1)
   1. удалить все из migration_volume
   2. docker exec test-wine_host-1 psql -U wine -d wine_db -c "DELETE FROM alembic_version;"
   3. docker exec test-app-1 alembic stamp head
   4. sh alembic.sh
   5. docker exec <имя_контейнера> alembic revision --autogenerate -m "Initial"
2. сложная ручная миграция
   1. docker compose -f docker-compose.xeon.yaml exec app alembic revision -m "move_drinks_to_sites"
   2. Alembic создаст файл в папке alembic/versions/. Открой его и замени содержимое функций upgrade и downgrade на код из move_drinks_to_sites
   3. docker compose -f docker-compose.xeon.yaml exec app alembic upgrade head
   4. docker compose -f docker-compose.xeon.yaml exec app alembic downgrade -1  # если что-то пошло не так
3. посмотреть таблицу
   1. docker exec test-wine_host-1 psql -U wine -d wine_db -c "\d sites"
   2. docker exec test-wine_host-1 psql -U wine -d wine_db -c "\d drinks"


