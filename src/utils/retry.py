import time
import random
import functools
from loguru import logger
from ..common.constants import MAX_RETRIES


def retry(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        for _ in range(MAX_RETRIES):
            try:
                res = func(*args, **kwargs)
                return res
            except Exception as e:
                logger.warning(f"{func.__name__} - exception: {str(e)}")
                if "insufficient funds" in str(e):
                    return
                if "already claimed" in str(e):
                    return
                time.sleep(random.randint(5, 10))
        else:
            return

    return wrapper
