
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.setup import get_db

from src.dependencies.roles_authorization import (common_role_based_authorization,
                                                  project_role_based_authorization)

from src.auth.token_handler import TokenHandler

from src.schemas.admin_schemas import GroupResponseSchema, CategoryResponseSchema
from src.schemas.common_schemas import CompanyCreteSchema, CompanyResponseSchema, OrderedCreateSchema, \
    OrderedResponseSchema, MaterialCodeCreateSchema, MaterialCodeResponseSchema

from src.repositories.common_repository import GroupFetchRepository, CompanyCreateRepository, CompanyFetchRepository, \
    OrderedCreateRepository, OrderedFetchRepository, CategoryFetchRepository, MaterialCodeCreateRepository, \
    MaterialCodeFetchRepository

from src.logging_config import setup_logger
logger = setup_logger(__name__, 'common.log')

router = APIRouter()


@router.get('/fetch-groups', status_code=200,
            dependencies=[Depends(TokenHandler.verify_access_token)],
            response_model=List[GroupResponseSchema])
async def fetch_groups(db: AsyncSession = Depends(get_db)):
    repository = GroupFetchRepository(db)
    try:
        return await repository.groups()
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error fetching groups: %s", e)
        return JSONResponse(status_code=500, content="Internal Server Error")


@router.get('/fetch-categories', status_code=status.HTTP_200_OK,
            dependencies=[Depends(TokenHandler.verify_access_token)],
            response_model=List[CategoryResponseSchema])
async def fetch_groups(db: AsyncSession = Depends(get_db)):
    repository = CategoryFetchRepository(db)
    try:
        return await repository.fetch_categories()
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error fetching groups: %s", e)
        return JSONResponse(status_code=500, content="Internal Server Error")



# Tested
@router.post('/create-company', status_code=201,
             response_model=CompanyResponseSchema)
async def create_company(company_data: CompanyCreteSchema,
                         db: AsyncSession = Depends(get_db),
                         user_id = Depends(common_role_based_authorization)):
    repository = CompanyCreateRepository(db)

    try:
        data = await repository.create_company(company_data, user_id)
        return data
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        logger.error(f'Create Company Error : {ex}')
        raise HTTPException(500, "Internal server error")


@router.get('/fetch-companies', status_code=200,
            dependencies=[Depends(TokenHandler.verify_access_token)],
            response_model=List[CompanyResponseSchema]
            )
async def fetch_companies(db: AsyncSession = Depends(get_db)):
    repository = CompanyFetchRepository(db)

    try:
        return await repository.companies()
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error fetching companies: %s", e)
        return JSONResponse(status_code=500, content="Internal Server Error")



# Tested
@router.post('/create-ordered', status_code=201,
             response_model=OrderedResponseSchema)
async def create_ordered(ordered_data: OrderedCreateSchema,
                         db: AsyncSession = Depends(get_db),
                         user_id = Depends(project_role_based_authorization)):

    repository = OrderedCreateRepository(db)

    try:

        data = await repository.create_ordered(ordered_data, user_id)
        return data
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        logger.error(f'Create Ordered Error : {ex}')
        raise HTTPException(500, "Internal server error")



@router.get('/fetch-ordered',
            dependencies=[Depends(TokenHandler.verify_access_token)],
            status_code=201)
async def fetch_ordered(db: AsyncSession = Depends(get_db)):
    repository = OrderedFetchRepository(db)

    try:
        return await repository.fetch_ordered()
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error fetching ordered: %s", e)
        return JSONResponse(status_code=500, content="Internal Server Error")



# Tested
@router.post('/create-material_code', status_code=201)
async def create_material_code(material_code_data: MaterialCodeCreateSchema,
                         db: AsyncSession = Depends(get_db),
                         user_id = Depends(common_role_based_authorization)):
    repository = MaterialCodeCreateRepository(db)

    try:
        data = await repository.create_material_code(material_code_data, user_id)
        return data
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        logger.error(f'Create Material Code Error : {ex}')
        raise HTTPException(500, "Internal server error")


@router.get('/fetch-material_code',
            dependencies = [Depends(TokenHandler.verify_access_token)],
            status_code=200,
            response_model=List[MaterialCodeResponseSchema])
async def fetch_material_code(db:AsyncSession = Depends(get_db) ):
    repository = MaterialCodeFetchRepository(db)
    try:
        data = await repository.fetch_material_code()
        return data
    except HTTPException as ex:
        raise ex
    except Exception as  ex:
        logger.error(f'Fetch Material Code Error : {ex}')
        raise HTTPException(500, "Internal server error")

