from typing import List, Tuple


from sqlalchemy import update, select, desc
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import status, HTTPException
from watchfiles import awatch

from src.dependencies.verify_project import ProjectVerify
from src.models import ProjectModel
from src.models.area_model import AreaModel
from src.models.ordered_model import GroupModel
from src.models.stock_models import StockModel
from src.models.warehouse_model import WarehouseModel
from src.schemas.area_schemas import AreaListAddSchema, AreaAddSchema, AreaResponseSchema

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
                raise ValueError(f"Row {idx}: Warehouse not found")

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



class AreaFetchRepository:

    def __init__(self, db: AsyncSession, payload: UserTokenSchema):

        self.db = db
        self.user_payload = payload
        self.verifier = ProjectVerify(user_payload=payload, model=AreaModel)


    async def fetch(self):

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
                    group_name = i.group.group_name.title()
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