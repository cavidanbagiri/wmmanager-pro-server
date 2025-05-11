

from sqlalchemy import DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base_model import Base

class LogStockMovementModel(Base):

    __tablename__ = 'log_stock_movement'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    movement_type: Mapped[str] = mapped_column()
    old_quantity: Mapped[float] = mapped_column()
    old_left_over: Mapped[float] = mapped_column()
    return_quantity: Mapped[float] = mapped_column()
    new_left_over: Mapped[float] = mapped_column()
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    stock_id: Mapped[int] = mapped_column(ForeignKey('stock.id'), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey('warehouse.id'), nullable=False)

    created_by_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)


class LogAreaMovementModel(Base):

    __tablename__ = 'log_area_movement'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    movement_type: Mapped[str] = mapped_column()
    old_quantity: Mapped[float] = mapped_column()
    return_quantity: Mapped[float] = mapped_column()

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    area_id: Mapped[int] = mapped_column(ForeignKey('area.id'), nullable=False)
    stock_id: Mapped[int] = mapped_column(ForeignKey('stock.id'), nullable=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

class LogUpdateWarehouseQtyModel(Base):

    __tablename__ = 'log_warehouse_movement'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    movement_type: Mapped[str] = mapped_column()
    old_quantity: Mapped[float] = mapped_column()
    old_left_over: Mapped[float] = mapped_column()
    new_quantity: Mapped[float] = mapped_column()
    new_left_over: Mapped[float] = mapped_column()
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    warehouse_id: Mapped[int] = mapped_column(ForeignKey('warehouse.id'), nullable=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)