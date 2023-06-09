import uuid
from decimal import Decimal
from typing import Optional

from pydantic import AnyHttpUrl, validator

from reshal_api.auth.schemas import UserRead
from reshal_api.base import ORJSONBaseModel

# Facility Image


class FacilityImageBase(ORJSONBaseModel):
    facility_id: uuid.UUID


class FacilityImageRead(FacilityImageBase):
    id: uuid.UUID
    path: str

    class Config:
        orm_mode = True


class FacilityImageCreate(FacilityImageBase):
    ...


class FacilityImageUpdate(FacilityImageBase):
    ...


# Facility Role


class FacilityTypeBase(ORJSONBaseModel):
    name: str

    class Config:
        orm_mode = True


class FacilityTypeRead(FacilityTypeBase):
    id: uuid.UUID


class FacilityTypeCreate(FacilityTypeBase):
    ...


class FacilityTypeUpdate(FacilityTypeBase):
    ...


# Facility


def validate_lat(value: float) -> float:
    if not -90 <= value <= 90:
        raise ValueError("Latitude must be between -90 and 90")
    return value


def validate_lon(value: float) -> float:
    if not -180 <= value <= 180:
        raise ValueError("Longitude must be between -180 and 180")
    return value


class FacilityBase(ORJSONBaseModel):
    name: str
    description: Optional[str]
    lat: float
    lon: float
    address: str
    price: Decimal
    image_url: AnyHttpUrl

    class Config:
        orm_mode = True

    _validate_lat = validator("lat", allow_reuse=True)(validate_lat)
    _validate_lon = validator("lon", allow_reuse=True)(validate_lon)


class FacilityReadBase(FacilityBase):
    id: uuid.UUID


class FacilityRead(FacilityReadBase):
    type: FacilityTypeRead


class FacilityReadAdmin(FacilityRead):
    type_id: uuid.UUID
    owners: list[UserRead]


class FacilityCreate(FacilityBase):
    type_id: uuid.UUID


class FacilityUpdate(FacilityBase):
    name: Optional[str]
    description: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    address: Optional[str]
    price: Optional[Decimal]
    image_url: Optional[AnyHttpUrl]
    type_id: Optional[uuid.UUID]

    _validate_lat = validator("lat", allow_reuse=True)(validate_lat)
    _validate_lon = validator("lon", allow_reuse=True)(validate_lon)


class FacilityOwnership(ORJSONBaseModel):
    user_id: uuid.UUID
    facility_id: uuid.UUID
