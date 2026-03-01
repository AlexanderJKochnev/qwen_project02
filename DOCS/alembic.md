### alembic hints

1. потряны ревизии:
   1. удалить все из migration_volume
   2. docker exec test-wine_host-1 psql -U wine -d wine_db -c "DELETE FROM alembic_version;"
   3. docker exec test-app-1 alembic stamp head
   4. sh alembic.sh