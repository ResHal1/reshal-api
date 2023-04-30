import uuid
from typing import Optional

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


# Facility


class FacilityBase(ORJSONBaseModel):
    name: str
    description: Optional[str]
    location: str
    address: str
    public: bool

    class Config:
        orm_mode = True


class FacilityRead(FacilityBase):
    id: uuid.UUID
    owners: list[UserRead]
    images: list[FacilityImageRead]


class FacilityCreate(FacilityBase):
    ...


class FacilityUpdate(FacilityBase):
    name: Optional[str]
    description: Optional[str]
    location: Optional[str]
    address: Optional[str]
    public: Optional[bool]


class FacilityOwnership(ORJSONBaseModel):
    user_id: uuid.UUID
    facility_id: uuid.UUID
    facility_id: uuid.UUID
