from typing import List
from abc import ABC, abstractmethod
from fastapi import HTTPException

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.common_models import CompanyModel
from src.models.ordered_model import GroupModel, OrderedModel

from src.logging_config import setup_logger
from src.models.warehouse_model import MaterialCategoryModel, MaterialCodeModel
from src.schemas.admin_schemas import GroupResponseSchema, CategoryResponseSchema
from src.schemas.common_schemas import CompanyCreteSchema, CompanyResponseSchema, OrderedCreateSchema, \
    OrderedResponseSchema, MaterialCodeCreateSchema, MaterialCodeResponseSchema

logger = setup_logger(__name__, 'common.log')


class VerifyColumnClass(ABC):

    @abstractmethod
    async def verify_column(self, *args, **kwargs):
        pass


class GroupFetchRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def groups(self) -> List[GroupResponseSchema]:

        try:
            result = await self.db.execute(
                select(GroupModel)
                .order_by(GroupModel.group_name)
            )
            groups = result.scalars().all()
            return [
                GroupResponseSchema(
                    id=group.id,
                    group_name=str(group.group_name).title()  # Business logic belongs here
                )
                for group in groups
            ]

        except Exception as ex:
            logger.error(f'Fetch groups error : {ex}')
            raise HTTPException(status_code=400, detail=f'Fetch groups error')



class CategoryFetchRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def fetch_categories(self) -> List[CategoryResponseSchema]:

        try:
            result = await self.db.execute(
                select(MaterialCategoryModel)
                .order_by(MaterialCategoryModel.category_name)
            )
            categories = result.scalars().all()
            return [
                CategoryResponseSchema(
                    id=category.id,
                    category_name=str(category.category_name).title()  # Business logic belongs here
                )
                for category in categories
            ]

        except Exception as ex:
            logger.error(f'Fetch groups error : {ex}')
            raise HTTPException(status_code=400, detail=f'Fetch groups error')



class CompanyCreateRepository(VerifyColumnClass):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_company(self, company_data: CompanyCreteSchema, user_id: int) -> CompanyResponseSchema:

        await self.verify_column(company_data.company_name, user_id)

        try:
            company = CompanyModel(**company_data.model_dump(), created_by_id=user_id)
            self.db.add(company)
            await self.db.flush()
            await self.db.commit()
            await self.db.refresh(company)
            return CompanyResponseSchema.model_validate(company)
        except HTTPException as ex:
            raise ex
        except Exception as ex:
            logger.error(f'create ordered data error: {ex}')
            raise HTTPException(status_code=500, detail=f'Create company  error')

    async def verify_column(self, company_name: str, user_id: int) -> None:
        try:
            company = await self.db.scalar(select(CompanyModel).where(CompanyModel.company_name == company_name.upper()))
            if company:
                logger.error(f'user_id {user_id} {company_name} already is available')
                raise HTTPException(status_code=409, detail=f'{company_name} already  is available')
        except Exception as ex:
            raise ex

class CompanyFetchRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def companies(self) -> List[CompanyResponseSchema]:

        try:
            result = await self.db.execute(
                select(CompanyModel)
                .order_by(CompanyModel.company_name)
            )
            companies = result.scalars().all()
            return [
                CompanyResponseSchema(
                    id=company.id,
                    company_name=str(company.company_name).upper(),
                )
                for company in companies
            ]

        except Exception as ex:
            logger.error(f'Fetch companies error : {ex}')
            raise HTTPException(status_code=400, detail=f'Fetch companies error')


class OrderedCreateRepository(VerifyColumnClass):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_ordered(self, ordered_data: OrderedCreateSchema, user_id: int) -> OrderedResponseSchema:

        await self.verify_column(ordered_data)

        try:
            ordered = OrderedModel(**ordered_data.model_dump(), created_by_id = user_id)
            self.db.add(ordered)
            await self.db.commit()
            await self.db.refresh(ordered)
            return OrderedResponseSchema.model_validate(ordered)
        except HTTPException as ex:
            raise ex
        except Exception as ex:
            logger.error(f'create ordered data error: {ex}')
            raise HTTPException(status_code=500, detail=f'Create ordered error')

    async def verify_column(self, ordered_data: OrderedCreateSchema):
        try:
            ordered_data = await self.db.scalar(select(OrderedModel).where(
                OrderedModel.f_name == ordered_data.f_name,
                OrderedModel.l_name == ordered_data.l_name,
                OrderedModel.email == ordered_data.email,
                OrderedModel.group_id == ordered_data.group_id,
                OrderedModel.project_id == ordered_data.project_id,
            ))
            if ordered_data:
                logger.error(f'user_id {ordered_data.f_name} {ordered_data.l_name} {ordered_data.group_id} {ordered_data.project_id} already is available')
                raise HTTPException(status_code=409, detail=f'{ordered_data.f_name}  already  is available')
        except Exception as ex:
                raise ex

class OrderedFetchRepository:

    def __init__(self, db: AsyncSession):
        self.db = db


    async def fetch_ordered(self):
        try:
            data = await self.db.execute(select(OrderedModel)
                                         .order_by(OrderedModel.f_name)
                                         .options(selectinload(OrderedModel.group))
                                         )
            return_data = data.scalars().fetchall()
            return [
                {
                    'id': i.id,
                    'username': i.username.title(),
                    'group': i.group.group_name.title()
                }
                for i in return_data
            ]
        except Exception as ex:
            logger.error(f'Fetch ordered error : {ex}')
            raise HTTPException(status_code=400, detail=f'Fetch ordered error')


class MaterialCodeCreateRepository(VerifyColumnClass):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_material_code(self, material_code_data: MaterialCodeCreateSchema, user_id: int) -> MaterialCodeResponseSchema:

        await self.verify_column(material_code_data.description, user_id)

        code_num = await self.create_code_num()
        code_data = MaterialCodeModel(
            description = material_code_data.description,
            code_num = code_num,
            created_by_id = user_id
        )
        self.db.add(code_data)
        await self.db.commit()
        await self.db.refresh(code_data)
        return MaterialCodeResponseSchema.model_validate(code_data)

    async def verify_column(self, description: str, user_id: int) -> None:
        try:
            material_code = await self.db.scalar(select(MaterialCodeModel).where(MaterialCodeModel.description == description.upper()))

            if material_code:
                logger.error(f'user_id {user_id} {description} already is available')
                raise HTTPException(status_code=409, detail=f'{description} already  is available')

        except Exception as ex:
            raise ex

    async def create_code_num(self) -> str:
        data = await self.db.execute(select(MaterialCodeModel).order_by(MaterialCodeModel.id))

        temp = data.scalars().all()
        return str(temp[-1].id+100000) if temp else '100000'

class MaterialCodeFetchRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def fetch_material_code(self):
        data = await self.db.execute(select(MaterialCodeModel.id, MaterialCodeModel.code_num, MaterialCodeModel.description))

        return data.mappings().all()