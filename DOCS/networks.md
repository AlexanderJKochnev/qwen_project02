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