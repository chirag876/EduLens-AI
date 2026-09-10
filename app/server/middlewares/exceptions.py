import contextlib
import time
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from jose import ExpiredSignatureError, JWTError
from starlette.middleware.base import BaseHTTPMiddleware

from app.server.logger.custom_logger import logger
from app.server.static import localization


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware to handles exceptions in HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next):
        response = await handle_exceptions(request, call_next)
        return response or await call_next(request)


async def handle_exceptions(request: Request, call_next) -> JSONResponse:
    """Middleware to catch all the Exceptions and send API process time over response headers"""
    try:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers['X-Process-Time'] = f'{round(process_time*1000, 2)}'
    except RequestValidationError as error:
        logger.exception(error)
        response = JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=get_error_response('Request validation error', status.HTTP_422_UNPROCESSABLE_ENTITY, error.errors()))
    except ValueError as error:
        logger.exception(error)
        response = JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=get_error_response(str(error), status.HTTP_422_UNPROCESSABLE_ENTITY))
    except ExpiredSignatureError as error:
        logger.exception(error)
        response = JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=get_error_response(localization.EXCEPTION_TOKEN_INVALID, status.HTTP_401_UNAUTHORIZED))
    except JWTError as error:
        logger.exception(error)
        response = JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=get_error_response(str(error), status.HTTP_401_UNAUTHORIZED))
    except HTTPException as error:
        logger.exception(error)
        headers = {}
        with contextlib.suppress(AttributeError):
            headers = error.headers
        response = JSONResponse(status_code=error.status_code, content=get_error_response(str(error.detail), error.status_code), headers=headers)
    except Exception as error:  # pylint: disable=broad-except
        logger.exception(error)
        response = JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=get_error_response(str(error), status.HTTP_500_INTERNAL_SERVER_ERROR))
    return response


def get_error_response(message: str, code: int, detail: Any = None) -> dict[str, Any]:
    """Function to format error data

    Args:
        message (str): Error message
        code (int): Error code

    Returns:
        JSON: Returns error data in the desired format
    """
    error = {'status': 'FAIL', 'errorData': {'errorCode': code, 'message': message}}
    if detail:
        error['errorData'].update({'detail': detail})
    return jsonable_encoder(error)
