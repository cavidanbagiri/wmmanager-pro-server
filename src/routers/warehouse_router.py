
from typing import Annotated

from src.core.types.numeric import UnsignedInt

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.setup import get_db
from src.auth.token_handler import TokenHandler

from src.dependencies.roles_authorization import project_role_based_authorization
from src.repositories.warehouse_repository import (WarehouseCreateRepository,
                                                   WarehouseSelectedByIDSRepository,
                                                   WarehouseFetchRepository,
                                                   WarehouseUpdateRepository,
                                                   WarehouseGetByIdRepository,
                                                   WarehouseFilterRepository)

from src.schemas.user_schemas import UserTokenSchema

from src.schemas.warehouse_schema import WarehouseListCreateSchema, WarehouseListSelectByIDS, \
    WarehouseStandartFetchResponseSchema, WarehouseUpdateSchema, WarehouseFilterSchema

from src.logging_config import setup_logger
logger = setup_logger(__name__, 'warehouse.log')


router = APIRouter()


# Tested
@router.post('/create-warehouse_list',
             status_code=status.HTTP_201_CREATED,
             response_model=dict[str, str])
async def create_warehouse_list(warehouse_list: WarehouseListCreateSchema,
                                db: Annotated[AsyncSession,  Depends(get_db)],
                                user_id = Depends(project_role_based_authorization)):

    repository = WarehouseCreateRepository(db, warehouse_list, user_id)
    try:
        data = await repository.create_warehouse_list()
        return data
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        logger.error(f'Create Warehouse Error {ex}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal Server Error')


# Tested
@router.post('/update-warehouse_list',
            status_code=status.HTTP_202_ACCEPTED,
            response_model=dict[str, str])
async def update_warehouse_list(update_data: WarehouseUpdateSchema,
                                db: Annotated[AsyncSession,  Depends(get_db)],
                                user_id = Depends(project_role_based_authorization)):

    repository = WarehouseUpdateRepository(db, update_data, user_id)
    try:
        data = await repository.update_warehouse()
        return data
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        logger.error(f'Update Warehouse Error {ex}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Internal Server Error {ex}')



# Tested
@router.get('/fetch-warehouse_list',
            status_code=200,
            response_model=list[WarehouseStandartFetchResponseSchema])
async def fetch_warehouse(db: Annotated[AsyncSession,  Depends(get_db)],
                            payload:UserTokenSchema = Depends(TokenHandler.verify_access_token)):

    repository = WarehouseFetchRepository(db, payload)

    try:
        data = await repository.fetch_warehouse()
        return data
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        logger.error(f"Fetch Warehouse list error {ex}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# Tested
@router.post('/fetch-selected-ids', status_code=200,
             response_model=list[WarehouseStandartFetchResponseSchema])
async def fetch_selected_ids(request: WarehouseListSelectByIDS,
                             db: Annotated[AsyncSession,  Depends(get_db)],
                             payload:UserTokenSchema = Depends(TokenHandler.verify_access_token)):

    repository = WarehouseSelectedByIDSRepository(db, payload)
    try:
        data = await repository.fetch_selected_ids(request.ids)
        return data
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        logger.error(f"Fetch Selected IDS error {ex}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# Tested
@router.get('/{item_id}',
            status_code=status.HTTP_200_OK,
            response_model=WarehouseStandartFetchResponseSchema
            )
async def get_by_id(item_id: UnsignedInt,
                    user_payload: Annotated[UserTokenSchema, Depends(TokenHandler.verify_access_token)],
                    db: Annotated[AsyncSession,  Depends(get_db)]):
    repository = WarehouseGetByIdRepository(db, item_id, user_payload)
    try:
        data = await repository.get_by_id()
        return data
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        logger.error(f"Fetch Selected IDS error {ex}")
        raise HTTPException(status_code=500, detail="Internal Server Error")




@router.post('/filter', status_code=status.HTTP_200_OK,
             response_model=list[WarehouseStandartFetchResponseSchema])
async def filter(filter_data: WarehouseFilterSchema,
                 user_payload: Annotated[UserTokenSchema, Depends(TokenHandler.verify_access_token)],
                 db: Annotated[AsyncSession,  Depends(get_db)]):

    try:
        repository = WarehouseFilterRepository(db, filter_data, user_payload)
        data = await repository.filter()
        return data
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        logger.error(f"Fetch Selected IDS error {ex}")
        raise HTTPException(status_code=500, detail="Internal Server Error")













