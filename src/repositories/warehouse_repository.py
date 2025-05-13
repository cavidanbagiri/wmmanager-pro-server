from fastapi import HTTPException, status

from sqlalchemy.dialects import postgresql

from sqlalchemy import select, update, insert, text, func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from watchfiles import awatch

from src.schemas.warehouse_schema import WarehouseUpdateSchema
from src.dependencies.verify_project import ProjectVerify
from src.models import ProjectModel
from src.models.common_models import CompanyModel
from src.models.ordered_model import OrderedModel
from src.models.warehouse_model import WarehouseModel, MaterialCategoryModel, MaterialCodeModel
from src.schemas.user_schemas import UserTokenSchema
from src.models.logging_models import LogUpdateWarehouseQtyModel
from src.schemas.warehouse_schema import WarehouseListCreateSchema, WarehouseStandartFetchResponseSchema, WarehouseFilterSchema

from src.logging_config import setup_logger
logger = setup_logger(__name__, 'warehouse.log')


class WarehouseStandartResponse:

    @staticmethod
    def format_response(model: list[WarehouseModel]):
        return [
            WarehouseStandartFetchResponseSchema(
                id=warehouse.id,
                qty=warehouse.qty,
                left_over=warehouse.left_over,
                unit=warehouse.unit,
                price=warehouse.price,
                currency=warehouse.currency,
                created_at=warehouse.created_at,
                project={
                    'id': warehouse.project.id,
                    'project_name': warehouse.project.project_name if warehouse.project else "N/A",
                },
                ordered={
                    'id': warehouse.ordered.id,
                    'ordered_name': warehouse.ordered.username.title() if warehouse.ordered else "N/A",
                },
                company={
                    'id': warehouse.company.id,
                    'company_name': warehouse.company.company_name if warehouse.company else "N/A"
                },
                material_code={
                    'id': warehouse.material_code.id,
                    'description': warehouse.material_code.description if warehouse.material_code else "N/A"
                },
                category=warehouse.category.category_name if warehouse.category else "N/A"
            )
            for warehouse in model
        ]


class WarehouseFetchQuery:

    @staticmethod
    async def fetch_query(session: AsyncSession, limit: int, *where_clauses):
        clean_clauses = [clause for clause in where_clauses if clause is not None and clause is not True]

        stmt = select(WarehouseModel)
        if clean_clauses:
            stmt = stmt.where(*clean_clauses)

        stmt = stmt.limit(limit).options(
                joinedload(WarehouseModel.ordered).load_only(
                    OrderedModel.f_name,
                    OrderedModel.m_name,
                    OrderedModel.l_name
                ),
                joinedload(WarehouseModel.category).load_only(
                    MaterialCategoryModel.category_name
                ),
                joinedload(WarehouseModel.project).load_only(
                    ProjectModel.project_name
                ),
                joinedload(WarehouseModel.material_code).load_only(
                    MaterialCodeModel.description
                ),
                joinedload(WarehouseModel.company).load_only(
                    CompanyModel.company_name
                )
            )

        return await session.execute(stmt)


class WarehouseCreateRepository:

    def __init__(self, db: AsyncSession, warehouse_data: WarehouseListCreateSchema, user_id:int):
        self.db = db
        self.warehouse_data = warehouse_data
        self.user_id = user_id

    async def create_warehouse_list(self, ) -> dict[str, str]:

        try:
            common_data = {
                "po_num": self.warehouse_data.po_num,
                "doc_num": self.warehouse_data.doc_num,
                "project_id": self.warehouse_data.project_id,
                "ordered_id": self.warehouse_data.ordered_id,
                "company_id": self.warehouse_data.company_id
            }

            records = []
            for idx, item in enumerate(self.warehouse_data.data_list, start=1):
                if item.qty <= 0:
                    raise ValueError(f'In {idx} quantity: {item.qty} is equal or less than 0')
                else:
                    temp = WarehouseModel(
                        created_by_id = self.user_id,
                        left_over = item.qty,
                        **item.model_dump(),
                        **common_data,
                    )
                    records.append(temp)

            self.db.add_all(records)
            await self.db.commit()
            return {"detail": "New data successfully created"}

        except SQLAlchemyError as ex:
            logger.exception(f"Database operation failed {ex}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid warehouse data"
            )
        except ValueError as ex:
            logger.warning(f"Validation error: {ex}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(ex)
            )
        except Exception as ex:
            logger.error(f"Create warehouse error {ex}")
            raise HTTPException(status_code=400, detail="Create warehouse error ")


class WarehouseUpdateRepository:

    def __init__(self, db: AsyncSession, update_data: WarehouseUpdateSchema, user_id: int):
        self.db = db
        self.update_data = update_data
        self.user_id = user_id

    async def update_warehouse(self) -> dict[str, str]:

        if self.update_data.qty <= 0:
            logger.error(f"Invalid quantity: {self.update_data.qty}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Quantity must be greater than zero. Got: {self.update_data.qty}"
            )

        try:

            result = await self.db.execute(
                select(WarehouseModel)
                .where(WarehouseModel.id == self.update_data.id)
                .with_for_update()
            )
            find_data = result.scalars().first()

            if find_data:
                self.check_qty(find_data.qty, find_data.left_over, self.update_data.qty)

                temp: dict = self.update_data.__dict__

                if self.update_data.qty != find_data.qty:
                    temp['left_over'] = self.update_data.qty - (find_data.qty - find_data.left_over)
                    await self.insert_warehouse_update_log(find_data)

                await self.db.execute(
                    update(WarehouseModel)
                    .where(WarehouseModel.id == self.update_data.id)
                    .values(**temp)
                )
                await self.db.commit()
                return {'detail':'Successfully updated'}

            else:
                logger.error('Warehouse data not found')
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Warehouse not found')

        except HTTPException as ex:
            raise
        except SQLAlchemyError as ex:
            logger.exception(f"Database error during return to stock {ex}")
            raise HTTPException(500, f"Failed to return to stock 1 {ex}")
        except Exception as ex:
            logger.exception(f"Unexpected error {ex}")
            raise HTTPException(500, f"Internal Server Error 2 {ex}")


    def check_qty(self, inventor_qty: float, left_over_qty: float, updated_qty: float):
        print(f'difference is {inventor_qty} {type(left_over_qty)} {updated_qty}')
        if updated_qty < inventor_qty - left_over_qty:
            logger.error(f"Updated qty can't be less {inventor_qty} - {left_over_qty} = {inventor_qty - left_over_qty}. ")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Updated qty can't be less {inventor_qty} - {left_over_qty} = {inventor_qty - left_over_qty}. ")
        else:
            return None

    async def insert_warehouse_update_log(self, finded_data: WarehouseModel):
        try:
            await self.db.execute(
                insert(LogUpdateWarehouseQtyModel).values(
                    movement_type = 'update qty',
                    old_quantity = finded_data.qty,
                    old_left_over = finded_data.left_over,
                    new_quantity = self.update_data.qty,
                    new_left_over = self.update_data.qty - (finded_data.qty - finded_data.left_over),
                    warehouse_id = finded_data.id,
                    created_by_id = self.user_id
                )
            )
        except Exception as ex:
            logger.error(f'Warehouse log error : {ex}')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Can insert warehouse log {ex}')


class WarehouseGetByIdRepository:

    def __init__(self, db: AsyncSession, item_id: int, user_payload: UserTokenSchema):
        self.db = db
        self.item_id = item_id
        self.verifier = ProjectVerify(user_payload=user_payload, model=WarehouseModel)

    async def get_by_id(self) -> WarehouseStandartFetchResponseSchema:
        try:

            project_filter = self.verifier.get_project_filter()
            filters = []
            if project_filter is not True:
                filters.append(project_filter)

            filters.append(WarehouseModel.id == self.item_id)

            result = await WarehouseFetchQuery.fetch_query(self.db, 1, *filters)

            warehouse = result.scalars().first()

            if warehouse:
                temp = [warehouse]
                return WarehouseStandartResponse.format_response(temp)[0]
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse id not found")

        except HTTPException as ex:
            raise ex
        except SQLAlchemyError as ex:
            logger.exception(f"Database operation failed {ex}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid warehouse data"
            )
        except Exception as ex:
            logger.error(f'Get warehouse by id error {ex}')
            raise HTTPException(status_code=400, detail=f"Get warehouse by id error {ex}")


class WarehouseFetchRepository:

    def __init__(self, db: AsyncSession, payload: UserTokenSchema):
        self.db = db
        self.payload = payload
        self.verifier = ProjectVerify(user_payload=payload, model=WarehouseModel)

    async def fetch_warehouse(self):

        try:

            project_filter = self.verifier.get_project_filter()

            filters = []
            if project_filter is not True and project_filter is not None:
                filters.append(project_filter)

            result = await WarehouseFetchQuery.fetch_query(self.db, 150, *filters)
            warehouses = result.scalars().all()
            return WarehouseStandartResponse.format_response(list(warehouses))

        except SQLAlchemyError as ex:
            logger.exception(f"Database operation failed {ex}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid warehouse data"
            )
        except Exception as ex:
            logger.error(f'Fetch Warehouse By ids error {ex}')
            raise HTTPException(status_code=400, detail=f"Fetch warehouse by ids error {ex}")


class WarehouseSelectedByIDSRepository:

    def __init__(self, db: AsyncSession, payload: UserTokenSchema):
        self.db = db
        self.payload = payload
        self.verifier = ProjectVerify(user_payload=payload, model=WarehouseModel)


    async def fetch_selected_ids(self, ids: list[int]) -> list[WarehouseStandartFetchResponseSchema]:

        try:

            project_filter = self.verifier.get_project_filter()

            filters = []
            if project_filter is not True and project_filter is not None:
                filters.append(project_filter)
            filters.append(WarehouseModel.id.in_(ids))

            result = await WarehouseFetchQuery.fetch_query(self.db, len(ids), *filters)
            warehouses = result.scalars().all()

            return WarehouseStandartResponse.format_response(list(warehouses))

        except SQLAlchemyError as ex:
            logger.exception(f"Database operation failed {ex}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid warehouse data"
            )
        except Exception as ex:
            logger.error(f'Fetch Warehouse By ids error {ex}')
            raise HTTPException(status_code=400, detail=f"Fetch warehouse by ids error {ex}")


class WarehouseFilterRepository:

    def __init__(self, db: AsyncSession, filter_data: WarehouseFilterSchema, user_payload: UserTokenSchema):
        self.db = db
        self.filter_data = filter_data
        self.user_payload = user_payload
        self.verifier = ProjectVerify(user_payload, WarehouseModel)

    async def filter(self):
        try:
            # query = self._build_filter_query()
            # data = await self.db.execute(text(query))
            data = await self.db.execute(self._build_filter_query())
            temp = data.mappings().fetchall()
            return temp

        except Exception as ex:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{ex}")

    def _build_filter_query(self):

        ALLOWED_FILTER_FIELDS = {
            "material_name": lambda val: WarehouseModel.material_name.ilike(f'%{val}%'),
            "qty": lambda val: WarehouseModel.qty == val,
            "unit": lambda val: WarehouseModel.unit.ilike(f'%{val}%'),
            "price": lambda val: WarehouseModel.price == val,
            "currency": lambda val: WarehouseModel.currency.ilike(f'%{val}%'),
            "category_id": lambda val: WarehouseModel.category_id == val,
            "po_num": lambda val: WarehouseModel.po_num.ilike(f'%{val}%'),
            "doc_num": lambda val: WarehouseModel.doc_num.ilike(f'%{val}%'),
            "material_code_id": lambda val: WarehouseModel.material_code_id == val,
            "project_id": lambda val: WarehouseModel.project_id == val,
            "ordered_id": lambda val: WarehouseModel.ordered_id == val,
            "company_id": lambda val: WarehouseModel.company_id == val,
            "created_at": lambda val: func.date(WarehouseModel.created_at) == val,
        }

        filters = []

        for field, value in self.filter_data.filter_data.__dict__.items():
            if value is not None and field in ALLOWED_FILTER_FIELDS:
                condition = ALLOWED_FILTER_FIELDS[field](value)
                if condition is not None:
                    filters.append(condition)

        project = self._verify_project()
        if project is not None:
            filters.append(project)
        stmt = select(WarehouseModel).where(*filters)
        #this will give to us exact writing row query for testing
        print(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
        return stmt

    def _verify_project(self) :
        project_id: int = self.user_payload.get('project_id')
        if not project_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project ID required.")

        if project_id == 1:
            return None  # no filter needed

        return WarehouseModel.project_id == project_id
