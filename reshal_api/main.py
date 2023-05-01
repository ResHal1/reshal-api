from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from reshal_api.auth.router import router as auth_router
from reshal_api.config import CORSSettings, UvicornSettings, get_config
from reshal_api.facility.router import router as facility_router
from reshal_api.lifespan import lifespan
from reshal_api.reservation.router import router as reservation_router
from reshal_api.timeframe.router import router as timeframe_router
from reshal_api.payment.router import router as payment_router

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
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")
app.include_router(auth_router, prefix="/auth")
app.include_router(facility_router, prefix="/facilities")
app.include_router(reservation_router, prefix="/reservations")
app.include_router(timeframe_router, prefix="/timeframes")
app.include_router(payment_router, prefix="/payments")


@app.get("/")
async def home():
    return {"message": "Reshal API"}


def run():
    import uvicorn

    uvicorn.run("reshal_api.main:app", **UvicornSettings().dict())


if __name__ == "__main__":
    run()
