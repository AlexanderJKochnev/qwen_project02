## Особенности  production version

1. строка запуска: docker compose -f docker-compose.prod.yaml up --build -d
2. mongodb heatlhcheck (не трогать пока работает. при запуске новой версии измени healthchek строку на следующую. проверь переменные)
   healthcheck:
      test: >
        mongo --username ${MONGO_INITDB_ROOT_USERNAME}
        --password ${MONGO_INITDB_ROOT_PASSWORD}
        --authenticationDatabase admin
        --eval 'db.runCommand("ping").ok'
        localhost:${MONGODB_PORT}/admin --quiet
3. mongodb при новом запуске закоменнтить эту строку # - ./mongo/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
4. nginx - 