"""
ML API Application
==================

FastAPI application that serves our Iris classifier with Prometheus metrics.

FASTAPI OVERVIEW:
-----------------
FastAPI is a modern Python web framework that:
- Auto-generates API documentation (Swagger UI at /docs)
- Validates request/response data with Pydantic
- Supports async/await for high performance
- Type hints = auto-completion and validation

PROMETHEUS INTEGRATION:
-----------------------
We expose metrics at /metrics endpoint that Prometheus scrapes.
The prometheus_client library handles the heavy lifting.
"""

import time
from contextlib import asynccontextmanager
from typing import Dict, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field, ConfigDict
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# Our custom modules
from model import get_model, IRIS_CLASSES
from metrics import (
    init_metrics,
    HTTP_REQUESTS_TOTAL,
    REQUEST_LATENCY,
    PREDICTIONS_TOTAL,
    PREDICTION_LATENCY,
    PREDICTION_ERRORS,
    MODEL_ACCURACY
)

# =============================================================================
# PYDANTIC MODELS (Request/Response Schemas)
# =============================================================================
# Pydantic models define the shape of data and validate it automatically

class PredictionRequest(BaseModel):
    """
    Request body for /predict endpoint.

    Field() lets us add validation and documentation:
    - gt = greater than
    - lt = less than
    - description shows up in Swagger docs
    """
    sepal_length: float = Field(
        ...,  # ... means required
        gt=0, lt=10,
        description="Sepal length in cm (typically 4.3-7.9)"
    )
    sepal_width: float = Field(
        ...,
        gt=0, lt=10,
        description="Sepal width in cm (typically 2.0-4.4)"
    )
    petal_length: float = Field(
        ...,
        gt=0, lt=10,
        description="Petal length in cm (typically 1.0-6.9)"
    )
    petal_width: float = Field(
        ...,
        gt=0, lt=5,
        description="Petal width in cm (typically 0.1-2.5)"
    )

    # Model configuration using ConfigDict (Pydantic v2 style)
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
        }
    )


class PredictionResponse(BaseModel):
    """Response body for /predict endpoint."""
    predicted_class: str = Field(
        description="Predicted iris species"
    )
    confidence: float = Field(
        description="Confidence score (0-1)"
    )
    probabilities: Dict[str, float] = Field(
        description="Probability for each class"
    )


class HealthResponse(BaseModel):
    """Response body for /health endpoint."""
    status: str
    model_loaded: bool
    model_accuracy: float


# =============================================================================
# APPLICATION LIFECYCLE
# =============================================================================

# Global model instance (loaded at startup)
model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.

    Code before 'yield' runs at startup.
    Code after 'yield' runs at shutdown.

    This is the modern way to handle startup/shutdown in FastAPI.
    """
    global model

    # STARTUP
    print("=" * 50)
    print("Starting ML API...")
    print("=" * 50)

    # Initialize Prometheus metrics
    init_metrics()

    # Load or train the ML model
    model = get_model()

    # Update accuracy metric
    MODEL_ACCURACY.labels(model='iris_classifier').set(model.accuracy)

    print(f"Model ready! Accuracy: {model.accuracy:.2%}")
    print("=" * 50)

    yield  # Application runs here

    # SHUTDOWN
    print("Shutting down ML API...")


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="Iris Classifier API",
    description="""
    A simple ML API that classifies iris flowers.

    ## Features
    - **Predict**: Classify iris species from measurements
    - **Metrics**: Prometheus metrics for monitoring
    - **Health**: Health check endpoint

    ## The Iris Dataset
    Classic ML dataset with 3 species: setosa, versicolor, virginica
    """,
    version="1.0.0",
    lifespan=lifespan
)


# =============================================================================
# MIDDLEWARE (runs on every request)
# =============================================================================

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """
    Middleware to track metrics for every HTTP request.

    WHAT IS MIDDLEWARE?
    Middleware wraps around your endpoints. It can:
    - Modify requests before they reach endpoints
    - Modify responses before they're sent
    - Track timing, add headers, handle errors, etc.

    This middleware:
    1. Records start time
    2. Lets the request proceed (call_next)
    3. Records metrics (latency, status, etc.)
    """
    # Skip metrics endpoint to avoid recursive tracking
    if request.url.path == "/metrics":
        return await call_next(request)

    # Record start time
    start_time = time.time()

    # Process the request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Record metrics
    # Labels let us slice data: http_requests_total{method="POST", endpoint="/predict"}
    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()  # Increment counter by 1

    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)  # Record value in histogram

    return response


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint.

    Used by:
    - Docker health checks
    - Kubernetes readiness/liveness probes
    - Load balancers
    - Monitoring systems

    Returns model status and accuracy.
    """
    return HealthResponse(
        status="healthy",
        model_loaded=model is not None and model.is_trained,
        model_accuracy=model.accuracy if model else 0.0
    )


@app.get("/metrics", tags=["System"])
async def metrics():
    """
    Prometheus metrics endpoint.

    Prometheus scrapes this endpoint at regular intervals (configured in prometheus.yml).
    The prometheus_client library formats metrics in Prometheus text format.

    Example output:
    ```
    # HELP http_requests_total Total number of HTTP requests
    # TYPE http_requests_total counter
    http_requests_total{method="POST",endpoint="/predict",status="200"} 42.0
    ```
    """
    return Response(
        content=generate_latest(),  # Generate prometheus format
        media_type=CONTENT_TYPE_LATEST  # text/plain with special charset
    )


@app.post("/predict", response_model=PredictionResponse, tags=["ML"])
async def predict(request: PredictionRequest):
    """
    Make a prediction for iris flower classification.

    Takes 4 measurements and returns:
    - Predicted species (setosa, versicolor, virginica)
    - Confidence score
    - Probability for each class

    ## Example

    ```bash
    curl -X POST http://localhost:8000/predict \\
      -H "Content-Type: application/json" \\
      -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'
    ```
    """
    if model is None:
        # Track error metric
        PREDICTION_ERRORS.labels(
            model='iris_classifier',
            error_type='model_not_loaded'
        ).inc()
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Time the prediction
        start_time = time.time()

        # Make prediction
        features = [
            request.sepal_length,
            request.sepal_width,
            request.petal_length,
            request.petal_width
        ]
        predicted_class, probabilities = model.predict(features)

        # Record prediction latency
        duration = time.time() - start_time
        PREDICTION_LATENCY.labels(model='iris_classifier').observe(duration)

        # Record prediction count (by class for distribution analysis)
        PREDICTIONS_TOTAL.labels(
            model='iris_classifier',
            predicted_class=predicted_class
        ).inc()

        # Build response
        return PredictionResponse(
            predicted_class=predicted_class,
            confidence=max(probabilities),  # Highest probability
            probabilities={
                name: prob
                for name, prob in zip(IRIS_CLASSES, probabilities)
            }
        )

    except Exception as e:
        # Track error
        PREDICTION_ERRORS.labels(
            model='iris_classifier',
            error_type=type(e).__name__
        ).inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Iris Classifier API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # This runs when you execute: python app.py
    # In production, use: uvicorn app:app --host 0.0.0.0 --port 8000
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
