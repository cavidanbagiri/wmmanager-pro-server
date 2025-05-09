from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator


Units = Literal["pcs","ton","kg","pallet","box","case","each","roll","meter","liter","gallon","pack","bundle","drum","carton","bag","sheet","pair","set"]


class WarehouseSchema(BaseModel):
    material_name: str
    qty: float
    unit: Units
    price: float | None = None
    currency: str
    material_code_id: int
    category_id: int

    @field_validator('unit')
    @classmethod
    def validate_unit(cls, val: str):
        val = val.lower()
        valid_units = Units.__args__
        if val in valid_units:
            return val
        raise ValueError(f'{val} is not available in Units list.')


class WarehouseListCreateSchema(BaseModel):

    po_num: str | None = None
    doc_num: str | None = None
    project_id: int
    ordered_id: int
    company_id: int

    data_list: list[WarehouseSchema]



class WarehouseListSelectByIDS(BaseModel):

    ids: list[int]

class WarehouseListSelectByIDSResponse(BaseModel):
    id:int
    qty: float
    left_over: float
    unit: str
    price: float | None = None
    currency: str | None = None
    created_at: datetime
    project: str
    ordered: str
    company: str
    category: str
    material_code: str
