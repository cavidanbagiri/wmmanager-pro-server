from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field, field_validator

Units = Literal["pcs","ton","kg","pallet","box","case","each","roll","meter","liter","gallon","pack","bundle","drum","carton","bag","sheet","pair","set"]

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
    unit: Units
    serial_number: str | None
    material_id: str | None
    username: str
    provide_type: str
    card_number: str
    created_at: datetime
    group: dict
    project: dict
    stock: dict
    category: dict


class AreaReturnStockSchema(BaseModel):

    id: int
    stock_id: int
    quantity: float
    project_id: int



class AreaFilterFieldSchema(BaseModel):
    material_name: str | None = None
    quantity: float | None = None
    unit: Units | None = None
    serial_number: str | None = None
    material_id: str | None = None
    username: str | None = None
    provide_type: str | None = None
    project_name: str | None = None
    card_number: str | None = None
    created_at: datetime | None = None
    group_id: int | None = None
    stock_id: int | None = None
    project_id: int | None = None
    category_id: int | None = None


class AreaFilterSchema(BaseModel):
    project_id: int
    filter_data: AreaFilterFieldSchema