import secrets

from fastapi import status
from fastapi.param_functions import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.server.config import config
from app.server.handler.error_handler import CustomHTTPException
from app.server.static import error_identifier, localization

security_basic = HTTPBasic()


def authorize_docs(credentials: HTTPBasicCredentials = Depends(security_basic)):
    """
    Authorize access to Swagger/Redoc documentation.
    Uses HTTP Basic Auth with credentials from config.

    Args:
        credentials (HTTPBasicCredentials): Basic auth credentials.

    Returns:
        str: The authenticated username.
    """
    correct_username = secrets.compare_digest(credentials.username, config.DOC_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, config.DOC_PASSWORD)

    if not (correct_username and correct_password):
        raise CustomHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=localization.EXCEPTION_USERNAME_PASSWORD_INVALID,
            headers={'WWW-Authenticate': 'Basic'},
            identifier=error_identifier.INVALID_CREDENTIALS,
        )
    return credentials.username