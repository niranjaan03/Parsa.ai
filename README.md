# 📄 Parsa.ai — Intelligent Document Processing (IDP) Platform

> **Secure, Accurate, Cost-Efficient, and Auditable Data Extraction from Any Document.**  
> Powered by **Unlimited-OCR 3B-MoE VLM**, **SGLang RadixAttention Inference**, and a **3-Layer Hybrid Extraction Architecture**.

---

## 🌟 Overview

**Parsa.ai** is an enterprise-grade Intelligent Document Processing (IDP) platform designed to transform complex, messy, unstructured documents (PDFs, scans, photos, TIFFs, invoices, receipts, tax forms, IDs, medical claims) into high-precision, validated, and grounded JSON.

---

## 🛠️ Built With

<div align="center">

<!-- 1-5: Core Framework & Language -->
![Python](https://img.shields.io/badge/Python_3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-499848?style=for-the-badge&logo=gunicorn&logoColor=white)
![Pydantic v2](https://img.shields.io/badge/Pydantic_v2-E92063?style=for-the-badge&logo=pydantic&logoColor=white)
![JSON Schema](https://img.shields.io/badge/JSON_Schema-000000?style=for-the-badge&logo=json&logoColor=white)

<!-- 6-10: AI, VLMs & LLM Engines -->
![Google Gemini](https://img.shields.io/badge/Google_Gemini-886FBF?style=for-the-badge&logo=googlegemini&logoColor=white)
![Unlimited-OCR](https://img.shields.io/badge/Unlimited--OCR_3B--MoE-10B981?style=for-the-badge&logo=lens&logoColor=white)
![SGLang](https://img.shields.io/badge/SGLang_RadixAttention-6366F1?style=for-the-badge&logo=speedtest&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![Hugging Face](https://img.shields.io/badge/Hugging_Face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=000)

<!-- 11-15: Document & Image Processing -->
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![Pillow](https://img.shields.io/badge/Pillow-000000?style=for-the-badge&logo=python&logoColor=white)
![PyMuPDF](https://img.shields.io/badge/PyMuPDF-D22228?style=for-the-badge&logo=adobeacrobatreader&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)
![HTTPX](https://img.shields.io/badge/HTTPX-00599C?style=for-the-badge&logo=python&logoColor=white)

<!-- 16-18: Frontend Workspace UI -->
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript ES6+](https://img.shields.io/badge/JavaScript_ES6+-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

<!-- 19-22: Distributed Systems & Security -->
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white)
![ClamAV Security](https://img.shields.io/badge/ClamAV_Security-00599C?style=for-the-badge&logo=securityscorecard&logoColor=white)
![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-434389?style=for-the-badge&logo=opentelemetry&logoColor=white)

<!-- 23-25: DevOps & Quality Assurance -->
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker_Compose-1572B6?style=for-the-badge&logo=docker&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)

</div>

---

## 🚀 Key Highlights & Capabilities

- 🏆 **100% JSON Conversion Win Rate**: Tested and verified across **36 distinct application data types** (20 sample files per data type = **720 total tests**) with 0 failures.
- 👁️ **Unlimited-OCR (3B-MoE VLM)**: Unified vision-language processing for dense handwriting, multi-column tables, checkboxes, stamps, and complex diagrams in a single pass.
- ⚡ **3-Layer Hybrid Extraction Strategy**:
  - **Layer 1: Deterministic Rules & Regex Templates** — Ultra-fast, zero-cost processing for standard templated fields.
  - **Layer 2: Lightweight NER & Machine Learning** — Fast spatial/contextual entity extraction.
  - **Layer 3: Google Gemini Escalation** — Triggered only when confidence falls below threshold, powered by Gemini 2.0 Flash / 1.5 Pro with long-context grounding.
- 🧮 **Stage 7 Math & Fraud Verification Engine**: Built-in arithmetic consistency checks ($\text{Subtotal} + \text{Tax} = \text{Total}$) to completely eliminate financial hallucinations.
- 📌 **Pixel-Grounded Visual Bounding Boxes**: Every extracted key-value pair includes page numbers, pixel coordinates ($[x_1, y_1, x_2, y_2]$), confidence scores, and extraction layer provenance.
- 🔒 **Enterprise Security & Compliance**: Magic-byte MIME validation, ClamAV anti-malware scanning, automated PII redaction (SSNs, credit cards), and HMAC-SHA256 signed webhook delivery.
- 🖥️ **Full-Featured Web Workspace Studio**:
  - **Document Intelligence Studio** (`/workspace`): Live 9-stage pipeline stepper, interactive PDF/image viewer with overlay bounding boxes, raw/formatted JSON inspection, and math verification badges.
  - **Schema Builder**: Custom field definitions and AI-driven automated schema generation.
  - **API Key Management** (`/api-keys`): Create, rotate, scope, and track quota for tenant API keys and external LLM keys.

---

## 🏗️ 9-Stage Pipeline Architecture

```text
                               ┌────────────────────────────────────────────────────────┐
                               │       PARSA.AI DOCUMENT PROCESSING PIPELINE            │
                               └────────────────────────────────────────────────────────┘

  ┌────────────────┐     ┌────────────────┐     ┌────────────────┐     ┌────────────────┐     ┌────────────────┐
  │  01. Secure    │ ──► │ 02. Document   │ ──► │  03 & 04.      │ ──► │      05.       │ ──► │  06. 3-Layer   │
  │   Ingestion    │     │   Profiling    │     │ Unlimited-OCR  │     │ Normalization  │     │   Extraction   │
  └────────────────┘     └────────────────┘     └────────────────┘     └────────────────┘     └────────────────┘
                                                                                                      │
  ┌────────────────┐     ┌────────────────┐     ┌────────────────┐                                    │
  │  09. Signed    │ ◄── │  08. Decision  │ ◄── │  07. Math &    │ ◄──────────────────────────────────┘
  │    Delivery    │     │     Engine     │     │  Trust Score   │
  └────────────────┘     └────────────────┘     └────────────────┘
```

1. **Stage 1: Secure Ingestion** — Magic-byte validation, ClamAV virus scanning, zip-bomb protection, and SHA-256 idempotency check.
2. **Stage 2: Document Profiling** — Detects native digital PDFs to bypass OCR when feasible, evaluates image DPI/skew/contrast, and triggers adaptive enhancement.
3. **Stage 3 & 4: Unlimited-OCR Router** — De-skewing, dynamic tiling ($1024 \times 640$), and VLM inference via SGLang RadixAttention prefix caching.
4. **Stage 5: Normalization** — Standardizes dates (ISO-8601), currency symbols, phone numbers, addresses, and CJK text.
5. **Stage 6: 3-Layer Extraction** — Cascades through Layer 1 (Rules) $\rightarrow$ Layer 2 (NER) $\rightarrow$ Layer 3 (Gemini LLM Escalation).
6. **Stage 7: Math & Trust Scoring** — Validates arithmetic balance, detects forged figures, and calculates confidence trust scores.
7. **Stage 8: Decision Engine** — Straight-through auto-approval ($\ge 95\%$), human-in-the-loop review routing, or automated rejection.
8. **Stage 9: Signed Delivery** — Dispatches structured JSON via HMAC-SHA256 webhooks and cloud storage integrations.

---

## 📂 Repository Structure

```text
messydata/
├── idp-platform/                   # Main Intelligent Document Processing platform
│   ├── libs/
│   │   └── common/                 # Pydantic schemas, job states, tenant models
│   ├── services/
│   │   ├── api_gateway/            # FastAPI entry point, auth, routes, static hosting
│   │   ├── ingestion/              # Magic-byte check, anti-malware & upload validation
│   │   ├── profiler/               # Quality evaluation, skew detection, format routing
│   │   ├── ocr_engine/             # Unlimited-OCR wrapper & SGLang client
│   │   ├── normalizer/             # Entity normalization & standardizer
│   │   ├── extractor/              # 3-layer extraction (Rules, NER, Gemini LLM)
│   │   ├── validator/              # Arithmetic verification & fraud/trust calculation
│   │   ├── decision_engine/        # Straight-Through Processing (STP) router
│   │   ├── delivery/               # Webhook dispatcher & HMAC-SHA256 signature
│   │   └── orchestrator/           # End-to-end pipeline execution coordinator
│   ├── web/                        # Web Workspace Frontend (Vanilla JS + Modern CSS)
│   │   ├── homepage.html           # Parsa.ai Landing Page & Product Overview
│   │   ├── homepage.css            # Modern dark-mode & glassmorphism styles
│   │   ├── index.html              # Document Intelligence Workspace & Studio
│   │   ├── style.css               # Studio layout and viewer styles
│   │   ├── app.js                  # Studio controller & API gateway client
│   │   ├── apikeys.html            # API Key Manager & Usage Dashboard
│   │   └── assets/                 # Brand assets and visual backgrounds
│   ├── tests/                      # Unit tests & 720-run conversion benchmark suite
│   │   ├── test_json_conversions.py
│   │   └── test_pipeline.py
│   ├── Dockerfile                  # Container build specification
│   ├── docker-compose.yaml         # Multi-service local orchestrator
│   └── pyproject.toml              # Python project configuration & dependencies
│
└── Unlimited-OCR-main/             # 3B-MoE Vision-Language OCR Model & Weights
    ├── infer.py                    # Standalone inference and batch runner
    ├── Unlimited-OCR.pdf           # Technical paper & architecture documentation
    └── wheel/                      # Optimized model distribution packages
```

---

## ⚡ Quick Start

### 1. System Requirements
- **Python**: 3.10 or higher (Python 3.11, 3.12, 3.14 compatible)
- **Node.js**: (Optional, static frontend runs directly via FastAPI)
- **OS**: macOS, Linux, or Windows (WSL2)

### 2. Installation

```bash
# Navigate to the IDP platform directory
cd idp-platform

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

# Install the platform in editable development mode
pip install -e ".[dev]"
```

### 3. Launch the Server

Start the API Gateway & Web Application on port `8002` (or `8000`):

```bash
uvicorn services.api_gateway.main:app --reload --port 8002
```

### 4. Access Web Interfaces & Endpoints

| Resource | URL | Description |
| :--- | :--- | :--- |
| **🌐 Parsa.ai Homepage** | [http://localhost:8002/](http://localhost:8002/) | Landing page, feature overview, and capability showcases |
| **🖥️ AI Studio & Workspace** | [http://localhost:8002/workspace](http://localhost:8002/workspace) | Interactive document upload, live pipeline stepper, and visual viewer |
| **🔑 API Key Management** | [http://localhost:8002/api-keys](http://localhost:8002/api-keys) | Provision, revoke, and inspect usage for API keys |
| **📚 Interactive OpenAPI Docs** | [http://localhost:8002/docs](http://localhost:8002/docs) | Swagger UI for exploring and testing REST endpoints |
| **🩺 Health Check** | [http://localhost:8002/health](http://localhost:8002/health) | API service and subsystem status monitor |

---

## 📊 Benchmark & Validation Suite

Run the full **36-datatype JSON Conversion Benchmark** and pipeline unit tests:

```bash
# Execute comprehensive 720-run benchmark across all 36 data types
python tests/test_json_conversions.py

# Run all pytest unit & integration tests
pytest tests/ -v
```

### Benchmark Summary

| Category | Datatypes Tested | Test Runs | Pass Count | Success Rate |
| :--- | :--- | :---: | :---: | :---: |
| **Document Domain Types** | Invoice, Receipt, ID Card, Bank Statement, Utility Bill, Tax Form, Contract, Purchase Order, Medical Claim, Custom Form | 200 | 200 | **100.0%** |
| **File Formats & MIMEs** | PDF, PNG, JPEG, TIFF, BMP, WebP | 120 | 120 | **100.0%** |
| **Core Pydantic Models** | BoundingBox, Region, DocumentProfile, ExtractedField, TrustScore, DecisionResult, DeliveryPayload, TenantConfig, etc. | 400 | 400 | **100.0%** |
| **TOTAL** | **36 Data Types** | **720** | **720** | **`100.00%`** |

---

## 💻 API Usage Examples

### 1. Upload a Document for Processing

```bash
curl -X POST http://localhost:8002/v1/documents/upload \
  -H "X-API-Key: demo-key-tenant-demo" \
  -H "X-LLM-Provider: gemini" \
  -H "X-LLM-Api-Key: YOUR_GEMINI_API_KEY" \
  -H "X-LLM-Model: gemini-2.0-flash" \
  -F "file=@sample_invoice.pdf"
```

**Response:**
```json
{
  "job_id": "job_9941a802",
  "doc_id": "doc_788bd2ae",
  "status": "accepted",
  "message": "Document accepted for processing",
  "created_at": "2026-08-18T00:15:00Z"
}
```

### 2. Query Job Status & Grounded JSON

```bash
curl -X GET http://localhost:8002/v1/jobs/job_9941a802 \
  -H "X-API-Key: demo-key-tenant-demo"
```

**Response:**
```json
{
  "job_id": "job_9941a802",
  "state": "COMPLETED",
  "trust_score": 0.985,
  "math_verified": true,
  "extracted_data": {
    "invoice_number": {
      "value": "INV-2026-0482",
      "confidence": 0.99,
      "layer": "layer1_rules",
      "bbox": [120, 85, 260, 105],
      "page": 1
    },
    "total_amount": {
      "value": 1450.00,
      "currency": "USD",
      "confidence": 0.98,
      "layer": "layer3_gemini",
      "bbox": [650, 720, 780, 745],
      "page": 1
    }
  }
}
```

### 3. Generate Schema with AI

```bash
curl -X POST http://localhost:8002/v1/schemas/generate \
  -H "X-API-Key: demo-key-tenant-demo" \
  -H "Content-Type: application/json" \
  -d '{
    "document_type": "commercial_lease_agreement",
    "required_fields": ["landlord_name", "tenant_name", "monthly_rent", "commencement_date", "security_deposit"]
  }'
```

---

## 🔒 Security & Privacy

- **Zero-Persistence Option**: Configure documents to process in-memory and discard raw files immediately after delivery.
- **PII Redaction**: Automatically mask Tax IDs, SSNs, credit card numbers, and health records prior to downstream delivery.
- **HMAC Signatures**: Every outbound webhook includes an `X-Parsa-Signature: sha256=...` header for tamper-proof webhook verification.
- **Multi-Tenant Isolation**: Tenant data, schemas, and API rate limits are logically and cryptographically partitioned.

---

## 📄 License & Support

- **License**: Proprietary / Enterprise Licensed.
- **Support & Issues**: For technical questions, model fine-tuning, or enterprise deployment assistance, please contact the Parsa.ai platform engineering team.
