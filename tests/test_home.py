from httpx import AsyncClient


async def test_home(client: AsyncClient):
    res = await client.get("")
    assert res.status_code == 200
    assert res.json() == {"message": "Reshal API"}
