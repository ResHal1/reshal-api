import logging
from contextlib import asynccontextmanager
from logging import LogRecord

from fastapi import FastAPI

from .database import async_engine


class EndpointFilter(logging.Filter):
    def __init__(self, *args, path: str, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._path = path

    def filter(self, record: LogRecord) -> bool:
        return record.getMessage().find(self._path) == -1


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger("uvicorn.access").addFilter(EndpointFilter(path="/metrics"))
    yield
    await async_engine.dispose()
