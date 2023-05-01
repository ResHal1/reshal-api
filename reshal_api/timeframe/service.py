from reshal_api.base import BaseCRUDService

from .models import TimeFrame
from .schemas import TimeFrameCreate, TimeFrameUpdate


class TimeFrameService(BaseCRUDService[TimeFrame, TimeFrameCreate, TimeFrameUpdate]):
    def __init__(self) -> None:
        super().__init__(TimeFrame)
