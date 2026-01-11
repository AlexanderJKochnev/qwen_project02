# app/core/exceptions.py

from fastapi import HTTPException, status
import logging

# Отключение логирования
logging.disable(logging.CRITICAL)


def exception_to_http(e: Exception) -> HTTPException:
    error_message = str(e)
    ERROR_MAPPING = {"UNKNOWN_ERROR:": (status.HTTP_500_INTERNAL_SERVER_ERROR, True),
                     "DATABASE_ERROR:": (status.HTTP_500_INTERNAL_SERVER_ERROR, True),
                     "NOT_FOUND:": (status.HTTP_404_NOT_FOUND, False),
                     "VALIDATION_ERROR:": (status.HTTP_400_BAD_REQUEST, False),
                     "AUTH_ERROR:": (status.HTTP_401_UNAUTHORIZED, False),
                     "PERMISSION_ERROR:": (status.HTTP_403_FORBIDDEN, False),
                     "CONFLICT:": (status.HTTP_409_CONFLICT, False),
                     "RATE_LIMIT:": (status.HTTP_429_TOO_MANY_REQUESTS, False), }

    error_message = str(e)

    for prefix, (status_code, should_log) in ERROR_MAPPING.items():
        if error_message.startswith(prefix):
            if should_log:
                # logging.error(f"Server error {prefix}: {e}", exc_info=True)  # Логирование отключено
                pass
            return HTTPException(status_code=status_code,
                                 detail=error_message.replace(prefix, "").strip()
                                 if not should_log else "Внутренняя ошибка сервера")

    # Если не нашли подходящий префикс
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
