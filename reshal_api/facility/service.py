import uuid
from typing import Any, Sequence

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from reshal_api.auth.models import User
from reshal_api.base import BaseCRUDService

from .file_manager import LocalFileManager
from .models import Facility, FacilityImage
from .schemas import (
    FacilityCreate,
    FacilityImageCreate,
    FacilityImageUpdate,
    FacilityUpdate,
)


class FacilityService(BaseCRUDService[Facility, FacilityCreate, FacilityUpdate]):
    def __init__(self) -> None:
        super().__init__(Facility)

    async def get_facilities_by_owner_id(
        self, session: AsyncSession, owner_id: uuid.UUID
    ) -> Sequence[Facility]:
        q = select(Facility).join(Facility.owners).where(User.id == owner_id)
        facilities = (await session.scalars(q)).all()
        return facilities


class FacilityImageService(
    BaseCRUDService[FacilityImage, FacilityImageCreate, FacilityImageUpdate]
):
    def __init__(self) -> None:
        super().__init__(FacilityImage)
        self.file_manager = LocalFileManager()

    async def create(
        self,
        session: AsyncSession,
        create_obj: FacilityImageCreate,
        file: UploadFile,
    ) -> FacilityImage:
        file_id = str(uuid.uuid4())
        file_path = await self.file_manager.save(
            file, file_id, directory_name=str(create_obj.facility_id)
        )
        try:
            create_obj_dict = dict(create_obj)
            create_obj_dict["path"] = file_path
            facility_image = await super().create(session, create_obj_dict)
        except Exception:
            await self.file_manager.delete(file_path)
            raise Exception
        else:
            return facility_image

    async def delete(
        self,
        session: AsyncSession,
        *args,
        db_obj: FacilityImage | None = None,
        image_path: str,
        **kwargs,
    ) -> None:
        await super().delete(session, *args, db_obj=db_obj, **kwargs)
        await self.file_manager.delete(image_path)

    async def delete_all_for_facility(
        self, session: AsyncSession, facility_id: str
    ) -> None:
        images = await session.stream_scalars(
            select(FacilityImage).where(FacilityImage.facility_id == facility_id)
        )

        async for image in images:
            await self.delete(session, db_obj=image, image_path=image.path)

    async def update(
        self,
        session: AsyncSession,
        *,
        update_obj: FacilityImageUpdate | dict[str, Any],
        db_obj: FacilityImage | None = None,
        **kwargs,
    ) -> None:
        raise NotImplementedError("FacilityImage cannot be updated")
