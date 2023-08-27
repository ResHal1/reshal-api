# import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles

from reshal_api.auth.router import router as auth_router
from reshal_api.config import CORSSettings, UvicornSettings, get_config
from reshal_api.facility.router import router as facility_router
from reshal_api.lifespan import lifespan
from reshal_api.opentelemetry import PrometheusMiddleware, metrics, setup_otlp
from reshal_api.payment.router import router as payment_router
from reshal_api.reservation.router import router as reservation_router

# from reshal_api.timeframe.router import router as timeframe_router

config = get_config()

app = FastAPI(
    lifespan=lifespan,
    title=config.TITLE,
    version=config.VERSION,
    root_path=config.ROOT_PATH,
    debug=config.ENVIRONMENT.is_local,
    default_response_class=ORJSONResponse,
    docs_url=None if config.ENVIRONMENT.is_production else "/docs",
    redocs_url=None if config.ENVIRONMENT.is_production else "/docs",
    openapi_url=None if config.ENVIRONMENT.is_production else "/openapi.json",
)


if not config.ENVIRONMENT.is_testing:
    app.add_middleware(PrometheusMiddleware, app_name=config.OTLP_APP_NAME)
    setup_otlp(app, config.OTLP_APP_NAME, config.OTLP_GRPC_ENDPOINT)

app.add_middleware(CORSMiddleware, **CORSSettings().dict())
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")
app.include_router(auth_router, prefix="/auth")
app.include_router(facility_router, prefix="/facilities")
app.include_router(reservation_router, prefix="/reservations")
# app.include_router(timeframe_router, prefix="/timeframes")
app.include_router(payment_router, prefix="/payments")


app.add_route("/metrics", metrics)


@app.get("/")
async def home():
    return {"message": "Reshal API"}


def run():
    import uvicorn
    from uvicorn import config as uvicorn_config

    log_config = uvicorn_config.LOGGING_CONFIG
    log_config["formatters"]["access"][
        "fmt"
    ] = "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s resource.service.name=%(otelServiceName)s] - %(message)s"

    uvicorn.run(
        "reshal_api.main:app", **UvicornSettings().dict(), log_config=log_config
    )


if __name__ == "__main__":
    run()
