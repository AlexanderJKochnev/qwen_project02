##  загрузка и установка ollama
1. все написано в docker-compose-.xeon.yaml 
2. при первом запуске (если потом не сделаю автозагрузчик):
   1. docker exec -it ollama ollama pull translategemma  # модель 2b дообученная
   2. docker exec -it ollama ollama pull gemma2:9b # модель 9б  
   3. docker exec -it ollama ollama pull gemma2:27b
   4. docker exec -it ollama ollama pull qwen2.5:7b
   5. docker exec -it ollama ollama list # проверка какие модели загружены

3. Ollama держит модель в памяти (VRAM) в течение 5 минут после последнего запроса (по умолчанию). 
4. Чтобы увидеть, что именно загружено прямо сейчас:
   1. docker exec -it ollama ollama ps
   2. nvidia-smi # загрузка видеокарты
5. настройки взаимодействия с LLM
6. запуск теста (в консоли)
   1. уу
   2. docker cp app:/app/bench_20260218_092133.csv ./результат.csv # название файла см в консоли
