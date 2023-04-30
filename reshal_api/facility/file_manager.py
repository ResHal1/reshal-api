import os
from abc import ABC, abstractmethod

import aiofiles
from fastapi import UploadFile

from reshal_api.config import get_config

config = get_config()


class BaseFileManager(ABC):
    @abstractmethod
    async def get(self, name: str) -> str:
        ...

    @abstractmethod
    async def save(self, file: UploadFile, name: str) -> str:
        ...

    @abstractmethod
    async def delete(self, path: str) -> None:
        ...


class LocalFileManager(BaseFileManager):
    async def get(self, name: str):
        raise NotImplementedError()

    async def save(self, file: UploadFile, name: str, *, directory_name: str) -> str:
        dir_path = os.path.join(config.STATIC_DIR, directory_name)
        os.makedirs(dir_path, exist_ok=True)
        filename = f"{os.path.join(dir_path, name)}.jpg"
        async with aiofiles.open(filename, mode="wb") as f:
            await f.write((await file.read()))
        return filename

    async def delete(self, path: str) -> None:
        os.remove(path)
