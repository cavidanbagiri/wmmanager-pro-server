
from datetime import datetime

from sqlalchemy import ForeignKey, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base_model import Base

class AreaModel(Base):

    __tablename__ = 'area'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    quantity: Mapped[float] = mapped_column(nullable=False)
    serial_number: Mapped[str] = mapped_column(String(20), nullable=True)
    material_id: Mapped[str] = mapped_column(String(20), nullable=True)
    provide_type: Mapped[str] = mapped_column(String(20), nullable=False)
    card_number: Mapped[str] = mapped_column(String(10), nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    created_by_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    stock_id: Mapped[int] = mapped_column(ForeignKey('stock.id'))
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), default=1)
    group_id: Mapped[int] = mapped_column(ForeignKey('groups.id'))

    stock = relationship("StockModel")
    group = relationship("GroupModel")
    project = relationship("ProjectModel")

    def __str__(self):
        return f"{self.id} {self.quantity} {self.serial_number} {self.material_id} {self.stock_id}"

