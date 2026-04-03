# Сети и IP
# сети для prod 172.2x.0.0/24
# для Test сдвиньте подсети: 172.30.x.x, 172.31.x.x
# для local сдвиньте подсети: 172.40.x.x, 172.41.x.x

##  внутренние сети (только для связи внутри проекта - не имеют name)
1. postgres_network  # postrgesql <-> pgbouncer
2. pgbouncer_network # pgbouncer <-> app
3. mongodb_network   # mongobd <-> app
4. preact_network    # preact <-> app
##  внешние сети (для связи между проектами - есть name для идентификации)
1. nginx_gateway_shared_network: owner nginx_gateway
2. vllm_network:                 owner nginx_gateway (все общее)
3. clickhouse_network:           owner nginx_gateway (общий сервис/создать и настроить таблицы для теста и prod)
4. clickhousepg_network          owner nginx_gateway
5. redis_network                 N/A
6. searxng_network               N/A
7. ollama_network                N/A

###  диагностика сетей
1. список активных контерйнеров
   1. docker ps --format "table {{.Names}}\t{{.Status}}"
2. список сетей
   1. docker network ls
3. список контейнеров в сети
   1. docker network inspect <network> | grep -A 20 "Containers"
4. сетевая связность
   1. docker inspect prod-app-1 | grep -A 5 "Networks"
   2. docker inspect prod-preact_front-1 | grep -A 5 "Networks"
   3. docker inspect nginx_gateway | grep -A 20 "Networks"
5. видит ли Nginx другие сервисы
6. 