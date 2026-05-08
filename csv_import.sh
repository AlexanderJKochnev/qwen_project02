#!/bin/bash
# импорт csv файла в postgresql
# файл сым  должен быть в директории со скриптом и docker-compose

# Если CSV С заголовком (пропустит первую строку)
cat synonyms_data.csv | docker-compose exec -T wine_host psql -U wine -d wine_db -c "\copy trichins(word, synonym) FROM STDIN CSV HEADER"
