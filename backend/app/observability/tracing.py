from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_tracing(
    *,
    app,
    enabled: bool,
    service_name: str,
    service_version: str,
    environment: str,
    otlp_endpoint: str,
    exporter_insecure: bool,
) -> TracerProvider | None:
    if not enabled:
        return None

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
            "deployment.environment": environment,
        }
    )
    tracer_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=exporter_insecure,
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)
    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)
    return tracer_provider


def shutdown_tracing(tracer_provider: TracerProvider | None) -> None:
    if tracer_provider is None:
        return
    tracer_provider.shutdown()
