
from typing import List, Tuple


from sqlalchemy import update, select, desc, insert
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import status, HTTPException

from src.dependencies.verify_project import ProjectVerify
from src.models import ProjectModel
from src.models.area_model import AreaModel
from src.models.ordered_model import GroupModel
from src.models.stock_models import StockModel
from src.models.warehouse_model import WarehouseModel
from src.models.logging_models import LogAreaMovementModel
from src.schemas.area_schemas import AreaListAddSchema, AreaAddSchema, AreaResponseSchema, AreaReturnStockSchema

from src.logging_config import setup_logger
from src.schemas.user_schemas import UserTokenSchema

logger = setup_logger(__name__, "area.log")


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

            data = await self.db.execute(
                select(AreaModel)
                .order_by(desc(AreaModel.created_at))
                .options(
                    joinedload(AreaModel.stock).joinedload(StockModel.warehouses).load_only(WarehouseModel.material_name),
                    joinedload(AreaModel.group).load_only(GroupModel.group_name),
                    joinedload(AreaModel.project).load_only(ProjectModel.project_name)
                )
                .where(project_verify if project_verify is not True else True)
                .limit(150)
            )
            temp = data.scalars().all()
            return_list: List = []
            for i in temp:
                data = AreaResponseSchema(
                    id = i.id,
                    material_name = i.stock.warehouses.material_name,
                    quantity=i.quantity,
                    serial_number=i.serial_number,
                    material_id=i.material_id,
                    username = i.username.title(),
                    provide_type = i.provide_type.title(),
                    project_name = i.project.project_name.upper(),
                    card_number = i.card_number,
                    created_at= i.created_at,
                    group_name = i.group.group_name.title(),
                    stock_id= i.stock.id,
                    project_id= i.project.id
                )
                return_list.append(data)
            return return_list

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

        project_filter = self.verifier.get_project_filter()

        data = await self.db.execute(
            select(AreaModel)
            .order_by(desc(AreaModel.created_at))
            .options(
                joinedload(AreaModel.stock).joinedload(StockModel.warehouses).load_only(WarehouseModel.material_name),
                joinedload(AreaModel.group).load_only(GroupModel.group_name),
                joinedload(AreaModel.project).load_only(ProjectModel.project_name)
            )
            .where(AreaModel.id == self.item_id, project_filter if  project_filter is not True else True)
            .limit(1)
        )
        temp = data.scalars().first()

        if temp:
            return self._format_response(temp)
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Area id not available")

    def _format_response(self, area: AreaModel):
        return AreaResponseSchema(
                    id = area.id,
                    material_name = area.stock.warehouses.material_name,
                    quantity = area.quantity,
                    serial_number = area.serial_number,
                    material_id = area.material_id,
                    username = area.username.title(),
                    provide_type = area.provide_type.title(),
                    project_name = area.project.project_name.upper(),
                    card_number = area.card_number,
                    created_at = area.created_at,
                    group_name = area.group.group_name.title(),
                    stock_id = area.stock.id,
                    project_id = area.project.id
                )