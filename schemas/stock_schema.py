from typing import List

from pydantic import BaseModel


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


class StockListResponse(BaseModel):
    id: int
    material_name: str
    quantity: float
    left_over: float
    serial_number: str | None = None
    material_id: str | None = None
    description: str
    category: str
    project: str
    ordered: str
    company: str

class StockListSelectByIDS(BaseModel):

    ids: list[int]