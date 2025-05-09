
from typing import Any, Coroutine, Union

from fastapi import HTTPException

from sqlalchemy import insert, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.user_schemas import UserLoginSchema

from src.models import UserModel
from src.models.user_models import TokenModel

from src.utils.hash_password import PasswordHash

from src.auth.token_handler import TokenHandler

from src.logging_config import setup_logger
logger = setup_logger(__name__, "user.log")


class RefreshTokenRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def manage_refresh_token(self, user_id:int, refresh_token) -> None:

        try:
            token = await self.find_refresh_token(user_id)
            if token:
                await self.delete_refresh_token(user_id)
            await self.save_refresh_token(user_id, refresh_token)
        except Exception as ex:
            logger.error(f'For {user_id}, manage refresh token error {ex}')
            raise HTTPException(status_code=404, detail=f'Manage refresh token error ')

    async def find_refresh_token(self, user_id: int) -> Union[TokenModel, None]:
        try:
            token = await self.db.execute(select(TokenModel).where(TokenModel.user_id == user_id))
            data = token.scalar()
            if data:
                return data
            else:
                return None
        except Exception as ex:
            logger.error(f'For {user_id}, refresh token not found {ex}')
            raise HTTPException(status_code=404, detail=f"Refresh token not found")

    async def delete_refresh_token(self, user_id: int) -> None:
        try:
            await self.db.execute(delete(TokenModel).where(TokenModel.user_id == user_id))
        except Exception as ex:
            logger.error(f'For {user_id},  not found in token model {ex}')
            raise HTTPException(status_code=404, detail=f'User id not found ')

    async def save_refresh_token(self,user_id: int, refresh_token: str) -> Coroutine[Any, Any, None]:
        try:
            if refresh_token:
                data = await self.db.execute(insert(TokenModel).values(
                    user_id = user_id,
                    tokens = refresh_token
                ))
                await self.db.commit()
                data = self.db.refresh(data)
                return data
            else:
                logger.error(f'For {user_id}, Refresh token can\'t find ')
                raise ValueError("Refresh token can't find")
        except Exception as ex:
            logger.error(f'For {user_id}, Refresh token can\'t save ')
            raise HTTPException(status_code=404, detail=f'Refresh Token can\'t save {str(ex)}')


class CheckUserAvailable:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.h_password = PasswordHash()

    async def check_user_exists(self, login_data: UserLoginSchema) -> UserModel:
        data = await self.db.execute(select(UserModel).where(UserModel.email==login_data.email))
        user = data.scalar()

        if user:
            logger.info(f'{login_data.email} find in database')
            pass_verify = self.h_password.verify(user.password, login_data.password)
            if pass_verify:
                return user
            else:
                logger.error(f'{login_data.email} password is wrong')
                raise HTTPException(status_code=404, detail="Password is wrong")
        else:
            logger.error(f'{login_data.email} email is wrong')
            raise HTTPException(status_code=404, detail="User not found")


class UserLoginRepository:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.check_user_available = CheckUserAvailable(self.db)
        self.refresh_token_repo = RefreshTokenRepository(self.db)


    async def login(self, login_data: UserLoginSchema)-> dict:
        try:
            logger.info(f'{login_data.email} try to login')
            user = await self.check_user_available.check_user_exists(login_data)

            token_data = {
                'sub': str(user.id),
                'email': user.email,
                'project_id': user.project_id
            }

            access_token = TokenHandler.generate_access_token(token_data)
            refresh_token = TokenHandler.generate_refresh_token(token_data)

            await self.refresh_token_repo.manage_refresh_token(user.id, refresh_token)

            return self.return_data(user, access_token, refresh_token)

        except HTTPException as ex:
            raise

    @staticmethod
    def return_data(user: UserModel, access_token: str, refresh_token: str):
        if user.middle_name:
            username = user.first_name.capitalize() + ' ' + user.middle_name.capitalize() + ' ' + user.last_name.capitalize()
        else:
            username = user.first_name.capitalize() + ' ' + user.last_name.capitalize()

        return {
            'user': {
                'sub': str(user.id),
                'email': user.email,
                'username': username,
            },
            'access_token': access_token,
            'refresh_token': refresh_token
        }





