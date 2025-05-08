from typing import Any, Type, Coroutine

from fastapi import Depends, status
from fastapi.exceptions import HTTPException

from src.auth.token_handler import TokenHandler
from src.database.setup import get_db
from src.models.user_models import UserModel

from sqlalchemy.ext.asyncio import AsyncSession

from src.logging_config import setup_logger
logger = setup_logger(__name__, "admin.log")

async def verify_admin(db: AsyncSession = Depends(get_db),
                       payload: dict = Depends(TokenHandler.verify_access_token))-> Type[UserModel] | None:
    try:
        user_id: int = int(payload.get('sub'))
        user_data = await db.get(UserModel, user_id)
        if user_data and user_data.is_admin:
            return user_data
        raise HTTPException(status_code=403)
    except Exception as ex:
        logger.error(f'User admin verification error {ex}')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'User admin authentication error {ex}')
