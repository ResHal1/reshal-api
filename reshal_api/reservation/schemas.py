import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytz
from pydantic import Field, root_validator, validator

from reshal_api.base import ORJSONBaseModel
from reshal_api.payment.schemas import PaymentRead

# from reshal_api.timeframe.schemas import TimeFrameRead

# Reservation


class ReservationCreateBase(ORJSONBaseModel):
    facility_id: uuid.UUID
    # timeframe_id: uuid.UUID
    start_time: datetime
    end_time: datetime

    @validator("start_time", "end_time")
    def time_to_utc(cls, v: datetime) -> datetime:
        return v.replace(tzinfo=pytz.timezone("UTC"))

    @validator("start_time", "end_time")
    def time_must_be_in_future(cls, v: datetime) -> datetime:
        if v < datetime.now().replace(tzinfo=pytz.timezone("UTC")):
            raise ValueError(f"{v} must be in the future.")
        return v

    @root_validator(skip_on_failure=True)
    def check_end_time(cls, values: dict) -> dict:
        start_time = values.get("start_time")
        end_time = values.get("end_time")
        if start_time and end_time:
            if start_time >= end_time:
                raise ValueError("End time must be after start time.")
        return values

    @root_validator(skip_on_failure=True)
    def reservation_duration_is_atleast_30_min_and_not_more_than_24_hours(
        cls, values: dict
    ) -> dict:
        start_time = values.get("start_time")
        end_time = values.get("end_time")

        if start_time and end_time:
            duration = end_time - start_time
            if duration < timedelta(minutes=30):
                raise ValueError("Reservation must be at least 30 minutes long.")

            if duration > timedelta(hours=24):
                raise ValueError("Reservation must not be longer than 24 hours.")
        return values


class ReservationCreate(ReservationCreateBase):
    price: Decimal
    payment_id: uuid.UUID
    user_id: uuid.UUID
    end_time: datetime

    @validator("end_time")
    def end_time_to_utc(cls, v: datetime) -> datetime:
        return v.replace(tzinfo=pytz.timezone("UTC"))

    @root_validator
    def check_end_time(cls, values):
        start_time = values.get("start_time")
        end_time = values.get("end_time")
        if start_time and end_time:
            if start_time >= end_time:
                raise ValueError("End time must be after start time.")
        return values


class ReservationReadBase(ORJSONBaseModel):
    id: uuid.UUID
    facility_id: uuid.UUID
    price: str = Field(..., min_length=1)
    # timeframe_id: uuid.UUID
    user_id: uuid.UUID
    start_time: datetime
    end_time: datetime

    class Config:
        orm_mode = True


class ReservationRead(ReservationReadBase):
    payment_id: uuid.UUID

    # timeframe: TimeFrameRead
    payment: PaymentRead

    class Config:
        orm_mode = True


class ReservationUpdate(ORJSONBaseModel):
    ...
