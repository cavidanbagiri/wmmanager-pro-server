
import os

from contextlib import asynccontextmanager

from src.logging_config import setup_logger

from src.routers import user_router, area_router, admin_router, common_router
from src.routers import stock_router, warehouse_router


logger = setup_logger(__name__, "main.log")


from fastapi import FastAPI

from dotenv import load_dotenv


load_dotenv()

# Startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.database.setup import get_db
    from src.repositories.admin_repository import CreateAdminRepository
    from src.schemas.admin_schemas import UserRegisterSchema
    async for db in get_db():
        repo = CreateAdminRepository(db)
        try:
            await repo.create_admin(UserRegisterSchema(
                    first_name="admin",
                    last_name="admin",
                    email=os.getenv('INITIAL_ADMIN_USER'),
                    password=os.getenv('INITIAL_ADMIN_PASSWORD'),
                    middle_name="",
                    project_id=1,
                    is_admin=True,
                ))
        except Exception as ex:
            logger.info(f"Create Initial Admin Error, {ex}")
        break
    yield


app = FastAPI(lifespan = lifespan)


# Include Routers
app.include_router(router=admin_router.router, prefix='/api/admin', tags=['Admin'])
app.include_router(router=user_router.router, prefix='/api/auth', tags=['User'])
app.include_router(router=common_router.router, prefix='/api/common', tags=['Common'])
app.include_router(router=warehouse_router.router, prefix='/api/warehouse', tags=['Warehouse'])
app.include_router(router=stock_router.router, prefix='/api/stock', tags=['Stock'])
app.include_router(router=area_router.router, prefix='/api/area', tags=['Area'])




