import contextlib
import sys
from typing import Any, Optional

from fastapi import HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.server.logger.custom_logger import logger


class CustomHTTPException(HTTPException):
    def __init__(self, status_code: int, detail: Any = None, identifier: str = None, headers: Optional[dict[str, Any]] = None) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.identifier = identifier

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f'{class_name}(status_code={self.status_code!r},identifier={self.identifier!r}, detail={self.detail!r})'


# pylint: disable=too-many-arguments
class PermissionCustomHTTPException(CustomHTTPException):
    def __init__(self, status_code: int, detail: Any = None, identifier: str = None, missing_permissions: list[str] = None, headers: Optional[dict[str, Any]] = None) -> None:
        super().__init__(status_code=status_code, detail=detail, identifier=identifier, headers=headers)
        self.identifier = identifier
        self.missing_permissions = missing_permissions

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f'{class_name}(status_code={self.status_code!r},identifier={self.identifier!r}, detail={self.detail!r}, missing_roles={self.missing_roles!r})'


async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Exception handler to handle Request validation errors
    Args:
        request (Request): Request object
        exc (RequestValidationError): Exception object

    Returns:
        JSONResponse: Returns error data in the desired format
    """
    if errors := exc.errors():
        # Use only the first error message
        first_error = errors[0]
        error_message = f"Request validation error at ({first_error['loc'][-1]}): {first_error['msg']}"
    else:
        # No error, default message
        error_message = 'Request validation error unknown'
    logger.error(error_message)
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=get_error_response(error_message, status.HTTP_422_UNPROCESSABLE_ENTITY, exc.errors()))


async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    """Exception handler to handle exception of type HTTPException
    Args:
        request (Request): Request object
        exc (HTTPException): Exception object

    Returns:
        JSONResponse: Returns error data in the desired format
    """
    _type, _, _trace = sys.exc_info()
    # workaround for HTTPException not being deserialized inside loguru using pickel
    logger.opt(exception=(_type, HTTPException(exc.status_code, exc.detail), None)).error(exc.detail)
    # logger.exception(exc)
    code = exc.status_code or status.HTTP_404_NOT_FOUND
    headers = {}
    with contextlib.suppress(AttributeError):
        headers = exc.headers
    return JSONResponse(status_code=code, content=get_error_response(exc.detail, code), headers=headers)


async def http_custom_exception_handler(_request: Request, exc: CustomHTTPException) -> JSONResponse:
    """Exception handler to handle exception of type HTTPException
    Args:
        request (Request): Request object
        exc (HTTPException): Exception object

    Returns:
        JSONResponse: Returns error data in the desired format
    """
    _type, _, _trace = sys.exc_info()
    # workaround for HTTPException not being deserialized inside loguru using pickel
    logger.opt(exception=(_type, HTTPException(exc.status_code, exc.detail), None)).error(exc.detail)
    # logger.exception(exc)
    code = exc.status_code or status.HTTP_404_NOT_FOUND
    headers = {}
    identifier = exc.identifier
    with contextlib.suppress(AttributeError):
        headers = exc.headers
    return JSONResponse(status_code=code, content=get_custom_error_response(exc.detail, code, identifier=identifier), headers=headers)


async def http_permission_exception_handler(_request: Request, exc: PermissionCustomHTTPException) -> JSONResponse:
    """Exception handler to handle exception of type HTTPException
    Args:
        request (Request): Request object
        exc (HTTPException): Exception object

    Returns:
        JSONResponse: Returns error data in the desired format
    """
    _type, _, _trace = sys.exc_info()
    # workaround for PermissionException not being deserialized inside loguru using pickel
    logger.opt(exception=(_type, HTTPException(exc.status_code, exc.detail), None)).error(exc.detail)
    # logger.exception(exc)
    code = exc.status_code or status.HTTP_404_NOT_FOUND
    headers = {}
    identifier = exc.identifier
    missing_permissions = exc.missing_permissions
    with contextlib.suppress(AttributeError):
        headers = exc.headers
    return JSONResponse(status_code=code, content=get_permission_error_response(exc.detail, code, identifier=identifier, missing_permissions=missing_permissions), headers=headers)


def get_custom_error_response(message: str, code: int, detail: Any = None, identifier: Any = None) -> dict[str, Any]:
    """Function to format error data
    Args:
        message (str): Error message
        code (int): Error code
    Returns:
        JSON: Returns error data in the desired format
    """
    error = {'status': 'FAIL', 'errorData': {'errorCode': code, 'message': message, 'identifier': identifier}}
    if detail:
        error['errorData'].update({'detail': detail})
    return jsonable_encoder(error)


def get_permission_error_response(message: str, code: int, detail: Any = None, identifier: Any = None, missing_permissions: list[str] = None) -> dict[str, Any]:
    """Function to format error data
    Args:
        message (str): Error message
        code (int): Error code
    Returns:
        JSON: Returns error data in the desired format
    """
    error = {'status': 'FAIL', 'errorData': {'errorCode': code, 'message': message, 'identifier': identifier, 'missingPermissions': missing_permissions}}
    if detail:
        error['errorData'].update({'detail': detail})
    return jsonable_encoder(error)


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
