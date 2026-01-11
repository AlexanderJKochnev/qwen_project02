import logging

# Отключение логирования
logger = logging.getLogger(__name__)
logger.disabled = True

s_handler = logging.StreamHandler()
f_handler = logging.FileHandler('log')
s_handler.setLevel(logging.WARNING)
f_handler.setLevel(logging.ERROR)

s_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
f_format = logging.Formatter('%(name)s - %(asctime)s - %(message)s')
s_handler.setFormatter(s_format)
f_handler.setFormatter(f_format)

logger.addHandler(s_handler)
# logger.addHandler(f_handler)
