
from typing import List, Tuple

from fastapi import HTTPException, status
from sqlalchemy.dialects import postgresql

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, insert, func
from sqlalchemy.orm import joinedload, aliased

from src.schemas.stock_schema import StockFilterSchema
from src.schemas.stock_schema import StockReturnToWarehouseSchema
from src.dependencies.verify_project import ProjectVerify
from src.models.common_models import CompanyModel, ProjectModel
from src.models.ordered_model import OrderedModel
from src.models.stock_models import StockModel
from src.models.warehouse_model import WarehouseModel, MaterialCategoryModel, MaterialCodeModel
from src.models.logging_models import LogStockMovementModel
from src.schemas.stock_schema import StockAddSchema, StockListRequest, StockStandardFetchResponse

from src.logging_config import setup_logger
from src.schemas.user_schemas import UserTokenSchema

logger = setup_logger(__name__, 'stock.log')


class StockStandardResponse:

    @staticmethod
    def format_response(model: list[StockModel]):
        return [
            StockStandardFetchResponse(
                id=i.id,
                quantity=i.quantity,
                left_over=i.left_over,
                serial_number=i.serial_number,
                material_id=i.material_id,
                material_name=i.warehouses.material_name,
                material_code={
                    "id": i.warehouses.material_code.id,
                    "description": i.warehouses.material_code.description
                },
                category={
                    "id": i.warehouses.category.id,
                    "category": i.warehouses.category.category_name
                },
                ordered={
                    "id": i.warehouses.ordered.id,
                    "ordered": i.warehouses.ordered.username
                },
                company={
                    "id": i.warehouses.company.id,
                    "company": i.warehouses.company.company_name
                },
                project={
                    "id": i.warehouses.project.id,
                    "company": i.warehouses.project.project_name
                }
            )
            for i in model
        ]


class StockFetchQuery:

    @staticmethod
    async def fetch_query(session: AsyncSession, limit: int, *where_clauses):
        filters = [ i for i in where_clauses if i is not None and i is not True ]

        stmt = select(StockModel)

        stmt = stmt.where(*filters)

        stmt = stmt.options(
            joinedload(StockModel.warehouses)
            .options(
                joinedload(WarehouseModel.ordered).load_only(OrderedModel.f_name, OrderedModel.m_name, OrderedModel.l_name),
                joinedload(WarehouseModel.category).load_only(MaterialCategoryModel.category_name),
                joinedload(WarehouseModel.company).load_only(CompanyModel.company_name),
                joinedload(WarehouseModel.material_code).load_only(MaterialCodeModel.description),
                joinedload(WarehouseModel.project).load_only(ProjectModel.project_name),
            )
        )

        return await session.execute(stmt)


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


class StockReturnToWarehouseRepository:

    def __init__(self, db: AsyncSession, return_data: StockReturnToWarehouseSchema, user_id: int):
        self.db = db
        self.return_data = return_data
        self.user_id = user_id

    async def return_to_warehouse(self) -> dict[str, str]:
        return_qty = self.return_data.quantity

        if return_qty <= 0:
            logger.error(f"Invalid quantity: {return_qty}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Quantity must be greater than zero. Got: {return_qty}"
            )

        try:
            # Lock both rows to prevent concurrent updates
            result = await self.db.execute(
                select(StockModel)
                .where(StockModel.id == self.return_data.id)
                .with_for_update()
            )
            stock = result.scalars().first()

            if not stock:
                logger.error(f"Stock {self.return_data.id} not found.")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Stock not found."
                )

            if return_qty > stock.left_over:
                logger.error(f"Requested return ({return_qty}) exceeds available left_over ({stock.left_over})")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot return more than available left_over stock."
                )

            result = await self.db.execute(
                select(WarehouseModel)
                .where(WarehouseModel.id == self.return_data.warehouse_id)
                .with_for_update()
            )
            warehouse = result.scalars().first()

            if not warehouse:
                logger.error(f"Warehouse {self.return_data.warehouse_id} not found.")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Warehouse not found."
                )

            # Create a new stock
            await self.insert_stock_movement_log(finded_data=stock)

            # Perform updates
            await self.db.execute(
                update(StockModel)
                .where(StockModel.id == self.return_data.id)
                .values(
                    left_over=StockModel.left_over - return_qty,
                    quantity=StockModel.quantity - return_qty
                )
            )

            await self.db.execute(
                update(WarehouseModel)
                .where(WarehouseModel.id == self.return_data.warehouse_id)
                .values(left_over=WarehouseModel.left_over + return_qty)
            )

            await self.db.commit()
            return {"detail": "Successfully Returned"}

        except HTTPException as ex:
            raise ex

        except SQLAlchemyError as ex:
            await self.db.rollback()
            logger.exception("Database error during warehouse return")
            raise HTTPException(status_code=500, detail="Failed to return to warehouse") from ex

        except Exception as ex:
            await self.db.rollback()
            logger.exception("Unexpected error during warehouse return")
            raise HTTPException(status_code=500, detail="Internal Server Error") from ex

    async def insert_stock_movement_log(self, finded_data: StockModel):
        try:
            await self.db.execute(
                insert(LogStockMovementModel).values(
                    movement_type = 'return to warehouse',
                    old_quantity = finded_data.quantity,
                    old_left_over = finded_data.left_over,
                    return_quantity = self.return_data.quantity,
                    new_left_over = finded_data.left_over - self.return_data.quantity,
                    stock_id = finded_data.id,
                    warehouse_id = self.return_data.warehouse_id,
                    created_by_id = self.user_id
                )
            )
        except Exception as ex:
            logger.error(f'Stock log error : {ex}')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Can insert stock log {ex}')


class StockFetchRepository:

    def __init__(self, db: AsyncSession, payload: UserTokenSchema):
        self.db = db
        self.payload = payload
        self.verifier = ProjectVerify(user_payload=payload, model=StockModel)

    async def fetch_stock_list(self) -> List[StockStandardFetchResponse]:

        try:

            project_verify = self.verifier.get_project_filter()

            filters = []
            if project_verify is not True:
                filters.append(project_verify)
            result = await StockFetchQuery.fetch_query(self.db, 150, *filters)
            stocks = result.unique().scalars().all()

            return StockStandardResponse.format_response(list(stocks))


        except SQLAlchemyError as ex:
            logger.exception(f"Database operation failed {ex}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid warehouse data {ex}"
            )

        except Exception as ex:
            logger.error(f"Fetch stock list error : {ex}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Fetch stock list error {ex}")


class StockFetchSelectedByIDSRepository:

    def __init__(self, db: AsyncSession, payload: UserTokenSchema, ids: list[int]):
        self.db = db
        self.payload = payload
        self.verifier = ProjectVerify(user_payload=payload, model=StockModel)
        self.ids = ids

    async def fetch_selected_ids(self) -> List[StockStandardFetchResponse]:

        try:

            project_verify = self.verifier.get_project_filter()

            filters = []
            if project_verify is not True:
                filters.append(project_verify)
            filters.append(StockModel.id.in_(self.ids))
            result = await StockFetchQuery.fetch_query(self.db, len(self.ids), *filters)
            stocks = result.unique().scalars().all()

            return StockStandardResponse.format_response(list(stocks))

        except SQLAlchemyError as ex:
            logger.exception(f"Database operation failed {ex}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid warehouse data"
            )

        except Exception as ex:
            logger.error(f"Fetch stock list error : {ex}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fetch stock list error")


class StockGetByIdRepository:

    def __init__(self, db: AsyncSession, item_id: int, user_payload: UserTokenSchema):
        self.db = db
        self.item_id = item_id
        self.verifier = ProjectVerify(user_payload=user_payload, model=StockModel)

    async def get_by_id(self) -> StockStandardFetchResponse:
        try:
            return await self._fetch_data()
        except HTTPException as ex:
            raise ex
        except SQLAlchemyError as ex:
            logger.exception(f"Database operation failed {ex}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid stock data"
            )
        except Exception as ex:
            logger.error(f'Get stock by id error {ex}')
            raise HTTPException(status_code=400, detail=f"Get stock by id error {ex}")

    async def _fetch_data(self):
        project_verify = self.verifier.get_project_filter()

        filters = []
        if project_verify is not True:
            filters.append(project_verify)
        filters.append(StockModel.id == self.item_id)
        result = await StockFetchQuery.fetch_query(self.db, 1, *filters)

        stock = result.scalars().first()

        if stock:
            temp = [stock]
            return StockStandardResponse.format_response(temp)[0]
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock id not available")


class StockFilterRepository:

    def __init__(self, db: AsyncSession, filter_data: StockFilterSchema, user_payload: UserTokenSchema):
        self.db = db
        self.filter_data = filter_data
        self.user_payload = user_payload
        self.verifier = ProjectVerify(user_payload=user_payload, model=StockModel)

    async def filter(self):

        try:
            data = await self.db.execute(self._build_query())
            temp = data.scalars().all()
            result = StockStandardResponse.format_response(list(temp))
            return result

        except Exception as ex:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{ex}")

    def _build_query(self):
        ALLOWED_FIELDS = {
            "material_name": lambda val: WarehouseModel.material_name.ilike(f'%{val}%'),
            "quantity": lambda val: StockModel.quantity == val,
            "unit": lambda val: WarehouseModel.unit.ilike(f'%{val}%'),
            "price": lambda val: WarehouseModel.price == val,
            "currency": lambda val: WarehouseModel.currency == val,
            "category_id": lambda val: WarehouseModel.category_id == val,
            "po_num": lambda val: WarehouseModel.po_num.ilike(f'%{val}%'),
            "doc_num": lambda val: WarehouseModel.doc_num.ilike(f'%{val}%'),
            "material_code_id": lambda val: WarehouseModel.material_code_id == val,
            "project_id": lambda val: StockModel.project_id == val,
            "ordered_id": lambda val: StockModel.warehouses.ordered_id == val,
            "company_id": lambda val: WarehouseModel.company_id == val,
            "created_at": lambda val: func.date(StockModel.created_at) == val,
            "serial_number": lambda val: StockModel.serial_number == val,
            "material_id": lambda val: StockModel.material_id == val,
        }

        filters = []

        for field, value in self.filter_data.filter_data.__dict__.items():
            if value is not None and field in ALLOWED_FIELDS:
                condition = ALLOWED_FIELDS[field](value)
                filters.append(condition)

        project = self._verify_project()
        if project is not None:
            filters.append(project)

        stmt = (
            select(StockModel)
            .join(WarehouseModel, StockModel.warehouse_id == WarehouseModel.id, isouter=True)
            .where(*filters)
            .options(
                joinedload(StockModel.warehouses).options(
                    joinedload(WarehouseModel.ordered).load_only(OrderedModel.f_name, OrderedModel.m_name,
                                                                 OrderedModel.l_name),
                    joinedload(WarehouseModel.category).load_only(MaterialCategoryModel.category_name),
                    joinedload(WarehouseModel.company).load_only(CompanyModel.company_name),
                    joinedload(WarehouseModel.material_code).load_only(MaterialCodeModel.description),
                    joinedload(WarehouseModel.project).load_only(ProjectModel.project_name)
                ),
            )
        )

        return stmt

    def _verify_project(self):
        project_id: int = self.user_payload.get('project_id')
        if not project_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project ID required.")

        if project_id == 1:
            return None

        return StockModel.project_id == project_id

