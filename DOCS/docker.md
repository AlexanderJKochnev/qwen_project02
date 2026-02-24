# for the memory: rare command in docker

1. use customized env file:
   1. docker compose --env-file .env.prod up --build -d
2. use customized docker-compose file
   1. docker compose -f docker-compose.prod.yaml up --build -d
3. use customized prohect_name
   1. docker compose -p super-name-project up --build -d
4. 