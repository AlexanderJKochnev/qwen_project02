# логирование
from loguru import logger

# Настройка в одну строку: пишем в файл, ротируем при достижении 500 МБ
logger.add("debug.log", rotation="500 MB", compression="zip")

logger.info("Скрипт запущен")
logger.error("Что-то пошло не так!")

@logger.catch  # Ловит любые ошибки внутри и выводит подробный traceback
def critical_function():
    return 1 / 0

critical_function()


-----
import time
import sys
from fastapi import FastAPI, Request
from loguru import logger

app = FastAPI()

# 1. Настройка Loguru
logger.remove()  # Удаляем стандартный обработчик
logger.add(
    sys.stdout, 
    colorize=True, 
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",
    enqueue=True  # ВАЖНО: делает логирование неблокирующим (использует очередь)
)
logger.add("logs/app.log", rotation="500 MB", retention="10 days", compression="zip", enqueue=True)

# 2. Middleware для автоматического логирования всех запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Логируем начало запроса
    logger.info(f"Начало запроса: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = "{0:.2f}".format(process_time)
    
    # Логируем завершение и время выполнения
    logger.info(f"Завершено: {request.method} {request.url.path} | Статус: {response.status_code} | Время: {formatted_process_time}мс")
    
    return response

# 3. Пример эндпоинта
@app.get("/")
async def root():
    logger.debug("Обработка главной страницы")
    return {"status": "ok"}

@app.get("/error")
async def trigger_error():
    try:
        1 / 0
    except ZeroDivisionError:
        # Автоматический лог ошибки с трассировкой стека и значениями переменных
        logger.exception("Произошла ошибка деления на ноль!")
    return {"status": "error handled"}

# @logger.catch(reraise=True)

Декоратор
@logger.catch — это одна из самых мощных функций Loguru. 
Он предназначен для того, чтобы «ловить» любые ошибки внутри функции и автоматически записывать их в лог 
с полной трассировкой стека (stack trace).
reraise=True использовать. что logger не глотал ошибки, а передавал дальше.