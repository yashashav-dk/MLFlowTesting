"""
Unit Tests for ML API
=====================

Tests cover:
1. Model training and prediction
2. API endpoints (health, predict, metrics)
3. Input validation
4. Error handling

PYTEST OVERVIEW:
----------------
- Functions starting with test_ are automatically discovered
- Fixtures (functions with @pytest.fixture) provide reusable setup
- Use assert statements to verify expected behavior

Run tests with: pytest -v
Run with coverage: pytest --cov=. --cov-report=html
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import IrisClassifier, IRIS_CLASSES


# =============================================================================
# FIXTURES - Reusable test setup
# =============================================================================


@pytest.fixture(scope="module")
def trained_model():
    """
    Fixture that provides a trained model.

    scope="module" means this runs once per test file,
    not once per test function (faster).
    """
    model = IrisClassifier()
    model.train()
    return model


@pytest.fixture(scope="module")
def client():
    """
    Fixture that provides a FastAPI test client.

    TestClient lets us make HTTP requests to our API
    without actually running a server.

    Using context manager ensures lifespan events (startup/shutdown) are triggered.
    """
    # Import here to avoid circular imports
    from app import app

    # Use context manager to trigger lifespan events (startup loads the model)
    with TestClient(app) as test_client:
        yield test_client


# =============================================================================
# MODEL TESTS
# =============================================================================


class TestIrisClassifier:
    """Tests for the IrisClassifier model."""

    def test_train_returns_accuracy(self, trained_model):
        """Training should return an accuracy score."""
        # Iris is easy - accuracy should be high
        assert trained_model.accuracy > 0.9
        assert trained_model.is_trained is True

    def test_predict_returns_valid_class(self, trained_model):
        """Predictions should be one of the known classes."""
        # Typical setosa measurements
        features = [5.1, 3.5, 1.4, 0.2]
        predicted_class, probabilities = trained_model.predict(features)

        assert predicted_class in IRIS_CLASSES
        assert len(probabilities) == 3
        assert sum(probabilities) == pytest.approx(1.0, rel=1e-5)

    def test_predict_setosa(self, trained_model):
        """Test prediction for setosa (small petals)."""
        # Setosa has small petals (length < 2, width < 0.5)
        features = [5.0, 3.4, 1.5, 0.2]
        predicted_class, probs = trained_model.predict(features)

        assert predicted_class == "setosa"
        assert max(probs) > 0.8  # Should be confident

    def test_predict_versicolor(self, trained_model):
        """Test prediction for versicolor (medium petals)."""
        # Versicolor has medium-sized petals
        features = [6.0, 2.7, 4.5, 1.5]
        predicted_class, probs = trained_model.predict(features)

        assert predicted_class == "versicolor"

    def test_predict_virginica(self, trained_model):
        """Test prediction for virginica (large petals)."""
        # Virginica has large petals (length > 5, width > 1.8)
        features = [6.7, 3.0, 5.5, 2.1]
        predicted_class, probs = trained_model.predict(features)

        assert predicted_class == "virginica"

    def test_predict_without_training_raises_error(self):
        """Prediction without training should raise RuntimeError."""
        model = IrisClassifier()
        # Don't train

        with pytest.raises(RuntimeError, match="not trained"):
            model.predict([5.0, 3.0, 1.5, 0.2])

    def test_evaluate_returns_score(self, trained_model):
        """Evaluate should return accuracy between 0 and 1."""
        accuracy = trained_model.evaluate()

        assert 0.0 <= accuracy <= 1.0
        assert accuracy > 0.9  # Should be good on iris


# =============================================================================
# API ENDPOINT TESTS
# =============================================================================


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self, client):
        """Health check should return 200 OK."""
        response = client.get("/health")

        assert response.status_code == 200

    def test_health_response_format(self, client):
        """Health response should have expected fields."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "model_loaded" in data
        assert "model_accuracy" in data
        assert data["status"] == "healthy"
        assert data["model_loaded"] is True


class TestPredictEndpoint:
    """Tests for the /predict endpoint."""

    def test_predict_valid_input(self, client):
        """Valid input should return prediction."""
        response = client.post(
            "/predict",
            json={
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "predicted_class" in data
        assert "confidence" in data
        assert "probabilities" in data
        assert data["predicted_class"] in IRIS_CLASSES

    def test_predict_missing_field(self, client):
        """Missing required field should return 422."""
        response = client.post(
            "/predict",
            json={
                "sepal_length": 5.1,
                # Missing sepal_width, petal_length, petal_width
            },
        )

        assert response.status_code == 422  # Validation error

    def test_predict_invalid_value(self, client):
        """Invalid values should return 422."""
        response = client.post(
            "/predict",
            json={
                "sepal_length": -1.0,  # Can't be negative
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2,
            },
        )

        assert response.status_code == 422

    def test_predict_response_probabilities_sum_to_one(self, client):
        """Probabilities should sum to 1."""
        response = client.post(
            "/predict",
            json={
                "sepal_length": 6.0,
                "sepal_width": 3.0,
                "petal_length": 4.0,
                "petal_width": 1.2,
            },
        )

        data = response.json()
        prob_sum = sum(data["probabilities"].values())

        assert prob_sum == pytest.approx(1.0, rel=1e-5)


class TestMetricsEndpoint:
    """Tests for the /metrics endpoint."""

    def test_metrics_returns_200(self, client):
        """Metrics endpoint should return 200 OK."""
        response = client.get("/metrics")

        assert response.status_code == 200

    def test_metrics_format(self, client):
        """Metrics should be in Prometheus format."""
        response = client.get("/metrics")

        # Prometheus format has specific content type
        assert "text/plain" in response.headers.get("content-type", "")

        # Should contain our custom metrics
        content = response.text
        assert "http_requests_total" in content or "ml_predictions_total" in content

    def test_metrics_after_prediction(self, client):
        """Metrics should update after making predictions."""
        # Make a prediction first
        client.post(
            "/predict",
            json={
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2,
            },
        )

        # Check metrics
        response = client.get("/metrics")
        content = response.text

        # Should have prediction metrics
        assert "ml_predictions_total" in content


class TestRootEndpoint:
    """Tests for the / endpoint."""

    def test_root_returns_info(self, client):
        """Root should return API info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestIntegration:
    """Integration tests that exercise multiple components."""

    def test_multiple_predictions(self, client):
        """Should handle multiple predictions correctly."""
        test_cases = [
            {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2,
            },
            {
                "sepal_length": 6.0,
                "sepal_width": 2.7,
                "petal_length": 4.5,
                "petal_width": 1.5,
            },
            {
                "sepal_length": 6.7,
                "sepal_width": 3.0,
                "petal_length": 5.5,
                "petal_width": 2.1,
            },
        ]

        for case in test_cases:
            response = client.post("/predict", json=case)
            assert response.status_code == 200
            assert response.json()["predicted_class"] in IRIS_CLASSES

    def test_api_docs_accessible(self, client):
        """Swagger docs should be accessible."""
        response = client.get("/docs")

        # FastAPI redirects /docs to the actual docs page
        assert response.status_code in [200, 307]
