from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from reshal_api.database import get_db_session
from reshal_api.exceptions import NotFound

from .service import FacilityImageService, FacilityService


async def get_facility_image_service() -> FacilityImageService:
    return FacilityImageService()


async def get_facility_service() -> FacilityService:
    return FacilityService()


async def facility_exists(
    facility_id: str,
    session: AsyncSession = Depends(get_db_session),
    facility_service: FacilityService = Depends(get_facility_service),
):
    facility = await facility_service.get(session, id=facility_id)
    if facility is None:
        raise NotFound("Facility not found")
    return facility


async def facility_image_exists(
    facility_image_id: str,
    session: AsyncSession = Depends(get_db_session),
    facility_image_service: FacilityImageService = Depends(get_facility_image_service),
):
    facility_image = await facility_image_service.get(session, id=facility_image_id)
    if facility_image is None:
        raise NotFound("Facility image not found")
    return facility_image
