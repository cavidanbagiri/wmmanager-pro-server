from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


from src.dependencies.verify_project import ProjectVerify
from src.models import ProjectModel
from src.models.common_models import CompanyModel
from src.models.ordered_model import OrderedModel
from src.models.warehouse_model import WarehouseModel, MaterialCategoryModel, MaterialCodeModel
from src.schemas.user_schemas import UserTokenSchema
from src.schemas.warehouse_schema import WarehouseListCreateSchema, WarehouseListSelectByIDSResponse

from src.logging_config import setup_logger
logger = setup_logger(__name__, 'warehouse.log')



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



class WarehouseSelectedByIDSRepository:

    def __init__(self, db: AsyncSession, payload: UserTokenSchema):
        self.db = db
        self.payload = payload
        self.verifier = ProjectVerify(user_payload=payload, model=WarehouseModel)


    async def fetch_selected_ids(self, ids: list[int]) -> list[WarehouseListSelectByIDSResponse]:

        try:

            project_filter = self.verifier.get_project_filter()

            result = await self.db.execute(
                select(WarehouseModel)
                .where(WarehouseModel.id.in_(ids),
                       project_filter if project_filter is not True else True)
                .options(
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
            )

            warehouses = result.scalars().all()
            return [
                WarehouseListSelectByIDSResponse(
                    id=warehouse.id,
                    qty=warehouse.qty,
                    left_over=warehouse.left_over,
                    unit=warehouse.unit,
                    price=warehouse.price,
                    currency=warehouse.currency,
                    created_at=warehouse.created_at,
                    project=warehouse.project.project_name if warehouse.project else "N/A",
                    ordered=warehouse.ordered.username.title() if warehouse.ordered else "N/A",
                    company=warehouse.company.company_name if warehouse.company else "N/A",
                    category=warehouse.category.category_name if warehouse.category else "N/A",
                    material_code=warehouse.material_code.description if warehouse.material_code else "N/A"
                )
                for warehouse in warehouses
            ]

        except SQLAlchemyError as ex:
            logger.exception(f"Database operation failed {ex}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid warehouse data"
            )
        except Exception as ex:
            logger.error(f'Fetch Warehouse By ids error {ex}')
            raise HTTPException(status_code=400, detail=f"Fetch warehouse by ids error {ex}")



class WarehouseFetchRepository:

    def __init__(self, db: AsyncSession, payload: UserTokenSchema):
        self.db = db
        self.payload = payload
        self.verifier = ProjectVerify(user_payload=payload, model=WarehouseModel)

    async def fetch_warehouse(self):

        try:

            project_filter = self.verifier.get_project_filter()

            result = await self.db.execute(
                select(WarehouseModel)
                .where(project_filter if  project_filter is not True else True)
                .limit(150)
                .options(
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
            )

            warehouses = result.scalars().all()
            return [
                WarehouseListSelectByIDSResponse(
                    id=warehouse.id,
                    qty=warehouse.qty,
                    left_over=warehouse.left_over,
                    unit=warehouse.unit,
                    price=warehouse.price,
                    currency=warehouse.currency,
                    created_at=warehouse.created_at,
                    project=warehouse.project.project_name if warehouse.project else "N/A",
                    ordered=warehouse.ordered.username.title() if warehouse.ordered else "N/A",
                    company=warehouse.company.company_name if warehouse.company else "N/A",
                    category=warehouse.category.category_name if warehouse.category else "N/A",
                    material_code=warehouse.material_code.description if warehouse.material_code else "N/A"
                )
                for warehouse in warehouses
            ]

        except SQLAlchemyError as ex:
            logger.exception(f"Database operation failed {ex}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid warehouse data"
            )
        except Exception as ex:
            logger.error(f'Fetch Warehouse By ids error {ex}')
            raise HTTPException(status_code=400, detail=f"Fetch warehouse by ids error {ex}")