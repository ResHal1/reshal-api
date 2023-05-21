import uuid
from decimal import Decimal
from typing import Optional

from pydantic import Field, validator

from reshal_api.base import ORJSONBaseModel
from reshal_api.facility.schemas import FacilityReadBase


def duration_more_than_30_min(v: int) -> int:
    if v < 1800:
        raise ValueError(
            "Invalid time frame duration. Time frame duration must be at least 30 minutes."
        )
    return v


def price_more_than_0(v: float) -> float:
    if v < 0:
        raise ValueError("Price must be > 0")
    return v


#  timeframe


class TimeFrameBase(ORJSONBaseModel):
    facility_id: uuid.UUID
    duration: int = Field(description="Time in seconds")
    price: Decimal


class TimeFrameReadBase(TimeFrameBase):
    id: uuid.UUID

    class Config:
        orm_mode = True


class TimeFrameRead(TimeFrameBase):
    id: uuid.UUID
    facility: FacilityReadBase

    class Config:
        orm_mode = True


class TimeFrameCreate(TimeFrameBase):
    ...

    _validate_duration = validator("duration", allow_reuse=True)(
        duration_more_than_30_min
    )
    _validate_price = validator("price", allow_reuse=True)(price_more_than_0)


class TimeFrameUpdate(ORJSONBaseModel):
    duration: Optional[int] = Field(None, description="Time in seconds")
    price: Optional[float]

    _validate_duration = validator("duration", allow_reuse=True)(
        duration_more_than_30_min
    )
    _validate_price = validator("price", allow_reuse=True)(price_more_than_0)
