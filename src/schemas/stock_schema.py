from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel

Units = Literal["pcs","ton","kg","pallet","box","case","each","roll","meter","liter","gallon","pack","bundle","drum","carton","bag","sheet","pair","set"]


class StockAddSchema(BaseModel):

    quantity: float
    serial_number: str | None = None
    material_id: str | None = None
    warehouse_id: int
    project_id: int

    class Config:
        from_attributes = True



class StockListRequest(BaseModel):
    project_id: int
    stock_data_list: List[StockAddSchema]


class StockStandardFetchResponse(BaseModel):
    id: int
    material_name: str
    quantity: float
    left_over: float
    serial_number: str | None = None
    material_id: str | None = None
    material_code: dict
    category: dict
    project: dict
    ordered: dict
    company: dict

class StockListSelectByIDS(BaseModel):

    ids: list[int]


class StockReturnToWarehouseSchema(BaseModel):
    id: int
    warehouse_id: int
    quantity: float
    project_id: int


class StockFilterFieldSchema(BaseModel):
    material_name: str | None = None
    quantity: float | None = None
    unit: Units | None = None
    price: float | None = None
    currency: str | None = None
    category_id: int | None = None
    po_num: str | None = None
    doc_num: str | None = None
    material_code_id: int | None = None
    project_id: int | None = None
    ordered_id: int | None = None
    company_id: int | None = None
    created_at: datetime | None = None
    serial_number: str | None = None
    material_id: str | None = None


class StockFilterSchema(BaseModel):
    project_id: int
    filter_data: StockFilterFieldSchema