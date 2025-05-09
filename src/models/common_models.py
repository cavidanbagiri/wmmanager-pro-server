
from sqlalchemy import String, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base_model import Base

class ProjectModel(Base):
    __tablename__ = 'projects'

    id: Mapped[int] = mapped_column(primary_key=True)
    project_name: Mapped[str] = mapped_column(String(40), nullable=False)
    project_code: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    users = relationship("UserModel", back_populates='project')

    def __str__(self):
        return f'{self.id} {self.project_code} {self.project_name}'


class CompanyModel(Base):

    __tablename__ = 'companies'

    id: Mapped[int] = mapped_column(primary_key=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(40), nullable=True)
    email: Mapped[str] = mapped_column(String(40), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(40), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    created_by_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

    def __str__(self):
        return f'{self.id} {self.company_name}'