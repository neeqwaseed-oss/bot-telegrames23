"""
TCGIS - API Gateway Logging Middleware
"""

import time
import logging
from fastapi import Request, Response


logger = logging.getLogger("tcgis.api")


def log_request(request: Request):
    """تسجيل الطلب"""
    logger.info(
        f"Request: {request.method} {request.url.path} - "
        f"Client: {request.client.host} - "
        f"User-Agent: {request.headers.get('user-agent', 'unknown')}"
    )


def log_response(request: Request, response: Response, duration: float):
    """تسجيل الاستجابة"""
    logger.info(
        f"Response: {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.3f}s"
    )
