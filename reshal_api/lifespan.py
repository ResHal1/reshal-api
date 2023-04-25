from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import async_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await async_engine.dispose()
