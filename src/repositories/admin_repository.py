
from fastapi import HTTPException, status

from sqlalchemy import insert, select, or_, exists
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import UserModel, ProjectModel
from src.models.ordered_model import GroupModel
from src.models.warehouse_model import MaterialCategoryModel
from src.schemas.admin_schemas import UserRegisterSchema, UserResponseSchema, ProjectCreateSchema, \
    ProjectResponseSchema, GroupCreateSchema, GroupResponseSchema, CategoryCreateSchema, CategoryResponseSchema
from src.utils.hash_password import PasswordHash

from src.logging_config import setup_logger
logger = setup_logger(__name__, "admin.log")


# This is lifespan method
class CreateAdminRepository:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.h_password = PasswordHash()

    async def create_admin(self, user_data: UserRegisterSchema):

        hashing_password = self.h_password.hash_password(user_data.password)
        user_data.password = hashing_password

        if await self.admin_exists(user_data.email):
            return

        try:
            await self.db.execute(insert(UserModel).values(
                first_name = user_data.first_name,
                middle_name = user_data.middle_name,
                last_name = user_data.last_name,
                email = user_data.email,
                password = user_data.password,
                is_admin = True,
                project_id = 1
            ))
            await self.db.commit()
            logger.warning("New Admin Successfully created")

            return user_data

        except Exception as ex:
            logger.error(f"Initial admin can't cretaed. {ex}")
            raise HTTPException(status_code=403, detail=f"{ex}")

    async def admin_exists(self, email) -> bool:

        data = await self.db.execute(select(UserModel).where(UserModel.email == email))
        if data.scalar():
            return True
        return False

#Tested
class VerifyEmail:

    @staticmethod
    async def verify_email(db: AsyncSession, register_data: UserRegisterSchema) -> None:
        try:
            logger.info(f'Verifying Email : {register_data.email}')
            print(f'reghister data {register_data}')
            user = await db.execute(select(exists().where(UserModel.email == register_data.email.strip().lower())))
            if user.scalar():
                logger.debug(f'{register_data.email} email already use')
                raise HTTPException(status_code=409, detail='Email already in use')
        except Exception as ex:
            logger.error(f'Verify mail error {ex}')
            raise ex
#Tested
class UserRegisterRepository:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.p_hash = PasswordHash()

    async def register(self, register_data: UserRegisterSchema):

            logger.info('New Register working')

            await VerifyEmail.verify_email(self.db, register_data)
            data = await self.save_user_database(register_data)
            return data

    async def save_user_database(self, register_data: UserRegisterSchema) -> UserResponseSchema:
        try:
            middle_name = None
            if register_data.middle_name:
                middle_name = register_data.middle_name.strip().lower()

            new_user = UserModel(
                first_name=register_data.first_name.strip().lower(),
                middle_name=middle_name,
                last_name=register_data.last_name.strip().lower(),
                email=register_data.email.strip().lower(),
                password=self.p_hash.hash_password(register_data.password.strip()),
                project_id=register_data.project_id,
                is_admin=register_data.is_admin,
                role_id=register_data.role_id,
            )

            self.db.add(new_user)
            await self.db.flush()
            await self.db.refresh(new_user)
            await self.db.commit()
            return UserResponseSchema.model_validate(new_user)
        except Exception as ex:
            await self.db.rollback()
            logger.error(f'New user registered error {ex}')
            raise HTTPException(status_code=400, detail="Failed to create user. Please try again.")

# Tested
class CreateProjectRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_project(self, project_data: ProjectCreateSchema):

        await self.verify_code_name(project_data)

        try:
            new_project = ProjectModel( **project_data.model_dump())

            self.db.add(new_project)
            await self.db.flush()
            await self.db.refresh(new_project)
            await self.db.commit()
            return ProjectResponseSchema.model_validate(new_project)
        except Exception as ex:
            raise HTTPException(status_code=409, detail = f"Create Project Error {ex}")

    async def verify_code_name(self, project_data: ProjectCreateSchema) -> None:
        data = await self.db.execute(select(ProjectModel).where(
            or_(
                ProjectModel.project_name == project_data.project_name.strip().upper(),
                ProjectModel.project_code == project_data.project_code.strip().upper(),
            )
        ))
        res = data.scalar()
        if res:
            logger.debug(f'{project_data.project_code} or {project_data.project_name} was already registered')
            raise HTTPException(status_code=409, detail="Project name or Project code was already registered")

# Tested
class CreateGroupRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_group(self, group_data: GroupCreateSchema):
        await self.verify_group_name(group_data.group_name)

        new_group = GroupModel(
            group_name = group_data.group_name.strip().lower(),
        )

        self.db.add(new_group)
        await self.db.flush()
        await self.db.refresh(new_group)
        await self.db.commit()
        return GroupResponseSchema.model_validate(new_group)

    async def verify_group_name(self, group_name: str) -> None:
        try:
            data = await self.db.execute(select(exists().where(GroupModel.group_name == group_name.strip().lower())))
            res = data.scalar()
            if res:
                logger.error(f'{group_name} Group name exists')
                raise HTTPException(status_code=409, detail="Group name exists")
        except Exception as ex:
            raise ex



# Tested
class CreateCategoryRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_category(self, category_data: CategoryCreateSchema):
        await self.verify_category_name(category_data.category_name)

        new_category = MaterialCategoryModel(
            category_name = category_data.category_name.strip().upper(),
        )

        self.db.add(new_category)
        await self.db.flush()
        await self.db.refresh(new_category)
        await self.db.commit()
        return CategoryResponseSchema.model_validate(new_category)

    async def verify_category_name(self, category_name: str) -> None:
        try:
            data = await self.db.execute(select(exists().where(MaterialCategoryModel.category_name == category_name.strip().upper())))
            res = data.scalar()
            if res:
                logger.error(f'{category_name} category name exists')
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{category_name} name exists")
        except Exception as ex:
            raise ex
