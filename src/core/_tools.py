import time
from loguru import logger

from typing import Callable, Awaitable, Any
from functools import wraps


def logging(show_result: bool = False, show_input: bool = False):
    """Декоратор что-бы логировать количество времени на выполнение команды

    Args:
        show_result (bool, optional): Показывать результат в конце, удобно для дебага. По умолчанию False.
        show_input (bool, optional): Показывать входящие данные. По умолчанию False.
    """

    def decorator(func: Callable[..., Awaitable[Any]]):
        func_path = f"{func.__module__}.{func.__qualname__}"

        @wraps(func)
        async def wrapper(*args, **kwargs):
            result: Any | None = None
            start_time = time.time()
            try:
                if show_input:
                    logger.debug(
                        f"Запуск функции {func_path} с аргументами: {args}, {kwargs}"
                    )
                result = await func(*args, **kwargs)
                return result

            except Exception as e:
                logger.error(f"Ошибка в функции {func_path}: {e}")
                raise

            finally:
                logger.debug(
                    f"Функция {func_path} выполнена за {time.time() - start_time:.2f} секунд"
                )
                if show_result and not callable(show_result):
                    logger.debug(f"Результат функции {func_path}: {result}")

        return wrapper

    if callable(show_result):
        return decorator(show_result)

    return decorator
