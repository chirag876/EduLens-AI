from typing import Any

from fastapi import APIRouter, Depends

from app.server.models.category import CategoryUpdate, CreateCategoryRequest, RoleUsersRequest
from app.server.services import category_service
from app.server.utils.token_util import JWTAuthPermission

router = APIRouter()


@router.post('/categories', summary='Create category')
async def create_category(params: CreateCategoryRequest, user=Depends(JWTAuthPermission(['erp.support.category:create']))) -> dict[str, Any]:
    data = await category_service.create_category(params, user)
    return {'data': data, 'status': 'SUCCESS'}


@router.get('/categories/list', summary='Get all categories')
async def get_categories(user=Depends(JWTAuthPermission(['erp.support.category:list', 'erp.support.category:view']))) -> dict[str, Any]:
    data = await category_service.get_categories(user)
    return {'data': data, 'status': 'SUCCESS'}


@router.get('/get/categories/', summary='Get category by ID')
async def get_category(category_id: str, user=Depends(JWTAuthPermission(['erp.support.category:view']))) -> dict[str, Any]:
    data = await category_service.get_category(category_id, user)
    return {'data': data, 'status': 'SUCCESS'}


@router.put('/categories/', summary='Update category')
async def update_category(params: CategoryUpdate, user=Depends(JWTAuthPermission(['erp.support.category:edit']))) -> dict[str, Any]:
    data = await category_service.update_category(params, user)
    return {'data': data, 'status': 'SUCCESS'}


@router.post('/categories/', summary='Delete category')
async def delete_category(category_id: str, user=Depends(JWTAuthPermission(['erp.support.category:delete']))) -> dict[str, Any]:
    data = await category_service.delete_category(category_id, user)
    return {'data': data, 'status': 'SUCCESS'}


@router.get('/get/roles/')
async def get_roles(user=Depends(JWTAuthPermission(['erp.support.sla:view']))) -> dict[str, Any]:
    data = await category_service.get_roles(user)
    return {'data': data, 'status': 'SUCCESS'}


@router.post('/roles/users', summary='Get users by role ids')
async def get_users_by_roles(params: RoleUsersRequest, user=Depends(JWTAuthPermission(['erp.support.category:view']))) -> dict[str, Any]:
    data = await category_service.get_users_by_roles(params, user)

    return {'data': data, 'status': 'SUCCESS'}
