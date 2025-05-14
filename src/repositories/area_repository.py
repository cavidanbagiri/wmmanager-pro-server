
from typing import List, Tuple


from sqlalchemy import update, select, desc, insert, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import status, HTTPException

from src.models.warehouse_model import MaterialCategoryModel
from src.dependencies.verify_project import ProjectVerify
from src.models import ProjectModel
from src.models.area_model import AreaModel
from src.models.ordered_model import GroupModel, OrderedModel
from src.models.stock_models import StockModel
from src.models.warehouse_model import WarehouseModel
from src.models.logging_models import LogAreaMovementModel
from src.schemas.area_schemas import AreaListAddSchema, AreaAddSchema, AreaResponseSchema, AreaReturnStockSchema, AreaFilterSchema

from src.logging_config import setup_logger
from src.schemas.user_schemas import UserTokenSchema

logger = setup_logger(__name__, "area.log")


class AreaStandardResponse:

    @staticmethod
    def format_response(model: list[AreaModel]):
        return [
            AreaResponseSchema(
                id=area.id,
                material_name=area.stock.warehouses.material_name,
                quantity=area.quantity,
                unit=area.stock.warehouses.unit,
                serial_number=area.serial_number,
                material_id=area.material_id,
                username=area.username.title(),
                provide_type=area.provide_type.title(),
                card_number=area.card_number,
                created_at=area.created_at,
                project={
                    "id": area.project.id,
                    "project_name": area.project.project_name.upper(),
                },
                group={
                    "id":area.group.id,
                    "group_name":area.group.group_name.title()
                },
                stock={
                    "id": area.stock.id
                },
                category={
                    "id": area.stock.warehouses.category.id,
                    "category_name": area.stock.warehouses.category.category_name.title()
                },
            )
            for area in model
        ]


class AreaFetchQuery:

    @staticmethod
    async def fetch_query(session: AsyncSession, limit: int, *where_clause):

        # List Comprehension
        filters = [ i for i in where_clause if i is not None and i is not True ]

        stmt = select(AreaModel)
        stmt = stmt.where(*filters)

        stmt = stmt.limit(limit).options(
                    joinedload(AreaModel.stock).
                    joinedload(StockModel.warehouses).joinedload(WarehouseModel.category).load_only(MaterialCategoryModel.category_name),
                    joinedload(AreaModel.group).load_only(GroupModel.group_name),
                    joinedload(AreaModel.project).load_only(ProjectModel.project_name)
                )

        return await session.execute(stmt)


class AreaAddRepository:

    def __init__(self, db: AsyncSession, area_data: AreaListAddSchema, user_id: int):
        self.db = db
        self.area_data = area_data
        self.user_id: int = user_id
        self.project_id: int = area_data.project_id

    async def add_area(self) -> dict[str, str]:

        try:
            self._check_project()

            stock_data, area_data = await self._check_quantity()

            await self._update_model(stock_data, area_data)

            return {"detail": "Successfully provide"}

        except ValueError as ex:
            logger.error(f"Add area error : {ex}")
            raise HTTPException(status_code=400, detail=str(ex))
        except HTTPException as ex:
            raise ex
        except Exception as ex:
            logger.error(f"Add Area error : {ex}")
            raise HTTPException(status_code=500, detail="Internal server error")

    def _check_project(self):
        if len(self.area_data.datas) > 0:
            first_project_id: int = self.area_data.datas[0].project_id
            for i in self.area_data.datas:
                if first_project_id != i.project_id:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project must be the same")
                if self.project_id != 1 and self.project_id != i.project_id:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authorization error. Can do any operation because of wrong project")
        else:
            raise ValueError("Please add item for operation")

    async def _check_quantity(self) -> Tuple[List, List]:

        stock_data = []
        area_data = []

        common_data = {
            "card_number": self.area_data.card_number.strip().lower(),
            "username": self.area_data.username.strip().lower(),
            "group_id": self.area_data.group_id,
        }

        for idx, item in enumerate(self.area_data.datas, start=1):

            # 0 - Check entering quantity for 0 or none negative numbers
            if item.quantity <= 0:
                raise ValueError(f'In {idx} Entering quantity Cant be negative or 0')

            # 1 - Get stock data with stock_id
            s_data = await self.db.get(StockModel, item.stock_id, with_for_update=True)

            # 2 - Check there is a data or not
            if not s_data:
                raise ValueError(f"Row {idx}: Area not found")

            # 3 - Check stock model left over
            if s_data.left_over < item.quantity:
                raise ValueError(
                    f"Row {idx}: Not enough stock (has {s_data.left_over}, need {item.quantity})"
                )

            # 4 - Add data to stock array for update the stock list
            stock_data.append({
                "id": item.stock_id,
                "quantity": item.quantity
            })
            # 5 - Create ready records for creating a data for area model
            area_data.append(AreaModel(
                **AreaAddSchema.model_dump(item),
                **common_data,
                created_by_id= self.user_id
            ))

        return stock_data, area_data

    async def _update_model(self, stock_data, area_data):
        try:
            [
                await self.db.execute(
                    update(StockModel)
                    .where(StockModel.id == i['id'])
                    .values(left_over = StockModel.left_over - i['quantity'])
                )
                for i in stock_data
            ]

            self.db.add_all(area_data)
            await self.db.commit()

        except SQLAlchemyError as ex:
            logger.exception(f"Database error during stock update {ex}")
            raise HTTPException(500, "Failed to update stock {ex}")
        except Exception as ex:
            logger.exception(f"Unexpected error {ex}")
            raise HTTPException(500, "Internal Server Error")


class AreaReturnToStockRepository:

    def __init__(self, db: AsyncSession, return_data:AreaReturnStockSchema, user_id: int, user_payload: UserTokenSchema):
        self.db = db
        self.return_data = return_data
        self.user_id = user_id
        self.verifier = ProjectVerify(user_payload=user_payload, model=AreaModel)

    async def return_to_stock(self) -> dict[str, str]:

        return_quantity = self.return_data.quantity

        if return_quantity <= 0:
            logger.error("Quantity must be greater than zero.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be greater than zero."
            )

        try:

            project_filter = self.verifier.get_project_filter()

            # 1. Lock the AreaModel row for update
            result = await self.db.execute(
                select(AreaModel)
                .where(AreaModel.id == self.return_data.id,
                       project_filter if  project_filter is not True else True)
                .with_for_update()
            )
            area = result.scalars().first()

            if not area:
                logger.error(f"Area {self.return_data.id} not found.")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Area {self.return_data.id} not found."
                )

            if return_quantity > area.quantity:
                logger.error(f"Cannot return more than available quantity in area.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot return more than available quantity."
                )

            # 2. Lock the StockModel row for update
            result = await self.db.execute(
                select(StockModel)
                .where(StockModel.id == self.return_data.stock_id)
                .with_for_update()
            )
            stock = result.scalars().first()

            if not stock:
                logger.error(f"Stock {self.return_data.stock_id} not found.")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Stock {self.return_data.stock_id} not found."
                )

            await self.insert_area_movement_log(area)

            area.quantity -= return_quantity

            stock.left_over += return_quantity

            await self.db.commit()

            return {"detail": "Successfully returned"}

        except HTTPException as ex:
            raise ex

        except SQLAlchemyError as ex:
            await self.db.rollback()  # Rollback on DB errors
            logger.exception(f"Database error during return to stock {ex}")
            raise HTTPException(status_code=500, detail=f"Database error {ex}") from ex
        except Exception as ex:
            await self.db.rollback()
            logger.exception(f"Unexpected error during return to stock {ex}")
            raise HTTPException(status_code=500, detail=f"Internal Server Error {ex}") from ex

    async def insert_area_movement_log(self, finded_data: AreaModel):
        try:
            await self.db.execute(
                insert(LogAreaMovementModel).values(
                    movement_type = 'return to stock',
                    old_quantity = finded_data.quantity,
                    return_quantity = self.return_data.quantity,
                    area_id = finded_data.id,
                    stock_id = self.return_data.stock_id,
                    created_by_id = self.user_id
                )
            )
        except Exception as ex:
            logger.error(f'Stock log error : {ex}')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Can insert stock log {ex}')


class AreaFetchRepository:

    def __init__(self, db: AsyncSession, payload: UserTokenSchema):

        self.db = db
        self.user_payload = payload
        self.verifier = ProjectVerify(user_payload=payload, model=AreaModel)


    async def fetch(self) -> List[AreaResponseSchema]:

        try:

            project_verify = self.verifier.get_project_filter()

            filters = []

            if project_verify is not True:
                filters.append(project_verify)
            data = await AreaFetchQuery.fetch_query(self.db, 150, *filters)

            temp = data.scalars().all()

            return AreaStandardResponse.format_response(list(temp))

        except SQLAlchemyError as ex:
            logger.exception(f"Database operation failed {ex}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid area data"
            )

        except Exception as ex:
            logger.error(f"Fetch area list error : {ex}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fetch area list error")


class AreaGetByIdRepository:

    def __init__(self, db: AsyncSession, item_id: int, user_payload: UserTokenSchema):
        self.db = db
        self.item_id = item_id
        self.verifier = ProjectVerify(user_payload=user_payload, model=AreaModel)

    async def get_by_id(self) -> AreaResponseSchema:
        try:
            return await self._fetch_data()
        except HTTPException as ex:
            raise ex
        except SQLAlchemyError as ex:
            logger.exception(f"Database operation failed {ex}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid area data"
            )
        except Exception as ex:
            logger.error(f'Get area by id error {ex}')
            raise HTTPException(status_code=400, detail=f"Get area by id error {ex}")

    async def _fetch_data(self):

        project_verify = self.verifier.get_project_filter()

        filters = []

        if project_verify is not True:
            filters.append(project_verify)

        filters.append(AreaModel.id == self.item_id)

        data = await AreaFetchQuery.fetch_query(self.db, 1, *filters)

        result = data.scalars().first()

        if result:
            temp = [result]
            return AreaStandardResponse.format_response(temp)[0]
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Area id not available")


class AreaFilterRepository:

    def __init__(self, db: AsyncSession, filter_data: AreaFilterSchema, user_payload: UserTokenSchema):
        self.db = db
        self.filter_data = filter_data
        self.project_verifier = ProjectVerify(user_payload, model=AreaModel)
        self.user_payload = user_payload

    async def filter(self):

        try:
            data = await self.db.execute(self._build_query())
            temp = data.unique().scalars().all()
            result = AreaStandardResponse.format_response(list(temp))
            return result

        except Exception as ex:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{ex}")

    def _build_query(self):

        ALLOWED_FIELDS = {
            "material_name": lambda val : WarehouseModel.material_name.ilike(f'%{val}%'),
            "quantity": lambda val : AreaModel.quantity.ilike(f'%{val}%'),
            "serial_number": lambda val : AreaModel.serial_number.ilike(f'%{val}%'),
            "material_id": lambda val : AreaModel.material_id.ilike(f'%{val}%'),
            "username": lambda val : AreaModel.username.ilike(f'%{val}%'),
            "provide_type": lambda val : AreaModel.provide_type.ilike(f'%{val}%'),
            "card_number": lambda val : AreaModel.card_number.ilike(f'%{val}%'),
            "created_at": lambda val : func.date(AreaModel.created_at) == val,
            "group_id": lambda val : GroupModel.id == val,
            "stock_id": lambda val : AreaModel.stock_id == val,
            "project_id": lambda val : AreaModel.project_id == val,
            "category_id": lambda val : MaterialCategoryModel.id == val
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
            select(AreaModel)
            .where(*filters)
            .options(
                joinedload(AreaModel.stock).
                joinedload(StockModel.warehouses).joinedload(WarehouseModel.category).load_only(
                    MaterialCategoryModel.category_name),
                joinedload(AreaModel.group).load_only(GroupModel.group_name),
                joinedload(AreaModel.project).load_only(ProjectModel.project_name)
            )
        )
        # print('-----------------------------------------')
        # print(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
        # print('-----------------------------------------')

        return stmt

    def _verify_project(self):
        project_id: int = self.user_payload.get('project_id')
        if not project_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project ID required.")

        if project_id == 1:
            return None

        return AreaModel.project_id == project_id
