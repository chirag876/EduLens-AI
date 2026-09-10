import uuid
from typing import Any

from fastapi import status

from app.server.database import core_data as core_service
from app.server.handler.error_handler import CustomHTTPException
from app.server.models.category import CategoryUpdate, CreateCategoryRequest, RoleUsersRequest
from app.server.static import error_identifier, localization
from app.server.static.collections import Collections


async def create_category(params: CreateCategoryRequest, user: dict[str, Any]) -> dict[str, Any]:
    org_id = user.get('org_id')
    if not org_id:
        raise CustomHTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Organization ID missing', identifier='ORG_ID_MISSING')

    # Duplicate check
    existing = await core_service.read_one(collection_name=Collections.TICKET_CATEGORIES, data_filter={'name': {'$regex': f'^{params.name}$', '$options': 'i'}, 'org_id': org_id, 'is_deleted': False})
    if existing:
        raise CustomHTTPException(status_code=status.HTTP_409_CONFLICT, detail='Category name already exists', identifier=error_identifier.CATEGORY_NAME_EXISTS)

    category_id = str(uuid.uuid4())

    category_doc = {**params.dict(exclude_unset=True), 'category_id': category_id, 'org_id': org_id, 'is_deleted': False}

    sla_doc = {'category_id': category_id, 'org_id': org_id, 'label': params.name, 'windows': {'first_response_hrs': 2, 'critical_hrs': 4, 'high_hrs': 8, 'medium_hrs': 48, 'low_hrs': 96}}

    # TRANSACTION USING YOUR HELPER
    session = await core_service.get_session()

    try:
        async with session.start_transaction():
            # Create Category
            await core_service.create_one(collection_name=Collections.TICKET_CATEGORIES, data=category_doc, session=session)

            # Create SLA (Upsert safe)
            await core_service.update_one(collection_name=Collections.SLA_CONFIGS, data_filter={'category_id': category_id}, update={'$setOnInsert': sla_doc}, upsert=True, session=session)

    except Exception as e:
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Failed to create category with SLA and escalation matrix: {str(e)}', identifier='CATEGORY_SLA_ESCALATION_TRANSACTION_FAILED'
        )

    finally:
        await session.end_session()
    return {'message': (f'Category created successfully with SLA configuration ' f'and {params.escalation_levels} escalation levels'), 'category_id': category_id}


async def get_categories(user: dict[str, Any]) -> list[dict[str, Any]]:
    org_id = user.get('org_id')

    data_filter = {'org_id': org_id, 'is_deleted': False}

    projection = {'category_id': 1, 'name': 1, 'description': 1, '_id': 0, 'escalation_levels': 1, 'role_responsible': 1}

    categories = await core_service.read_many(collection_name=Collections.TICKET_CATEGORIES, data_filter=data_filter, options=projection, sort={'name': 1})

    return categories


async def get_category(category_id: str, user: dict[str, Any]) -> dict[str, Any]:
    org_id = user.get('org_id')

    data_filter = {'category_id': category_id, 'org_id': org_id, 'is_deleted': False}

    projection = {'category_id': 1, 'name': 1, 'description': 1, '_id': 0, 'escalation_levels': 1, 'role_responsible': 1}

    category = await core_service.read_one(collection_name=Collections.TICKET_CATEGORIES, data_filter=data_filter, options=projection)

    if not category:
        raise CustomHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=localization.EXCEPTION_CATEGORY_NOT_FOUND, identifier=error_identifier.CATEGORY_NOT_FOUND)

    return category


async def update_category(params: CategoryUpdate, user: dict[str, Any]) -> dict[str, Any]:  # noqa: C901
    org_id = user.get('org_id')

    # Check existing category
    existing = await core_service.read_one(collection_name=Collections.TICKET_CATEGORIES, data_filter={'category_id': params.category_id, 'org_id': org_id, 'is_deleted': False})

    if not existing:
        raise CustomHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=localization.EXCEPTION_CATEGORY_NOT_FOUND, identifier=error_identifier.CATEGORY_NOT_FOUND)

    # Validate escalation update
    if params.escalation_levels is not None or params.role_responsible is not None:
        if params.escalation_levels is None or params.role_responsible is None:
            raise CustomHTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Both escalation_levels and role_responsible are required together', identifier='INVALID_ESCALATION_UPDATE')

        if params.escalation_levels != len(params.role_responsible):
            raise CustomHTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=(f'All {params.escalation_levels} escalation levels ' f'must be configured'), identifier='ESCALATION_LEVEL_MISMATCH'
            )

        expected_levels = set(range(1, params.escalation_levels + 1))

        provided_levels = {item.level for item in params.role_responsible}

        if expected_levels != provided_levels:
            raise CustomHTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=(f'Escalation levels must be sequential from 1 to ' f'{params.escalation_levels}'), identifier='INVALID_ESCALATION_SEQUENCE'
            )

    update_data = params.dict(exclude_unset=True)

    # Remove category_id from update payload
    update_data.pop('category_id', None)

    if not update_data:
        raise CustomHTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='No fields to update', identifier='NO_UPDATE_FIELDS')

    # Duplicate category name check
    if 'name' in update_data:
        existing_name = await core_service.read_one(
            collection_name=Collections.TICKET_CATEGORIES,
            data_filter={'name': {'$regex': f'^{update_data["name"]}$', '$options': 'i'}, 'org_id': org_id, 'is_deleted': False, 'category_id': {'$ne': params.category_id}},
        )

        if existing_name:
            raise CustomHTTPException(status_code=status.HTTP_409_CONFLICT, detail='Category name already exists', identifier=error_identifier.CATEGORY_NAME_EXISTS)

    session = await core_service.get_session()

    try:
        async with session.start_transaction():
            # Update Category
            await core_service.update_one(collection_name=Collections.TICKET_CATEGORIES, data_filter={'category_id': params.category_id}, update={'$set': update_data}, session=session)

            # Sync SLA label if category name changes
            if 'name' in update_data:
                await core_service.update_one(
                    collection_name=Collections.SLA_CONFIGS, data_filter={'category_id': params.category_id}, update={'$set': {'label': update_data['name']}}, session=session, raise_error=False
                )

    finally:
        await session.end_session()

    # Dynamic response message
    message = 'Category updated successfully'

    if 'name' in update_data:
        message = 'Category and related SLA label updated successfully'

    if 'escalation_levels' in update_data or 'role_responsible' in update_data:
        message += ' with escalation configuration updates'

    return {'message': message}


async def delete_category(category_id: str, user: dict[str, Any]) -> dict[str, Any]:
    org_id = user.get('org_id')

    # Fetch to validate
    category = await core_service.read_one(collection_name=Collections.TICKET_CATEGORIES, data_filter={'category_id': category_id, 'org_id': org_id, 'is_deleted': False})
    if not category:
        raise CustomHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=localization.EXCEPTION_CATEGORY_NOT_FOUND, identifier=error_identifier.CATEGORY_NOT_FOUND)

    # Soft delete
    await core_service.update_one(collection_name=Collections.TICKET_CATEGORIES, data_filter={'category_id': category_id, 'org_id': org_id}, update={'$set': {'is_deleted': True}})
    return {'message': 'Category deleted successfully'}


async def get_roles(user: dict[str, Any]) -> list[dict[str, Any]]:
    org_id = user.get('org_id')

    data_filter = {'org_id': org_id, 'is_deleted': False}

    projection = {'_id': 1, 'name': 1, 'identifier': 1, 'system_role': 1}

    roles = await core_service.read_many(collection_name=Collections.ROLES, data_filter=data_filter, options=projection, sort={'name': 1})

    return roles


async def get_users_by_roles(params: RoleUsersRequest, user: dict[str, Any]) -> list[dict[str, Any]]:
    org_id = user.get('org_id')

    # If no role_ids provided, return all active users
    if not params.role_ids:
        aggregate = [
            {'$match': {'org_id': org_id, 'is_deleted': False, 'account_status': 'ACTIVE'}},
            {'$project': {'_id': 0, 'user_id': '$_id', 'full_name': {'$trim': {'input': {'$concat': [{'$ifNull': ['$first_name', '']}, ' ', {'$ifNull': ['$last_name', '']}]}}}}},
            {'$sort': {'full_name': 1}},
        ]

        return await core_service.query_read_all(collection_name=Collections.USERS, aggregate=aggregate)

    # Existing role-based flow
    aggregate = [
        {'$match': {'org_id': org_id, 'is_deleted': False, 'user_type': 'Staff', 'roles': {'$in': params.role_ids}}},
        {'$lookup': {'from': Collections.ROLES, 'localField': 'roles', 'foreignField': '_id', 'as': 'role_details'}},
        {
            '$project': {
                '_id': 0,
                'user_id': '$_id',
                'full_name': {'$trim': {'input': {'$concat': [{'$ifNull': ['$first_name', '']}, ' ', {'$ifNull': ['$last_name', '']}]}}},
                'roles': {
                    '$map': {
                        'input': {'$filter': {'input': '$role_details', 'as': 'role', 'cond': {'$in': ['$$role._id', params.role_ids]}}},
                        'as': 'role',
                        'in': {'role_id': '$$role._id', 'name': '$$role.name', 'identifier': '$$role.identifier', 'system_role': '$$role.system_role'},
                    }
                },
            }
        },
        {'$sort': {'full_name': 1}},
    ]

    users = await core_service.query_read_all(collection_name=Collections.USERS, aggregate=aggregate)

    return users
