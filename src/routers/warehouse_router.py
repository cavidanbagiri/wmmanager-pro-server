
from typing import Annotated

from src.core.types.numeric import UnsignedInt

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.setup import get_db
from src.auth.token_handler import TokenHandler
from src.repositories.warehouse_repository import WarehouseUpdateRepository, WarehouseGetByIdRepository

from src.dependencies.roles_authorization import project_role_based_authorization
from src.repositories.warehouse_repository import (WarehouseCreateRepository,
                                                   WarehouseSelectedByIDSRepository,
                                                   WarehouseFetchRepository)
from src.schemas.user_schemas import UserTokenSchema

from src.schemas.warehouse_schema import WarehouseListCreateSchema, WarehouseListSelectByIDS, \
    WarehouseListSelectByIDSResponse, WarehouseUpdateSchema

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




@router.get('/fetch-warehouse_list',
             status_code=200,
             response_model=list[WarehouseListSelectByIDSResponse])
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



@router.post('/fetch-selected-ids', status_code=200,
             response_model=list[WarehouseListSelectByIDSResponse])
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



@router.get('/{item_id}',
            dependencies=[Depends(TokenHandler.verify_access_token)],
            status_code=status.HTTP_200_OK,
            response_model=WarehouseListSelectByIDSResponse
            )
async def get_by_id(item_id: UnsignedInt,
                              db: Annotated[AsyncSession,  Depends(get_db)]):
    repository = WarehouseGetByIdRepository(db, item_id)
    try:
        data = await repository.get_by_id()
        return data
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        logger.error(f"Fetch Selected IDS error {ex}")
        raise HTTPException(status_code=500, detail="Internal Server Error")




















