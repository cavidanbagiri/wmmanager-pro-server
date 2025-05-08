

from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.token_handler import TokenHandler
from src.database.setup import get_db
from src.dependencies.roles_authorization import project_role_based_authorization
from src.repositories.area_repository import AreaAddRepository, AreaFetchRepository
from src.schemas.area_schemas import AreaListAddSchema
from src.schemas.user_schemas import UserTokenSchema

router = APIRouter()

from src.logging_config import setup_logger
logger = setup_logger(__name__, "area.log")


@router.post('/add_area', status_code=201)
async def add_area(area_data: AreaListAddSchema,
                   db: AsyncSession = Depends(get_db),
                   user_id: int = Depends(project_role_based_authorization)):
    repository = AreaAddRepository(db, area_data, user_id)

    try:
        data = await repository.add_area()
        return data
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        logger.error(f"Add area error : {ex}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")



@router.get('/fetch_area', status_code=200)
async def fetch_area(db: AsyncSession = Depends(get_db),
                     payload: UserTokenSchema = Depends(TokenHandler.verify_access_token)):
    repository = AreaFetchRepository(db, payload)

    try:
        data = await repository.fetch()
        return data
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        logger.error(f"Fetch area internal server error : {ex}")
        return HTTPException(status_code=500, detail="Internal server error")