
from fastapi import HTTPException, APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.setup import get_db

from src.schemas.admin_schemas import UserRegisterSchema, ProjectCreateSchema, GroupCreateSchema, CategoryCreateSchema

from src.repositories.admin_repository import UserRegisterRepository, CreateProjectRepository, CreateGroupRepository, \
    CreateCategoryRepository

from src.dependencies.admin_required import verify_admin


from src.logging_config import setup_logger
logger = setup_logger(__name__, "admin.log")

router = APIRouter()


# Tested
@router.post('/register', status_code=201, dependencies=[Depends(verify_admin)])
async def register(register_data: UserRegisterSchema, db_session: AsyncSession = Depends(get_db)):

    repository = UserRegisterRepository(db_session)

    try:
        data = await repository.register(register_data)
        return data

    except HTTPException as ex:
        raise ex

    except Exception as e:
        logger.exception("Unexpected error register user: %s", e)
        raise HTTPException(500, "Internal server error")


# Tested
@router.post('/create-project', status_code=201, dependencies=[Depends(verify_admin)])
async def create_project(project_data: ProjectCreateSchema, db_session: AsyncSession = Depends(get_db)):
    repository = CreateProjectRepository(db_session)
    try:
        data = await repository.create_project(project_data)
        return data

    except HTTPException as ex:
        raise ex
    except Exception as e:
        logger.exception("Unexpected error create project: %s", e)
        raise HTTPException(500, "Internal server error")


# Tested
@router.post('/create-group', status_code=201, dependencies=[Depends(verify_admin)])
async def create_group(
    group_data: GroupCreateSchema,
    db_session: AsyncSession = Depends(get_db)
):
    repository = CreateGroupRepository(db_session)
    try:
        return await repository.create_group(group_data)
    except HTTPException as ex:
        raise ex
    except Exception as e:
        logger.exception("Group creation failed")
        raise HTTPException(500, "Internal server error")


# Tested
@router.post('/create-category', status_code=201, dependencies=[Depends(verify_admin)])
async def create_group(
    category_data: CategoryCreateSchema,
    db_session: AsyncSession = Depends(get_db)
):
    repository = CreateCategoryRepository(db_session)
    try:
        return await repository.create_category(category_data)
    except HTTPException as ex:
        raise ex
    except Exception as e:
        logger.exception("Category creation failed")
        raise HTTPException(500, "Internal server error")
