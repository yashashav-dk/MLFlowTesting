"""
Prometheus Metrics Setup
========================

This module sets up all the Prometheus metrics we want to track.

CONCEPTS:
---------
Prometheus has different metric types:

1. Counter: Only goes up (like a car odometer)
   - Use for: total requests, errors, predictions made

2. Gauge: Can go up or down (like a speedometer)
   - Use for: current temperature, active connections, accuracy

3. Histogram: Measures distributions (buckets of values)
   - Use for: request latency, response sizes

4. Summary: Similar to histogram but calculates percentiles
   - Use for: when you need precise percentiles

Labels let you slice metrics:
- predictions_total{model="iris", result="setosa"} = 42
- predictions_total{model="iris", result="versicolor"} = 38
"""

from prometheus_client import Counter, Histogram, Gauge, Info

# =============================================================================
# APPLICATION INFO
# =============================================================================
# Info metric - static labels about your app (version, git commit, etc.)
APP_INFO = Info(
    "ml_api",  # Metric name
    "Information about the ML API application",  # Description (shows in /metrics)
)

# =============================================================================
# REQUEST METRICS
# =============================================================================
# Counter for all HTTP requests
# Labels let us filter: http_requests_total{method="POST", endpoint="/predict", status="200"}
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],  # These become label keys
)

# Histogram for request latency
# Buckets define the ranges we care about (in seconds)
# .005 = 5ms, .01 = 10ms, etc.
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# =============================================================================
# ML-SPECIFIC METRICS
# =============================================================================
# Counter for predictions made
# We track by predicted class to see distribution
PREDICTIONS_TOTAL = Counter(
    "ml_predictions_total",
    "Total number of ML predictions made",
    ["model", "predicted_class"],
)

# Histogram for prediction latency (just the model inference time)
PREDICTION_LATENCY = Histogram(
    "ml_prediction_duration_seconds",
    "Time spent making ML predictions",
    ["model"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

# Gauge for model accuracy (can go up or down as we evaluate)
MODEL_ACCURACY = Gauge(
    "ml_model_accuracy", "Current accuracy of the ML model", ["model"]
)

# Counter for prediction errors
PREDICTION_ERRORS = Counter(
    "ml_prediction_errors_total",
    "Total number of failed predictions",
    ["model", "error_type"],
)


def init_metrics():
    """
    Initialize metrics with default values.

    Called at startup to ensure metrics exist in Prometheus
    even before any requests are made. This helps with:
    - Dashboard queries not failing on startup
    - Rate calculations working immediately
    """
    # Set application info
    APP_INFO.info(
        {"version": "1.0.0", "model": "iris_classifier", "framework": "fastapi"}
    )

    # Initialize model accuracy (will be updated after evaluation)
    MODEL_ACCURACY.labels(model="iris_classifier").set(0.0)
