from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, field_validator


class AreaAddSchema(BaseModel):
    quantity: float
    serial_number: str | None = None
    material_id: str | None = None
    provide_type: str
    stock_id: int
    project_id: int

    @field_validator('provide_type')
    @classmethod
    def validate_provide_type(cls, v: str):
        return v.lower()

    class Config:
        from_attributes = True

class AreaListAddSchema(BaseModel):
    project_id: int
    card_number: str
    username: str = Field(min_length=2)
    group_id: int

    datas: List[AreaAddSchema]

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str):
        return v.lower()

    class Config:
        from_attributes = True


class AreaResponseSchema(BaseModel):
    id: int
    material_name: str
    quantity: float
    serial_number: str | None
    material_id: str | None
    username: str
    provide_type: str
    project_name: str
    card_number: str
    created_at: datetime
    group_name: str
    stock_id: int
    project_id: int


class AreaReturnStockSchema(BaseModel):

    id: int
    stock_id: int
    quantity: float
    project_id: int