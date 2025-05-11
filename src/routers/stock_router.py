from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.types.numeric import UnsignedInt
from src.repositories.stock_repository import StockReturnToWarehouseRepository, StockGetByIdRepository
from src.schemas.stock_schema import StockReturnToWarehouseSchema
from src.auth.token_handler import TokenHandler
from src.database.setup import get_db
from src.dependencies.roles_authorization import project_role_based_authorization
from src.repositories.stock_repository import StockAddRepository, StockFetchRepository, StockFetchSelectedByIDSRepository
from src.schemas.stock_schema import StockListRequest, StockListResponse, StockListSelectByIDS

from src.logging_config import setup_logger
from src.schemas.user_schemas import UserTokenSchema

logger = setup_logger(__name__, 'stock.log')

router = APIRouter()

# Tested
@router.post('/add_stock_data_list', status_code=201, response_model=dict[str, str])
async def add_stock_list(request: StockListRequest,
                         db: Annotated[AsyncSession,  Depends(get_db)],
                         user_id = Depends(project_role_based_authorization)):

    repository = StockAddRepository(db, request, user_id)

    try:
        data = await repository.add_stock_list()
        return data
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        logger.error(f'Create Warehouse Error {ex}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal Server Error')

# Tested
@router.post('/return_to_warehouse',
             status_code=201,
             response_model=dict[str, str])
async def return_to_warehouse(return_data: StockReturnToWarehouseSchema,
                              db: Annotated[AsyncSession,  Depends(get_db)],
                              user_id: int = Depends(project_role_based_authorization)):

    repository = StockReturnToWarehouseRepository(db, return_data, user_id)

    try:
        data = await repository.return_to_warehouse()
        return data
    except HTTPException as ex:
        logger.error(f'Return Warehouse Error {ex}')
        raise ex
    except Exception as ex:
        logger.error(f'Return Warehouse Error {ex}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal Server Error')


@router.get('/fetch-stock_list', status_code=200,
            response_model=List[StockListResponse])
async def fetch_stock_list(db: Annotated[AsyncSession,  Depends(get_db)],
                           payload: UserTokenSchema = Depends(TokenHandler.verify_access_token)):

    repository = StockFetchRepository(db,payload)

    try:
        data = await repository.fetch_stock_list()
        return data
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        logger.error(f"Fetch Stock list error {ex}")
        raise HTTPException(status_code=500, detail="Internal Server Error")



@router.post('/fetch-selected-ids', status_code=200,)
async def fetch_selected_ids(request: StockListSelectByIDS,
                             db: Annotated[AsyncSession,  Depends(get_db)],
                             payload:UserTokenSchema = Depends(TokenHandler.verify_access_token)
                             ):

    repository = StockFetchSelectedByIDSRepository(db, payload, request.ids)
    try:
        data = await repository.fetch_selected_ids()
        return data
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        logger.error(f"Fetch Selected IDS error {ex}")
        raise HTTPException(status_code=500, detail="Internal Server Error")



@router.get('/{item_id}',
            dependencies=[Depends(TokenHandler.verify_access_token)],
            status_code=status.HTTP_200_OK,
            response_model=StockListResponse
            )
async def get_by_id(item_id: UnsignedInt,
                              db: Annotated[AsyncSession,  Depends(get_db)]):
    repository = StockGetByIdRepository(db, item_id)
    try:
        data = await repository.get_by_id()
        return data
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        logger.error(f"Fetch Selected IDS error {ex}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


