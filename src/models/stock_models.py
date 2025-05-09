
from datetime import datetime

from sqlalchemy import DateTime, String, func, ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column

from src.models import Base

class StockModel(Base):
    
    __tablename__ = "stock"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    quantity: Mapped[float] = mapped_column(nullable=False)
    left_over: Mapped[float] = mapped_column(nullable=False)
    serial_number: Mapped[str] = mapped_column(String(20), nullable=True)
    material_id: Mapped[str] = mapped_column(String(20), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default = func.now()) 
    
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouse.id"), nullable=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)

    warehouses = relationship("WarehouseModel")
    project = relationship("ProjectModel")

    def __str__(self):
        return f"id: {self.id} / quantity: {self.quantity} / leftover: {self.left_over} / serial_num {self.serial_number} / material_id: {self.material_id} "


