
from typing import List, Tuple

from fastapi import HTTPException, status

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from sqlalchemy.orm import joinedload

from src.dependencies.verify_project import ProjectVerify
from src.models.common_models import CompanyModel
from src.models.ordered_model import OrderedModel
from src.models.stock_models import StockModel
from src.models.warehouse_model import WarehouseModel, MaterialCategoryModel, MaterialCodeModel
from src.schemas.stock_schema import StockAddSchema, StockListRequest, StockListResponse

from src.logging_config import setup_logger
from src.schemas.user_schemas import UserTokenSchema

logger = setup_logger(__name__, 'stock.log')


class StockAddRepository:

    def __init__(self, db: AsyncSession, stock_data: StockListRequest, user_id: int):
        self.db = db
        self.stock_data: List[StockAddSchema] = stock_data.stock_data_list
        self.project_id:int = stock_data.project_id
        self.user_id: int = user_id

    async def add_stock_list(self) -> dict[str, str]:
        try:

            self.check_project()

            async with self.db.begin_nested() if self.db.in_transaction() else self.db.begin():

                warehouse_update_list, ready_stock_data = await self._check_quantity()

                await self._update_model(warehouse_update_list, ready_stock_data)

                return {"detail": "New Stock successfully created"}

        except ValueError as ex:
            logger.error(f'{ex}')
            raise HTTPException(status_code=400, detail=str(ex))

        except Exception as ex:
            logger.error(f'{ex}')
            raise ex

    def check_project(self):
        if len(self.stock_data):
            first_project_id: int = self.stock_data[0].project_id
            for i in self.stock_data:
                if first_project_id != i.project_id:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project must be the same")
                if self.project_id != 1 and self.project_id != i.project_id:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authorization error. Can do any operation because of wrong project")
        else:
            raise ValueError("Please add item for operation")

    async def _check_quantity(self) -> Tuple[List[dict], List[StockModel]]:
        row: int = 0
        warehouse_data = []
        stock_data = []
        for i in self.stock_data:
            row += 1
            if i.quantity <= 0:
                raise ValueError(f'In {row} Entering quantity Cant be negative or 0')

            w_data = await self.db.get(
                WarehouseModel,
                i.warehouse_id,
                with_for_update=True
            )


            if not w_data:
                raise ValueError(f"Row {row}: Warehouse not found")
            if w_data.left_over < i.quantity:
                raise ValueError(
                    f"Row {row}: Not enough stock (has {w_data.left_over}, need {i.quantity})"
                )
            else:
                warehouse_data.append({
                    "id": w_data.id,
                    "left_over": i.quantity
                })
                stock_data.append(StockModel(
                    **StockAddSchema.model_dump(i),
                    left_over = i.quantity,
                    created_by_id = self.user_id,
                ))
        return warehouse_data, stock_data

    async def _update_model(self, warehouse_data: List[dict], stock_data: List[StockModel] ) -> None:

        try:

            [
                await self.db.execute(
                    update(WarehouseModel)
                    .where(WarehouseModel.id == i['id'])
                    .values(left_over=WarehouseModel.left_over - i['left_over'])
                )
                for i in warehouse_data
            ]

            self.db.add_all(stock_data)
            await self.db.commit()

        except SQLAlchemyError as ex:
            logger.exception(f"Database error during stock update {ex}")
            raise HTTPException(500, "Failed to update inventory")
        except Exception as ex:
            logger.exception(f"Unexpected error {ex}")
            raise HTTPException(500, "Internal Server Error")


class StockFetchRepository:

    def __init__(self, db: AsyncSession, payload: UserTokenSchema):
        self.db = db
        self.payload = payload
        self.verifier = ProjectVerify(user_payload=payload, model=StockModel)

    async def fetch_stock_list(self) -> List[StockListResponse]:

        try:

            project_verify = self.verifier.get_project_filter()

            query = (
                select(StockModel)
                .options(
                    joinedload(StockModel.warehouses)
                    .joinedload(WarehouseModel.ordered).load_only(OrderedModel.f_name, OrderedModel.m_name, OrderedModel.l_name),
                    joinedload(StockModel.warehouses)
                    .joinedload(WarehouseModel.category).load_only(MaterialCategoryModel.category_name),  # Load category
                    joinedload(StockModel.warehouses)
                    .joinedload(WarehouseModel.company).load_only(CompanyModel.company_name),
                    joinedload(StockModel.warehouses)
                    .joinedload(WarehouseModel.material_code).load_only(MaterialCodeModel.description),  # Load material_code
                    joinedload(StockModel.project)
                )
                .where(project_verify if project_verify is not True else True)
                .limit(150)
            )

            result = await self.db.execute(query)
            stocks = result.unique().scalars().all()

            return [
                StockListResponse(
                    id=i.id,
                    quantity=i.quantity,
                    left_over=i.left_over,
                    serial_number=i.serial_number,
                    material_id=i.material_id,
                    project=i.project.project_name,
                    material_name=i.warehouses.material_name,
                    description=i.warehouses.material_code.description,
                    category=i.warehouses.category.category_name,
                    ordered=i.warehouses.ordered.username,
                    company=i.warehouses.company.company_name
                )
                for i in stocks
            ]

        except SQLAlchemyError as ex:
            logger.exception(f"Database operation failed {ex}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid warehouse data"
            )

        except Exception as ex:
            logger.error(f"Fetch stock list error : {ex}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fetch stock list error")


class StockFetchSelectedByIDSRepository:

    def __init__(self, db: AsyncSession, payload: UserTokenSchema, ids: list[int]):
        self.db = db
        self.payload = payload
        self.verifier = ProjectVerify(user_payload=payload, model=StockModel)
        self.ids = ids

    async def fetch_selected_ids(self) -> List[StockListResponse]:

        try:

            project_verify = self.verifier.get_project_filter()

            query = (
                select(StockModel)
                .options(
                    joinedload(StockModel.warehouses)
                    .joinedload(WarehouseModel.ordered).load_only(OrderedModel.f_name, OrderedModel.m_name, OrderedModel.l_name),
                    joinedload(StockModel.warehouses)
                    .joinedload(WarehouseModel.category).load_only(MaterialCategoryModel.category_name),  # Load category
                    joinedload(StockModel.warehouses)
                    .joinedload(WarehouseModel.company).load_only(CompanyModel.company_name),
                    joinedload(StockModel.warehouses)
                    .joinedload(WarehouseModel.material_code).load_only(MaterialCodeModel.description),  # Load material_code
                    joinedload(StockModel.project)
                )
                .where(
                    StockModel.id.in_(self.ids),
                    project_verify if project_verify is not True else True)
                .limit(150)
            )

            result = await self.db.execute(query)
            stocks = result.unique().scalars().all()

            return [
                StockListResponse(
                    id=i.id,
                    quantity=i.quantity,
                    left_over=i.left_over,
                    serial_number=i.serial_number,
                    material_id=i.material_id,
                    project=i.project.project_name,
                    material_name=i.warehouses.material_name,
                    description=i.warehouses.material_code.description,
                    category=i.warehouses.category.category_name,
                    ordered=i.warehouses.ordered.username,
                    company=i.warehouses.company.company_name
                )
                for i in stocks
            ]

        except SQLAlchemyError as ex:
            logger.exception(f"Database operation failed {ex}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid warehouse data"
            )

        except Exception as ex:
            logger.error(f"Fetch stock list error : {ex}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fetch stock list error")


