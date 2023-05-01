"""
Contains base classes for models, services, services, and dependencies
"""

from datetime import datetime
from typing import Any, Generic, Optional, Sequence, TypeVar

import humps
import orjson
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.base import ExecutableOption

# ORJSONBaseModel


def orjson_dumps(v, *, default):
    """
    orjson.dumps() returns bytes; decode to match standard json.dumps()
    """
    return orjson.dumps(v, default=default).decode()


class ORJSONBaseModel(BaseModel):
    """
    Custom BaseModel that uses `orjson` for serialization/deserialization
    and `pyhumps` for camelCase field names
    """

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps
        alias_generator = humps.camelize
        allow_population_by_field_name = True


class TimestampSchema(BaseModel):
    created_at: datetime
    updated_at: datetime


# Generic CRUD Service


ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=ORJSONBaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=ORJSONBaseModel)


class BaseCRUDService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: type[ModelType]) -> None:
        self._model = model

    def _create_query(self, options: Optional[list[ExecutableOption]] = None):
        """Create a query with the given options"""
        q = select(self._model)
        if options:
            q = q.options(*options)
        return q

    async def create(
        self,
        session: AsyncSession,
        create_obj: CreateSchemaType | dict[str, Any],
    ) -> ModelType:
        if isinstance(create_obj, dict):
            create_obj_dict = create_obj
        else:
            create_obj_dict = dict(create_obj)
        db_obj = self._model(**create_obj_dict)
        session.add(db_obj)
        await session.flush()

        return db_obj

    async def get(
        self,
        session: AsyncSession,
        *args,
        options: Optional[list[ExecutableOption]] = None,
        **kwargs
    ) -> Optional[ModelType]:
        """Return first result that matches the given filters"""
        q = self._create_query(options)

        result = await session.execute(q.filter(*args).filter_by(**kwargs))

        return result.scalars().first()

    async def get_many(
        self,
        session: AsyncSession,
        *args,
        offset: int = 0,
        limit: int = 100,
        options: Optional[list[ExecutableOption]] = None,
        **kwargs
    ) -> Sequence[ModelType]:
        """Return a list of results that match the given filters"""
        q = self._create_query(options)
        result = await session.execute(
            q.filter(*args).filter_by(**kwargs).offset(offset).limit(limit)
        )

        return result.scalars().all()

    async def get_all(
        self,
        session: AsyncSession,
        *args,
        options: Optional[list[ExecutableOption]] = None,
        **kwargs
    ) -> Sequence[ModelType]:
        """Return a list of all results that match the given filters"""
        q = self._create_query(options)
        result = await session.execute(q.filter(*args).filter_by(**kwargs))

        return result.scalars().all()

    async def update(
        self,
        session: AsyncSession,
        *,
        update_obj: UpdateSchemaType | dict[str, Any],
        db_obj: Optional[ModelType] = None,
        **kwargs
    ) -> Optional[ModelType]:
        db_obj = db_obj or await self.get(session, **kwargs)
        if db_obj:
            if isinstance(update_obj, dict):
                update_data = update_obj
            else:
                update_data = update_obj.dict(exclude_unset=True)

            for field in update_data:
                setattr(db_obj, field, update_data[field])

            session.add(db_obj)
            await session.flush()

        return db_obj

    async def delete(
        self, session: AsyncSession, *args, db_obj: Optional[ModelType] = None, **kwargs
    ) -> Optional[ModelType]:
        db_obj = db_obj or await self.get(session, *args, **kwargs)
        if db_obj:
            await session.delete(db_obj)
        return db_obj
