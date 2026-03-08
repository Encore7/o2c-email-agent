from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import get_settings
from app.db.session import init_db
from app.observability import (
    PrometheusHttpMiddleware,
    RequestLoggingMiddleware,
    configure_json_logging,
    metrics_response,
    setup_tracing,
    shutdown_tracing,
)

settings = get_settings()
configure_json_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(settings.postgres_dsn)
    tracer_provider = setup_tracing(
        app=app,
        enabled=settings.otel_enabled,
        service_name=settings.otel_service_name,
        service_version=settings.app_version,
        environment=settings.otel_environment,
        otlp_endpoint=settings.otel_exporter_otlp_endpoint,
        exporter_insecure=settings.otel_exporter_insecure,
    )
    yield
    shutdown_tracing(tracer_provider)


app = FastAPI(title=settings.app_name, lifespan=lifespan)
if settings.metrics_enabled:
    app.add_middleware(PrometheusHttpMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_v1_prefix)

if settings.metrics_enabled:
    app.add_api_route("/metrics", metrics_response, methods=["GET"], include_in_schema=False)
