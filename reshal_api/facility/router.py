import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
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
from reshal_api.exceptions import BadRequest, Conflict, Forbidden, NotFound
from reshal_api.reservation.dependencies import (
    ReservationService,
    get_reservation_service,
)
from reshal_api.reservation.schemas import ReservationReadBase  # noqa: F401

from .dependencies import (
    facility_exists,
    get_facility_image_service,
    get_facility_service,
    get_facility_type_service,
)
from .models import Facility, FacilityImage  # noqa: F401
from .schemas import (
    FacilityCreate,
    FacilityOwnership,
    FacilityRead,
    FacilityReadAdmin,
    FacilityTypeCreate,
    FacilityTypeRead,
    FacilityUpdate,
)
from .service import FacilityImageService, FacilityService, FacilityTypeService

router = APIRouter(tags=["facility"])


@router.get("", response_model=list[FacilityRead])
async def get_facilities(
    session: AsyncSession = Depends(get_db_session),
    facility_service: FacilityService = Depends(get_facility_service),
):
    facilities = await facility_service.get_all(session)
    return facilities


@router.get("/types", response_model=list[FacilityTypeRead], tags=["facility-type"])
async def get_facility_types(
    session: AsyncSession = Depends(get_db_session),
    types_service: FacilityTypeService = Depends(get_facility_type_service),
):
    types = await types_service.get_all(session)
    return types


@router.post(
    "/types",
    status_code=status.HTTP_201_CREATED,
    response_model=FacilityTypeRead,
    tags=["facility-type"],
    dependencies=[Depends(get_admin)],
)
async def create_facility_type(
    data: FacilityTypeCreate,
    session: AsyncSession = Depends(get_db_session),
    types_service: FacilityTypeService = Depends(get_facility_type_service),
):
    if await types_service.type_name_exists(session, data.name):
        raise Conflict(detail=f"Facility type {data.name!r} already exists")

    facility_type = await types_service.create(session, data)
    return facility_type


@router.delete(
    "/types/{type_id}", tags=["facility-type"], dependencies=[Depends(get_admin)]
)
async def delete_facility_type(
    type_id: str,
    session: AsyncSession = Depends(get_db_session),
    types_service: FacilityTypeService = Depends(get_facility_type_service),
):
    await types_service.delete(session, id=type_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
    "/assign-ownership",
    response_model=FacilityReadAdmin,
    dependencies=[Depends(get_admin)],
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

    await facility_service.add_owner(session, facility, user)
    await session.refresh(user)
    await session.refresh(facility, ["owners"])

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

    if not facility.is_owner(user.id):
        raise BadRequest(detail="User is not an owner of this facility")
    await facility_service.remove_owner(session, facility, user)

    return Response(status_code=status.HTTP_200_OK)


# @router.get("/{facility_id}/images", response_model=list[FacilityImageRead])
# async def get_facility_images(
#     facility_id: str,
#     session: AsyncSession = Depends(get_db_session),
#     facility: Facility = Depends(facility_exists),
#     facility_image_service: FacilityImageService = Depends(get_facility_image_service),
# ):
#     images = await facility_image_service.get_all(session, facility_id=facility_id)
#     return images


@router.get("/{facility_id}/reservations")
async def get_reservations_for_facility(
    facility_id: str,
    session: AsyncSession = Depends(get_db_session),
    facility: Facility = Depends(facility_exists),
):
    await session.refresh(facility, ["reservations"])
    return facility.reservations


# @router.post(
#     "/{facility_id}/images",
#     status_code=status.HTTP_201_CREATED,
#     response_model=list[FacilityImageRead],
# )
# async def add_facility_images(
#     facility_id: str,
#     images: list[UploadFile],
#     session: AsyncSession = Depends(get_db_session),
#     facility: Facility = Depends(facility_exists),
#     facility_image_service: FacilityImageService = Depends(get_facility_image_service),
# ):
#     db_imgs = []
#     for image in images:
#         facility_image = await facility_image_service.create(
#             session, FacilityImageCreate(facility_id=uuid.UUID(facility_id)), image
#         )
#         db_imgs.append(facility_image)

#     return db_imgs


# @router.delete(
#     "/{facility_id}/images/{facility_image_id}",
#     status_code=status.HTTP_204_NO_CONTENT,
#     dependencies=[Depends(get_owner)],
# )
# async def delete_facility_image(
#     facility_id: str,
#     facility_image_id: str,
#     session: AsyncSession = Depends(get_db_session),
#     facility: Facility = Depends(facility_exists),
#     facility_image: FacilityImage = Depends(facility_image_exists),
#     facility_image_service: FacilityImageService = Depends(get_facility_image_service),
# ):
#     await facility_image_service.delete(
#         session, db_obj=facility_image, image_path=facility_image.path
#     )
#     return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{facility_id}", response_model=FacilityRead)
async def get_facility_by_id(
    facility_id: str,
    facility: Facility = Depends(facility_exists),
):
    return facility


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=FacilityRead,
    dependencies=[Depends(get_admin)],
)
async def create_facility(
    data: FacilityCreate,
    session: AsyncSession = Depends(get_db_session),
    facility_service: FacilityService = Depends(get_facility_service),
    types_service: FacilityTypeService = Depends(get_facility_type_service),
):
    if not bool(await types_service.get(session, id=data.type_id)):
        raise BadRequest(detail="Facility type not found")

    facility = await facility_service.create(session, data)
    await session.refresh(facility, ["owners", "type", "images"])
    return facility


@router.put("/{facility_id}", response_model=FacilityRead)
async def update_facility(
    data: FacilityUpdate,
    session: AsyncSession = Depends(get_db_session),
    facility_service: FacilityService = Depends(get_facility_service),
    facility: Facility = Depends(facility_exists),
    types_service: FacilityTypeService = Depends(get_facility_type_service),
    user: User = Depends(get_user),
):
    if data.type_id and not bool(await types_service.get(session, id=data.type_id)):
        raise BadRequest(detail="Facility type not found")

    if user.role != UserRole.admin and not facility.is_owner(user.id):
        raise Forbidden()

    data_dict = data.dict(exclude_unset=True)

    if data_dict.get("images", False):
        facility.images = [
            FacilityImage(path=image["path"]) for image in data_dict["images"]
        ]
        del data_dict["images"]

    updated_facility = await facility_service.update(
        session, db_obj=facility, update_obj=data_dict
    )

    return updated_facility


@router.delete(
    "/{facility_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_admin)],
)
async def delete_facility(
    facility_id: str,
    # background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
    facility_service: FacilityService = Depends(get_facility_service),
    reservation_service: ReservationService = Depends(get_reservation_service)
    # facility_image_service: FacilityImageService = Depends(get_facility_image_service),
):
    if facility := await facility_service.get(session, id=facility_id):
        if not await reservation_service.reservations_in_future_exist(
            session, facility_id
        ):
            await facility_service.delete(session, db_obj=facility)
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "msg": "Could not delete this facility, there are upcoming reservations"
                },
            )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
