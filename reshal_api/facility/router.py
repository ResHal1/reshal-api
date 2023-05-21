import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from reshal_api.auth.dependencies import (
    get_admin,
    get_auth_service,
    get_owner,
    get_user,
)
from reshal_api.auth.models import User, UserRole
from reshal_api.auth.service import AuthService
from reshal_api.database import get_db_session
from reshal_api.exceptions import Conflict, Forbidden, NotFound
from reshal_api.reservation.schemas import ReservationReadBase

from .dependencies import (
    facility_exists,
    facility_image_exists,
    get_facility_image_service,
    get_facility_service,
)
from .models import Facility, FacilityImage
from .schemas import (
    FacilityCreate,
    FacilityImageCreate,
    FacilityImageRead,
    FacilityOwnership,
    FacilityRead,
    FacilityReadAdmin,
    FacilityUpdate,
)
from .service import FacilityImageService, FacilityService

router = APIRouter(tags=["facility"])


@router.get("/", response_model=list[FacilityRead])
async def get_facilities(
    session: AsyncSession = Depends(get_db_session),
    facility_service: FacilityService = Depends(get_facility_service),
):
    facilities = await facility_service.get_all(session)
    return facilities


# TODO: change name
@router.get(
    "/admin", response_model=list[FacilityReadAdmin], dependencies=[Depends(get_admin)]
)
async def get_facilities_admin(
    session: AsyncSession = Depends(get_db_session),
    facility_service: FacilityService = Depends(get_facility_service),
):
    facilities = await facility_service.get_all(session)
    return facilities


@router.get("/me", response_model=list[FacilityRead])
async def get_facilities_me(
    session: AsyncSession = Depends(get_db_session),
    facility_service: FacilityService = Depends(get_facility_service),
    user: User = Depends(get_owner),
):
    facilities = await facility_service.get_facilities_by_owner_id(session, user.id)
    return facilities


@router.post(
    "/assign-ownership", response_model=FacilityRead, dependencies=[Depends(get_admin)]
)
async def assign_facility_ownership(
    data: FacilityOwnership,
    session: AsyncSession = Depends(get_db_session),
    facility_service: FacilityService = Depends(get_facility_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    facility = await facility_service.get(session, id=data.facility_id)
    user = await auth_service.get_by_id(session, data.user_id)
    if facility is None or user is None:
        raise NotFound()

    if facility.is_owner(user.id):
        raise Conflict(detail="User already has ownership")

    facility.owners.append(user)

    return facility


@router.delete(
    "/revoke-ownership",
    dependencies=[Depends(get_admin)],
)
async def revoke_facility_ownership(
    data: FacilityOwnership,
    session: AsyncSession = Depends(get_db_session),
    facility_service: FacilityService = Depends(get_facility_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    facility = await facility_service.get(session, id=data.facility_id)
    user = await auth_service.get_by_id(session, data.user_id)
    if facility is None or user is None:
        raise NotFound()

    if facility.is_owner(user.id):
        facility.owners.remove(user)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{facility_id}/images", response_model=list[FacilityImageRead])
async def get_facility_images(
    facility_id: str,
    session: AsyncSession = Depends(get_db_session),
    facility: Facility = Depends(facility_exists),
    facility_image_service: FacilityImageService = Depends(get_facility_image_service),
):
    images = await facility_image_service.get_all(session, facility_id=facility_id)
    return images


@router.get("/{facility_id}/reservations", response_model=list[ReservationReadBase])
async def get_reservations_for_facility(
    facility_id: str,
    session: AsyncSession = Depends(get_db_session),
    facility: Facility = Depends(facility_exists),
):
    await session.refresh(facility, ["reservations"])
    return facility.reservations


@router.post(
    "/{facility_id}/images",
    status_code=status.HTTP_201_CREATED,
    response_model=list[FacilityImageRead],
)
async def add_facility_images(
    facility_id: str,
    images: list[UploadFile],
    session: AsyncSession = Depends(get_db_session),
    facility: Facility = Depends(facility_exists),
    facility_image_service: FacilityImageService = Depends(get_facility_image_service),
):
    db_imgs = []
    for image in images:
        facility_image = await facility_image_service.create(
            session, FacilityImageCreate(facility_id=uuid.UUID(facility_id)), image
        )
        db_imgs.append(facility_image)

    return db_imgs


@router.delete(
    "/{facility_id}/images/{facility_image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_owner)],
)
async def delete_facility_image(
    facility_id: str,
    facility_image_id: str,
    session: AsyncSession = Depends(get_db_session),
    facility: Facility = Depends(facility_exists),
    facility_image: FacilityImage = Depends(facility_image_exists),
    facility_image_service: FacilityImageService = Depends(get_facility_image_service),
):
    await facility_image_service.delete(
        session, db_obj=facility_image, image_path=facility_image.path
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{facility_id}", response_model=FacilityRead)
async def get_facility_by_id(
    facility_id: str,
    facility: Facility = Depends(facility_exists),
    user: User = Depends(get_owner),
):
    if user.role != UserRole.admin and not facility.is_owner(user.id):
        raise Forbidden()
    return facility


@router.post("/", response_model=FacilityRead, dependencies=[Depends(get_admin)])
async def create_facility(
    data: FacilityCreate,
    session: AsyncSession = Depends(get_db_session),
    facility_service: FacilityService = Depends(get_facility_service),
):
    facility = await facility_service.create(session, data)
    await session.refresh(facility, ["owners", "images"])
    return facility


@router.put("/{facility_id}", response_model=FacilityRead)
async def update_facility(
    data: FacilityUpdate,
    session: AsyncSession = Depends(get_db_session),
    facility_service: FacilityService = Depends(get_facility_service),
    facility: Facility = Depends(facility_exists),
    user: User = Depends(get_user),
):
    """multipart/form-data"""
    if user.role != UserRole.admin and not facility.is_owner(user.id):
        raise Forbidden()
    updated_facility = await facility_service.update(
        session, db_obj=facility, update_obj=data
    )

    return updated_facility


@router.delete(
    "/{facility_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_admin)],
)
async def delete_facility(
    facility_id: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
    facility_service: FacilityService = Depends(get_facility_service),
    facility_image_service: FacilityImageService = Depends(get_facility_image_service),
):
    await facility_image_service.delete_all_for_facility(session, facility_id)
    await facility_service.delete(session, id=facility_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
