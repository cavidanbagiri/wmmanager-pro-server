from sqlalchemy import String, func, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base_model import Base


class MaterialCategoryModel(Base):

    __tablename__ = 'categories'
    id: Mapped[int] = mapped_column(primary_key=True, unique=True, autoincrement=True)
    category_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


    def __str__(self):
        return f'{self.id} {self.category_name}'


class MaterialCodeModel(Base):

    __tablename__ = 'material_codes'
    id: Mapped[int] = mapped_column(primary_key=True, unique=True, autoincrement=True)
    code_num: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    created_by_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

    def __str__(self):
        return f'{self.id} {self.code_num} {self.description}'


class WarehouseModel(Base):

    __tablename__ = 'warehouse'

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, autoincrement=True)
    material_name: Mapped[str] = mapped_column(Text, nullable=False)
    qty: Mapped[float] = mapped_column(nullable=False)
    left_over: Mapped[float] = mapped_column(nullable=False)
    unit: Mapped[str] = mapped_column( nullable=False)
    price: Mapped[float] = mapped_column(nullable=True)
    currency: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    po_num: Mapped[str] = mapped_column(String, nullable=True)
    doc_num: Mapped[str] = mapped_column(String, nullable=True)

    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), nullable=False)
    material_code_id: Mapped[int] = mapped_column(ForeignKey('material_codes.id'), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'), nullable=False)
    ordered_id: Mapped[int] = mapped_column(ForeignKey('ordered.id'), nullable=True)
    company_id: Mapped[int] = mapped_column(ForeignKey('companies.id'), nullable=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

    ordered = relationship("OrderedModel")
    category = relationship("MaterialCategoryModel")
    project = relationship("ProjectModel")
    material_code = relationship("MaterialCodeModel")
    company = relationship("CompanyModel")
    stocks = relationship("StockModel", back_populates="warehouses")


    def __str__(self):
        return f'{self.id} {self.material_name} {self.qty}'
