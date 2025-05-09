from sqlalchemy import String, func, DateTime, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base_model import Base

class GroupModel(Base):

    __tablename__ = 'groups'
    id: Mapped[int] = mapped_column(primary_key=True, unique=True, autoincrement=True)
    group_name: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ordered = relationship('OrderedModel', back_populates='group')

    def __str__(self):
        return f'{self.id} {self.group_name}'


class OrderedModel(Base):

    __tablename__ = 'ordered'

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, autoincrement=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    f_name: Mapped[str] = mapped_column(String(30), nullable=False)
    m_name: Mapped[str] = mapped_column(String(30), nullable=True)
    l_name: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(30), nullable=True)
    group_id: Mapped[int] = mapped_column(ForeignKey('groups.id'), nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), nullable=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

    group = relationship('GroupModel', back_populates='ordered')

    @hybrid_property
    def username(self)->str:
        if self.m_name:
            return self.f_name + ' ' + self.m_name + ' ' + self.l_name
        return f"{self.f_name} {self.l_name}"

    def __str__(self):
        return f'{self.id} {self.f_name} {self.l_name} {self.email}'
