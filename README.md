# FabricIQ

**AI-powered intelligence for fabric & textile manufacturing** — demand prediction, explainable ML, production scheduling optimization, and document digitization in one platform.

![Status](https://img.shields.io/badge/status-active--development-yellow)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Next.js](https://img.shields.io/badge/frontend-Next.js-black)

---

## 📖 Overview

FabricIQ is an end-to-end platform that helps textile and fabric manufacturers move from gut-feel planning to data-driven decisions. It ingests production and order data, predicts demand using machine learning, explains *why* the model made a prediction (not just what it predicted), optimizes production scheduling under real-world constraints, and digitizes paper-based records (invoices, delivery challans, quality reports) via OCR — all surfaced through a single dashboard.

**Core problems it solves:**
- Manual, spreadsheet-driven demand forecasting that doesn't scale
- Black-box ML predictions that operations teams don't trust
- Manual production scheduling that ignores machine/labor constraints
- Paper-based records that never make it into any system

---

## 🧱 Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend API** | FastAPI (Python) | Core REST API, request validation, orchestration |
| **Database** | PostgreSQL + SQLAlchemy ORM | Persistent storage for orders, production data, model metadata |
| **Data Ingestion** | Custom ingestion pipeline (Pandas) | Cleans and normalizes raw CSV/Excel/ERP exports |
| **ML Preprocessing** | Scikit-learn pipelines | Feature engineering, scaling, encoding |
| **Prediction Model** | XGBoost | Demand/production forecasting |
| **Explainability** | SHAP | Per-prediction feature attribution for transparency |
| **Scheduling Optimization** | Google OR-Tools (CP-SAT) | Constraint-based production scheduling |
| **Document Digitization** | Tesseract OCR / OCR pipeline | Extracts text from scanned invoices, challans, reports |
| **Frontend** | Next.js (React) | Dashboard, visualizations, user interactions |
| **Containerization** | Docker + Docker Compose | Reproducible local & production environments |
| **Automation** | Makefile | One-command setup, test, and run commands |
| **CI/CD** | GitHub Actions | Automated linting, testing, and build checks |

---

## ✨ Features

### 1. Demand & Production Prediction
- XGBoost-based forecasting model trained on historical order and production data
- Supports batch prediction and single-record prediction via API
- Model versioning so predictions can be traced back to a specific trained model

### 2. Explainable AI (XAI) Layer
- SHAP value generation for every prediction
- Human-readable breakdown of which factors (seasonality, raw material cost, order backlog, etc.) drove a given forecast
- Designed so non-technical operations staff can understand *why*, not just *what*

### 3. Production Scheduling Optimizer
- OR-Tools CP-SAT solver to generate feasible production schedules
- Respects constraints such as machine availability, labor shifts, and order priority/deadlines
- Outputs an optimized schedule that can be reviewed and adjusted before execution

### 4. OCR Document Digitization
- Upload scanned invoices, delivery challans, or quality inspection sheets
- OCR pipeline extracts structured text/fields for downstream storage and search
- Reduces manual data entry from paper records

### 5. Interactive Dashboard
- Built in Next.js, consumes the FastAPI backend
- Visualizes demand forecasts, SHAP explanations, and schedules in one place
- Designed for both plant managers and analysts

### 6. Developer & Ops Tooling
- Dockerized services for consistent local/prod parity
- Makefile shortcuts (`make setup`, `make test`, `make run`, etc.)
- GitHub Actions CI pipeline for linting and automated tests on every push/PR

---

## 🖥️ Dashboard Preview

![FabricIQ Dashboard](./docs/screenshots/dashboard.png)

> *Replace the image above with an actual screenshot of your running dashboard (recommended path: `docs/screenshots/dashboard.png`). A placeholder is used here since no live screenshot was available at README generation time.*

---

## 🏗️ Project Structure

```
fabriciq/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI route handlers
│   │   ├── models/           # SQLAlchemy DB models
│   │   ├── ml/               # XGBoost training + inference
│   │   ├── explainability/   # SHAP integration
│   │   ├── scheduler/        # OR-Tools optimization logic
│   │   └── ocr/              # OCR ingestion pipeline
│   └── tests/
├── frontend/
│   ├── pages/                # Next.js pages (dashboard, uploads, etc.)
│   └── components/
├── docker/
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── docker-compose.yml
├── Makefile
├── .github/workflows/        # CI/CD pipelines
└── README.md
```

---

## ⚠️ Known Limitations / Loopholes

Being transparent about the current gaps is intentional — this is an active project, not a finished product.

- **Cold-start forecasting:** The model needs a reasonable volume of historical data per product line; new SKUs with little history get low-confidence predictions.
- **OCR accuracy on poor scans:** Handwritten or low-quality scanned documents can produce incomplete or incorrect field extraction; there's currently no human-in-the-loop correction step.
- **Scheduler assumes static constraints:** The OR-Tools model currently treats machine/labor availability as fixed inputs per run — it doesn't yet react to real-time floor changes (e.g., a machine going down mid-shift).
- **No authentication/authorization layer yet:** The API and dashboard currently assume a trusted internal network; role-based access control is not yet implemented.
- **Single-tenant design:** The current architecture is not yet built for multi-factory/multi-tenant deployments.
- **Limited automated test coverage:** CI currently covers linting and basic unit tests; integration and end-to-end test coverage is still shallow.
- **No data versioning/lineage tracking:** Training datasets aren't yet versioned, which makes it harder to fully reproduce a specific model's training run after the fact.

---

## 🚀 Roadmap / Future Scope

- [ ] Human-in-the-loop review/correction step for OCR extraction
- [ ] Real-time constraint updates for the scheduling optimizer
- [ ] Multi-factory / multi-tenant support
- [ ] Model monitoring & drift detection for the XGBoost pipeline
- [ ] Data versioning (e.g., DVC) for full training reproducibility
- [ ] Expand CI/CD to include integration and end-to-end tests
- [ ] Mobile-responsive dashboard views
- [ ] Alerting system (e.g., email/Slack) for schedule conflicts or low-confidence forecasts

---

## ⚙️ Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ (for local frontend dev outside Docker)

### Setup
```bash
# Clone the repository
git clone https://github.com/<your-username>/fabriciq.git
cd fabriciq

# Build and start all services
make setup
make run
```

### Common Make commands
```bash
make setup     # Install dependencies, build containers
make run       # Start backend + frontend via Docker Compose
make test      # Run backend test suite
make lint      # Run linters
make down      # Stop all running containers
```

Once running:
- Backend API: `http://localhost:8000`
- API docs (Swagger): `http://localhost:8000/docs`
- Frontend dashboard: `http://localhost:3000`

---

## 🤝 Contributing

Contributions are welcome. Please open an issue to discuss significant changes before submitting a pull request, and ensure `make lint` and `make test` pass locally before opening a PR.

---

