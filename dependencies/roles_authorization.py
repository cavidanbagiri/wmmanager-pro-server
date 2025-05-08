
from fastapi import Depends, HTTPException
from fastapi.requests import Request

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.token_handler import TokenHandler
from src.database.setup import get_db
from src.models import UserModel

from enum import Enum

class CommonRoleAuthentication(str, Enum):

    MANAGER = 'MANAGER'
    HEAD = 'HEAD'
    STAFF = 'STAFF'
    OPERATOR = 'OPERATOR'

class ProjectRoleAuthentication(str, Enum):

    MANAGER = 'MANAGER'
    HEAD = 'HEAD'
    STAFF = 'STAFF'
    OPERATOR = 'OPERATOR'


async def project_role_based_authorization(
        request: Request,
        db: AsyncSession = Depends(get_db),
        payload: dict = Depends(TokenHandler.verify_access_token)) -> int:

    data = await request.json()
    project_id = data.get('project_id')
    try:
        user_id = int(payload.get('sub'))
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    f_user = await db.scalar(
        select(UserModel)
        .where(UserModel.id == user_id)
        .options(selectinload(UserModel.role)))

    if not f_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Admin pass
    if f_user.is_admin:
        return f_user.id

    if not f_user.role or not f_user.role.name:
        raise HTTPException(status_code=403, detail="No role assigned")

    if f_user.role_id:
        role_name: str = str(f_user.role.name).upper()
        if role_name in ProjectRoleAuthentication:
            # if role_name == ProjectRoleAuthentication.OPERATOR:
            #     raise HTTPException(status_code=403, detail='Insufficient permissions')
            if (role_name == ProjectRoleAuthentication.HEAD or
                    role_name == ProjectRoleAuthentication.STAFF or
                    role_name == ProjectRoleAuthentication.OPERATOR):
                if f_user.project_id == project_id:
                    return f_user.id
                else:
                    raise HTTPException(status_code=403, detail='Insufficient permissions')
            elif role_name == ProjectRoleAuthentication.MANAGER:
                return f_user.id
            else:
                raise HTTPException(status_code=403, detail='Insufficient permissions')

    raise HTTPException(status_code=403, detail='Insufficient permissions')


async def common_role_based_authorization(db: AsyncSession = Depends(get_db),
                             payload: dict = Depends(TokenHandler.verify_access_token)) -> int:
    try:
        user_id = int(payload.get('sub'))
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    f_user = await db.scalar(
        select(UserModel)
        .where(UserModel.id == user_id)
        .options(selectinload(UserModel.role)))

    if not f_user:
        raise HTTPException(status_code=404, detail="User not found")
    if f_user.is_admin:
        return f_user.id
    if not f_user.role or not f_user.role.name:
        raise HTTPException(status_code=403, detail="No role assigned")
    if f_user.role_id:
        if str(f_user.role.name).upper() in CommonRoleAuthentication:
            return f_user.id

    raise HTTPException(status_code=403, detail='Insufficient permissions')

