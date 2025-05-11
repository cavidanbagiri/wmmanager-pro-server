from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
# from fastapi.dependencies import
from fastapi.responses import Response

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.setup import get_db

from src.repositories.user_repository import UserLoginRepository
from src.schemas.user_schemas import UserLoginSchema


from src.logging_config import setup_logger
logger = setup_logger(__name__, "user.log")

router = APIRouter()

# Tested
@router.post('/login', status_code=201)
async def login(response: Response, login_data: UserLoginSchema, db_session: Annotated[AsyncSession,  Depends(get_db)]):

    repository = UserLoginRepository(db_session)

    try:
        data = await repository.login(login_data)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"

        response.set_cookie('refresh_token', data.get('refresh_token'),
                            httponly=True,
                            secure=True,
                            samesite="none"
                            )
        return {
            'user': data.get('user'),
            'access_token': data.get('access_token')
        }

    except HTTPException as ex:
        raise ex
    except Exception as ex:  # Catch all other exceptions
        logger.exception("Unexpected error login user: %s", ex)
        raise HTTPException(500, 'Internal server error')


