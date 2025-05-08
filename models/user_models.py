
from sqlalchemy import String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base_model import Base

class Role(Base):
    __tablename__ = 'roles'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(20), unique=True) # /Manager/Head/Staff/Worker
    description: Mapped[str] = mapped_column(String(100))

class Permission(Base):
    __tablename__ = 'permissions'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(20), unique=True) # /inventory:create/inventory:update/inventory:delete/

class RolePermission(Base):
    __tablename__ = 'role_permissions'
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id'), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey('permission.id'), primary_key=True)


class UserModel(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(40), nullable=False)
    middle_name: Mapped[str] = mapped_column(String(40), nullable=True)
    last_name: Mapped[str] = mapped_column(String(40), nullable=False)
    email: Mapped[str] = mapped_column(String(40), nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)  # Added String length
    is_admin: Mapped[bool] = mapped_column(default=False)
    profile_image: Mapped[str] = mapped_column(String(255), nullable=True)  # Added String length
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id'))

    # Corrected foreign key and string reference
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'))  # Fixed table name
    project = relationship("ProjectModel", back_populates='users')
    role = relationship('Role')

    def __str__(self):
        return f"id:{self.id} /first_name:{self.first_name} /last_name:{self.last_name} /email:{self.email} /is_admin:{self.is_admin} /project_id:{self.project_id} /role_id:{self.role_id}"


class TokenModel(Base):
    __tablename__ = 'tokens'

    id: Mapped[int] = mapped_column(primary_key=True)

    tokens: Mapped[str] = mapped_column(String)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    def __str__(self):
        return f"{self.id} {self.tokens} {self.user_id}"