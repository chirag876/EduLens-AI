from typing import Any

from fastapi import APIRouter

import app.server.services.app_version as version_service
from app.server.models.app_version import VersionModel
from app.server.static.enums import VersionPlatform

router = APIRouter()


@router.post('/app-version/create', summary='Creates new platform version')
async def create_version(params: VersionModel) -> dict[str, Any]:
    data = await version_service.create_version(params)
    return {'data': data, 'status': 'SUCCESS'}


@router.get('/app-version/latest', summary='Gets latest platform version')
async def get_latest_version(platform: VersionPlatform) -> dict[str, Any]:
    data = await version_service.get_latest_version(platform)
    return {'data': data, 'status': 'SUCCESS'}


@router.get('/app-version/check', summary='Checks platform version')
async def check_version(platform: VersionPlatform, version: str) -> dict[str, Any]:
    data = await version_service.check_version(platform, version)
    return {'data': data, 'status': 'SUCCESS'}
