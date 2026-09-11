from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import ORJSONResponse
from starlette.exceptions import HTTPException

from app.server.config import config
from app.server.handler.error_handler import (
    CustomHTTPException,
    PermissionCustomHTTPException,
    http_custom_exception_handler,
    http_exception_handler,
    http_permission_exception_handler,
    validation_exception_handler,
)
from app.server.logger.custom_logger import logger
from app.server.middlewares.exceptions import ExceptionHandlerMiddleware
from app.server.middlewares.request_gzip import GzipRoute
from app.server.utils import date_utils
from app.server.utils.token_util import authorize_docs
from app.server.routes.ingestion import router as INGESTION
from app.server.routes.query import router as QUERY

# NOTE: Routes will be imported and registered here as they are built
# from app.server.routes.ingestion import router as INGESTION
# from app.server.routes.query import router as QUERY

app = FastAPI(
    docs_url=None,
    redoc_url=None,
    root_path=config.PROXY_API_PREFIX,
    title=config.APP_TITLE,
    version='1.0.0',
    swagger_ui_parameters={'defaultModelsExpandDepth': -1},
    default_response_class=ORJSONResponse,
)

GZIP_REQUEST_ROUTE = APIRouter(route_class=GzipRoute)

# add routes
app.include_router(GZIP_REQUEST_ROUTE)
# NOTE: Routes will be added here as they are built
app.include_router(INGESTION, tags=['INGESTION'], prefix='/api/v1')
app.include_router(QUERY, tags=['QUERY'], prefix='/api/v1')

# add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(CustomHTTPException, http_custom_exception_handler)
app.add_exception_handler(PermissionCustomHTTPException, http_permission_exception_handler)

# add middlewares
app.add_middleware(ExceptionHandlerMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/docs', include_in_schema=False)
async def get_documentation(request: Request, _username: str = Depends(authorize_docs)):
    return get_swagger_ui_html(
        openapi_url=f"{request.scope.get('root_path')}{app.openapi_url}",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        title=app.title,
        swagger_ui_parameters=app.swagger_ui_parameters,
    )


@app.get('/redoc', include_in_schema=False)
async def get_redoc_documentation(request: Request, _username: str = Depends(authorize_docs)):
    return get_redoc_html(
        openapi_url=f"{request.scope.get('root_path')}{app.openapi_url}",
        title=app.title,
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get('/openapi.json', include_in_schema=False)
async def openapi(_username: str = Depends(authorize_docs)):
    return get_openapi(
        title=app.title,
        version=app.version,
        tags=app.openapi_tags,
        routes=app.routes,
    )


@app.on_event('startup')
async def startup_event():
    logger.debug(f'App startup: {str(date_utils.get_current_date_time())}')
    # Preload embedding model at startup
    from app.server.embeddings.embedder import get_embedding_model
    get_embedding_model()


@app.on_event('shutdown')
def shutdown_event():
    logger.debug(f'App shutdown: {str(date_utils.get_current_date_time())}')


@app.get('/', tags=['Root'], include_in_schema=False)
async def read_root():
    return {'message': app.title}