from typing import Any

import app.server.database.core_data as core_service
from app.server.handler.error_handler import CustomHTTPException
from app.server.models.app_version import SemanticVersion, VersionModel
from app.server.static import error_identifier, localization, projections
from app.server.static.collections import Collections
from app.server.static.enums import VersionPlatform


def is_newer_version(new_version: SemanticVersion, current_version: SemanticVersion):
    """
    Checks if a given version is newer than another version.

    Args:
        new_version (SemanticVersion): The new version to compare.
        current_version (SemanticVersion): The current version to compare.

    Returns:
        bool: True if the new version is newer, False otherwise.
    """
    is_new = False
    # Compare major versions
    if new_version.major > current_version.major:
        is_new = True
    elif new_version.major == current_version.major:
        # Compare minor versions if major versions are equal
        if new_version.minor > current_version.minor:
            is_new = True
        elif new_version.minor == current_version.minor:
            # Compare patch versions if minor versions are equal
            is_new = new_version.patch > current_version.patch
    return is_new


def sem_ver_to_string(sem_ver: dict[str, Any]) -> str:
    """
    Converts a semantic version dictionary to a string representation.

    Args:
        sem_ver: A dictionary representing a semantic version with 'major', 'minor', and 'patch' keys.

    Returns:
        A string representation of the semantic version in the format 'major.minor.patch'.
    """
    return f"{sem_ver['major']}.{sem_ver['minor']}.{sem_ver['patch']}"


async def create_version(version_info: VersionModel):
    """
    Create a new version with the given version information.

    Args:
        version_info (VersionModel): The version information.

    Returns:
        dict: The created version.

    Raises:
        HTTPException: If the new version is not greater than the existing versions.
    """
    version_dict = version_info.dict()
    new_version = version_info.sem_ver

    # Get the latest version document for the given platform
    latest_version_doc = await get_latest_version(version_info.platform)

    # Check if there is a latest version
    if latest_version_doc:
        latest_version = SemanticVersion(**latest_version_doc['sem_ver'])

        # Check if the new version is greater than the latest version
        if not is_newer_version(new_version, latest_version):
            raise CustomHTTPException(status_code=400, detail=localization.EXCEPTION_APP_VERSION_LESSER, identifier=error_identifier.LESSER_APP_VERSION)

    # Create the version document in the database
    await core_service.create_one(Collections.APP_VERSIONS, version_dict, options=projections.PLATFORM_VERSION_PROJECTION)

    return {'message': 'Version created successfully.'}


async def get_latest_version(platform: VersionPlatform):
    """
    Get the latest version for a given platform.

    Args:
        platform (VersionPlatform): The platform for which to get the latest version.

    Returns:
        dict: The latest version for the given platform, or None if no version is found.
    """
    aggregate_query: list[dict[str, Any]] = [
        {'$match': {'platform': platform}},
        {'$addFields': {'version': {'$concat': [{'$toString': '$sem_ver.major'}, '.', {'$toString': '$sem_ver.minor'}, '.', {'$toString': '$sem_ver.patch'}]}}},
        {'$sort': {'sem_ver.major': -1, 'sem_ver.minor': -1, 'sem_ver.patch': -1}},
        {'$project': projections.PLATFORM_VERSION_PROJECTION},
    ]
    latest_versions = await core_service.query_read(Collections.APP_VERSIONS, aggregate=aggregate_query, page_size=1)
    return latest_versions[0] if latest_versions else {}


async def check_version(platform: VersionPlatform, version: str):
    # Convert the version string from the request to major, minor, patch
    try:
        major, minor, patch = map(int, version.split('.'))
    except ValueError as error:
        raise CustomHTTPException(status_code=400, detail=localization.EXCEPTION_APP_VERSION_INVALID, identifier=error_identifier.INVALID_APP_VERSION) from error

    # Aggregate query to get the latest version
    aggregate_query: list[dict[str, Any]] = [
        {
            '$match': {
                'platform': platform,
                '$or': [
                    {'sem_ver.major': {'$gt': major}},
                    {'$and': [{'sem_ver.major': major}, {'sem_ver.minor': {'$gt': minor}}]},
                    {'$and': [{'sem_ver.major': major}, {'sem_ver.minor': minor}, {'sem_ver.patch': {'$gt': patch}}]},
                ],
            }
        },
        {'$addFields': {'version': {'$concat': [{'$toString': '$sem_ver.major'}, '.', {'$toString': '$sem_ver.minor'}, '.', {'$toString': '$sem_ver.patch'}]}}},
        {'$sort': {'sem_ver.major': -1, 'sem_ver.minor': -1, 'sem_ver.patch': -1}},
        {'$group': {'_id': None, 'requires_logout': {'$max': '$requires_logout'}, 'latest_version': {'$first': '$version'}}},
        {'$project': projections.PLATFORM_VERSION_PROJECTION},
    ]
    result = await core_service.query_read(Collections.APP_VERSIONS, aggregate=aggregate_query, page_size=1)

    logout_required = result[0]['requires_logout'] if result else False
    latest_version = result[0]['latest_version'] if result else version

    return {'requires_logout': logout_required, 'latest_version': latest_version}
