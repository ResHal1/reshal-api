from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from reshal_api.config import CORSSettings, UvicornSettings, get_config
from reshal_api.lifespan import lifespan

config = get_config()

app = FastAPI(
    lifespan=lifespan,
    title=config.TITLE,
    version=config.VERSION,
    root_path=config.ROOT_PATH,
    debug=config.ENVIRONMENT.is_local,
    docs_url=None if config.ENVIRONMENT.is_production else "/docs",
    redocs_url=None if config.ENVIRONMENT.is_production else "/docs",
    openapi_url=None if config.ENVIRONMENT.is_production else "/openapi.json",
)

app.add_middleware(CORSMiddleware, **CORSSettings().dict())


@app.get("/")
async def home():
    return {"message": "Reshal API"}


def run():
    import uvicorn

    uvicorn.run("reshal_api.main:app", **UvicornSettings().dict())


if __name__ == "__main__":
    run()
