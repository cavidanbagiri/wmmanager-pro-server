
from src.models.base_model import Base

from src.models.warehouse_model import WarehouseModel
from src.schemas.user_schemas import UserTokenSchema


class ProjectVerify:
    def __init__(self,
                user_payload: UserTokenSchema,
                model: type[Base] = WarehouseModel):

        self.model = model
        self.user_payload = user_payload

    def get_project_filter(self):

        if self.user_payload.get('project_id') == 1:
            return True
        return self.model.project_id == self.user_payload.get('project_id')