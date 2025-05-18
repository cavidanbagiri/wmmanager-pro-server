from datetime import datetime

from pydantic import BaseModel, field_validator

from src.constants.constants import Units, Currency

class WarehouseSchema(BaseModel):
    material_name: str
    qty: float
    unit: Units
    price: float | None = None
    currency: Currency | None = None
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


class WarehouseUpdateSchema(BaseModel):
    id:int
    material_name: str
    qty: float
    unit: Units
    price: float | None = None
    currency: Currency | None = None
    po_num: str | None = None
    doc_num: str | None = None
    category_id: int
    material_code_id: int
    project_id: int
    ordered_id: int
    company_id: int


class WarehouseListSelectByIDS(BaseModel):

    ids: list[int]

class WarehouseStandartFetchResponseSchema(BaseModel):
    id:int
    material_name: str
    qty: float
    left_over: float
    unit: str
    price: float | None = None
    currency: Currency | None = None
    created_at: datetime
    material_code: dict
    category: str
    project: dict
    ordered: dict
    company: dict


class WarehouseFilterFieldSchema(BaseModel):
    material_name: str | None = None
    qty: float | None = None
    unit: Units | None = None
    price: float | None = None
    currency: Currency | None = None
    category_id: int | None = None
    po_num: str | None = None
    doc_num: str | None = None
    material_code_id: int | None = None
    project_id: int | None = None
    ordered_id: int | None = None
    company_id: int | None = None
    created_at: datetime | None = None

class WarehouseFilterSchema(BaseModel):
    project_id: int
    filter_data: WarehouseFilterFieldSchema