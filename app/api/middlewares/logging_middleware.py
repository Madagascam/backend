import time
from typing import Callable

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()

        with logger.catch():
            logger.info(f"Request started: {request.method} {request.url.path}")

            response = await call_next(request)

            process_time = time.time() - start_time

            logger.info(f"Request completed: {response.status_code} (took {process_time:.3f}s)")

            return response
