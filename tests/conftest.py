import asyncio

import httpx
import pytest

from reshal_api.main import app


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
async def client():
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client
