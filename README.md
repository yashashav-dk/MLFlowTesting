# Learn CI/CD, Grafana, Prometheus & ML

A hands-on learning project that ties together monitoring, visualization, CI/CD pipelines, and a simple ML workload. Everything runs locally with Docker Compose.

## What You'll Learn

| Technology | What It Does |
|------------|--------------|
| **Prometheus** | Collects and stores metrics (time-series database) |
| **Grafana** | Visualizes metrics with dashboards |
| **GitHub Actions** | Automates testing and deployment (CI/CD) |
| **FastAPI** | Serves the ML model as an API |
| **Docker Compose** | Runs all services together |

## Quick Start

```bash
# Start all services
docker-compose up -d

# Wait for startup, then access:
# - ML API:     http://localhost:8000
# - API Docs:   http://localhost:8000/docs
# - Prometheus: http://localhost:9090
# - Grafana:    http://localhost:3000 (admin/admin)

# Make a prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'

# Stop everything
docker-compose down
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Compose                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    scrapes     ┌─────────────────────┐    │
│  │  Prometheus │◄───metrics─────│  ML API (FastAPI)   │    │
│  │  :9090      │                │  :8000              │    │
│  └──────┬──────┘                │  - /predict         │    │
│         │                       │  - /metrics         │    │
│         │ queries               │  - /health          │    │
│         ▼                       └─────────────────────┘    │
│  ┌─────────────┐                                           │
│  │   Grafana   │                                           │
│  │   :3000     │                                           │
│  │  Dashboards │                                           │
│  └─────────────┘                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
.
├── README.md                           # This file
├── docker-compose.yml                  # Orchestrates all services
├── .github/
│   └── workflows/
│       └── ci.yml                      # GitHub Actions CI pipeline
├── ml_api/
│   ├── Dockerfile                      # Container definition
│   ├── requirements.txt                # Python dependencies
│   ├── app.py                          # FastAPI application
│   ├── model.py                        # Iris classifier
│   ├── metrics.py                      # Prometheus instrumentation
│   └── tests/
│       └── test_app.py                 # Unit tests
├── prometheus/
│   └── prometheus.yml                  # Scrape configuration
└── grafana/
    └── provisioning/
        ├── datasources/
        │   └── prometheus.yml          # Data source config
        └── dashboards/
            ├── dashboard.yml           # Dashboard provisioning
            └── ml_dashboard.json       # Pre-built dashboard
```

---

## Concepts Deep Dive

### 1. Prometheus (Metrics & Monitoring)

**What is it?**
Prometheus is a time-series database designed for monitoring. It stores metrics with timestamps, allowing you to track how things change over time.

**How it works:**
- Prometheus "pulls" (scrapes) metrics from your applications
- Your app exposes a `/metrics` endpoint in a special text format
- Prometheus stores data and lets you query it with PromQL

**Metric Types:**
```
# Counter - only goes up (like an odometer)
http_requests_total{method="POST", endpoint="/predict"} 42

# Gauge - can go up or down (like a speedometer)
ml_model_accuracy{model="iris"} 0.967

# Histogram - distribution of values (latency buckets)
http_request_duration_seconds_bucket{le="0.1"} 100
http_request_duration_seconds_bucket{le="0.5"} 150
```

**Example PromQL queries:**
```promql
# Request rate over last 5 minutes
rate(http_requests_total[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
```

### 2. Grafana (Visualization)

**What is it?**
Grafana is a visualization platform. It connects to data sources (like Prometheus) and displays data as graphs, gauges, and tables.

**Key Concepts:**
- **Data Source**: Where data comes from (Prometheus, InfluxDB, etc.)
- **Dashboard**: Collection of panels showing related metrics
- **Panel**: A single visualization (graph, stat, table, etc.)
- **Query**: PromQL expression that fetches data

**Our Dashboard includes:**
- Total predictions count
- Predictions per minute
- Model accuracy
- Latency percentiles (p50, p95, p99)
- Error rate
- Request breakdown by endpoint

### 3. CI/CD (Continuous Integration/Deployment)

**Continuous Integration (CI):**
Every time you push code:
1. **Lint** - Check code style (ruff)
2. **Test** - Run unit tests (pytest)
3. **Build** - Build Docker image

**Continuous Deployment (CD):**
After CI passes:
1. Push Docker image to registry
2. Deploy to production

**Our GitHub Actions Pipeline:**
```yaml
push → lint → test → build → integration test
```

### 4. The ML Model

**Dataset: Iris Flowers**
- 150 samples of iris flowers
- 4 features: sepal length/width, petal length/width
- 3 classes: setosa, versicolor, virginica

**Why Iris?**
- Simple enough to understand
- Complex enough to be interesting
- Built into scikit-learn (no download needed)
- Perfect for learning ML + monitoring

---

## Step-by-Step Tutorial

### Step 1: Start the Services

```bash
docker-compose up -d --build
```

This builds and starts:
- `ml-api` - FastAPI app on port 8000
- `prometheus` - Metrics database on port 9090
- `grafana` - Dashboards on port 3000

### Step 2: Explore the ML API

Open http://localhost:8000/docs to see the Swagger UI.

**Health Check:**
```bash
curl http://localhost:8000/health
# {"status":"healthy","model_loaded":true,"model_accuracy":0.9666...}
```

**Make Predictions:**
```bash
# Setosa (small petals)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'

# Versicolor (medium petals)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"sepal_length": 6.0, "sepal_width": 2.7, "petal_length": 4.5, "petal_width": 1.5}'

# Virginica (large petals)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"sepal_length": 6.7, "sepal_width": 3.0, "petal_length": 5.5, "petal_width": 2.1}'
```

**View Raw Metrics:**
```bash
curl http://localhost:8000/metrics
```

### Step 3: Explore Prometheus

Open http://localhost:9090

**Check Targets:**
Navigate to Status → Targets. You should see `ml-api` with state "UP".

**Run Queries:**
In the query box, try:
```promql
# Total predictions
ml_predictions_total

# Request rate
rate(http_requests_total[1m])

# Model accuracy
ml_model_accuracy
```

### Step 4: Explore Grafana

Open http://localhost:3000 (login: admin/admin)

The "ML API Dashboard" is pre-loaded. You'll see:
- Overview stats (predictions, latency, accuracy)
- Prediction rate by class
- Latency percentiles over time
- HTTP request breakdown

**Generate Some Traffic:**
```bash
# Make 100 predictions to see the graphs move
for i in {1..100}; do
  curl -s -X POST http://localhost:8000/predict \
    -H "Content-Type: application/json" \
    -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}' > /dev/null
  sleep 0.1
done
```

### Step 5: Run Tests Locally

```bash
cd ml_api
pip install -r requirements.txt
pytest tests/ -v
```

### Step 6: CI/CD Pipeline

Push to GitHub and watch the Actions tab:
1. **Lint** - ruff checks code style
2. **Test** - pytest runs unit tests
3. **Build** - Docker image is built
4. **Integration** - Full stack is tested

---

## Common Tasks

### Rebuild After Code Changes
```bash
docker-compose up -d --build
```

### View Logs
```bash
docker-compose logs -f           # All services
docker-compose logs -f ml-api    # Just ML API
```

### Stop Everything
```bash
docker-compose down      # Keep data volumes
docker-compose down -v   # Delete data volumes
```

### Add a New Metric

In `metrics.py`:
```python
MY_METRIC = Counter('my_metric_total', 'Description', ['label1'])
```

In `app.py`:
```python
MY_METRIC.labels(label1='value').inc()
```

### Add to Dashboard

1. Open Grafana → ML API Dashboard
2. Click "Add" → "Visualization"
3. Write your PromQL query
4. Save dashboard

---

## Troubleshooting

### Prometheus shows "DOWN" for ml-api
- Check if ml-api is running: `docker-compose ps`
- Check ml-api logs: `docker-compose logs ml-api`
- Verify /metrics endpoint: `curl http://localhost:8000/metrics`

### Grafana shows "No data"
- Prometheus needs data before graphs work
- Make some predictions first
- Check time range (top-right) is recent

### Docker build fails
- Check Docker is running: `docker ps`
- Clear cache: `docker-compose build --no-cache`

### Tests fail
- Install dependencies: `pip install -r ml_api/requirements.txt`
- Check Python version (needs 3.11+)

---

## Next Steps

1. **Add Alerting**: Configure Prometheus alerts for high error rates
2. **Slack Notifications**: Connect Grafana alerts to Slack
3. **Model Retraining**: Add endpoint to retrain with new data
4. **Deploy to Cloud**: Push to AWS/GCP/Azure
5. **Add More Models**: Create multi-model API
6. **A/B Testing**: Compare model versions with metrics

---

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
