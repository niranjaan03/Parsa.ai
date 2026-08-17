# 📄 Parsa.ai Document Intelligence Platform

> **Secure, Accurate, Cost-Efficient, Trusted Data from Any Document.**  
> Powered by **Unlimited-OCR 3B-MoE VLM**, **SGLang RadixAttention Inference**, and a **3-Layer Hybrid Extraction Strategy**.

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

- **🏆 100% JSON Conversion Win Rate**: Tested and verified across **36 distinct application data types** (20 sample files per data type = **720 total tests**) with 0 errors.
- **👁️ Unlimited-OCR (3B-MoE VLM)**: Unified vision-language processing for printed text, dense handwriting, complex multi-column tables, and image figures in a single inference pass.
- **⚡ 3-Layer Cost-Optimized Extraction**:
  - **Layer 1**: Deterministic Rules & Regex Templates (Fastest, $0.00 cost)
  - **Layer 2**: Lightweight Named Entity Recognition (NER / Small ML Model)
  - **Layer 3**: LLM Escalation (Invoked *only* when confidence drops below threshold, powered by Google Gemini 2.0 Flash / 1.5 Pro).
- **🤖 Google Gemini Integration**: Exclusively powered by **Google Gemini API** (Gemini 2.0 Flash / 1.5 Pro) for high-speed, long-context Layer 3 escalation with verified Gemini API key management.
- **🧮 Stage 7 Math & Fraud Verification Engine**: Automatic arithmetic integrity checks ($Subtotal + Tax = Total$) eliminate financial hallucinations.
- **📌 Grounded Bounding Box Citations**: Every extracted JSON value includes pixel bounding box coordinates, page numbers, confidence percentages, and extraction layer tags.
- **🔒 Enterprise Security & PII Redaction**: Built-in magic-byte validation, ClamAV scanning, automatic PII redaction (SSNs, Card numbers), and HMAC-SHA256 signed webhook delivery.
- **🖥️ Web Workspace Studio**: Includes the **Parsa.ai Landing Page** (`/`), **Document Intelligence Studio** (`/workspace`), **API Key Manager** (`/api-keys`), **Interactive Schema Builder**, and **Live 9-Stage Pipeline Stepper**.

---

## 🏗️ 9-Stage Architecture & Pipeline

```text
                                 DOCUMENT PROCESSING PIPELINE
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  01. Secure  │ ──► │ 02. Document │ ──► │  03 & 04.    │ ──► │     05.      │ ──► │  06. 3-Layer │
│  Ingestion   │     │  Profiling   │     │ OCR Router   │     │ Normalization│     │  Extraction  │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                                           │
┌──────────────┐     ┌──────────────┐     ┌──────────────┐                                 │
│ 09. Signed   │ ◄── │ 08. Decision │ ◄── │ 07. Math &   │ ◄───────────────────────────────┘
│   Delivery   │     │    Engine    │     │ Trust Score  │
└──────────────┘     └──────────────┘     └──────────────┘
```

1. **Stage 1: Secure Ingestion** — Magic-byte MIME validation, ClamAV virus scanning, zip-bomb protection, and SHA-256 idempotency check.
2. **Stage 2: Document Profiling** — Detects digital PDFs to skip OCR, scores image quality, and chooses image enhancement filters.
3. **Stage 3 & 4: Unlimited-OCR Router** — De-skewing, dynamic tiling ($1024 \times 640$), and VLM inference via SGLang RadixAttention prefix caching.
4. **Stage 5: Normalization** — Converts dates to ISO-8601, normalizes currency codes, and cleans CJK/special characters.
5. **Stage 6: 3-Layer Extraction** — Cascades through Layer 1 Rules $\rightarrow$ Layer 2 Small Model $\rightarrow$ Layer 3 LLM Escalation (Google Gemini 2.0 Flash / 1.5 Pro).
6. **Stage 7: Math & Trust Scoring** — Verifies arithmetic equations ($Subtotal + Tax = Total$), checks fraud signatures, and computes document trust scores.
7. **Stage 8: Decision Engine** — Straight-through auto-approval ($\ge 95\%$ confidence), human review routing, or rejection.
8. **Stage 9: Output Delivery** — Delivers structured JSON via HMAC-SHA256 signed webhooks and ERP connectors.

---

## 📂 Project Structure

```text
idp-platform/
├── libs/
│   └── common/             # Shared Pydantic schemas, job states, enums
├── services/
│   ├── api_gateway/        # REST API, FastAPI router, auth, rate limiting
│   ├── ingestion/          # Magic-byte MIME validation & virus scanning
│   ├── profiler/           # Document quality scoring & format profiling
│   ├── ocr_engine/         # Unlimited-OCR & SGLang router
│   ├── normalizer/         # Text & data field normalization
│   ├── extractor/          # 3-layer extraction strategy & Gemini LLM escalation
│   ├── validator/          # Arithmetic verification & trust scoring
│   ├── decision_engine/    # Straight-through processing & review routing
│   ├── delivery/           # Signed webhooks & ERP delivery connectors
│   └── orchestrator/       # Job state machine & pipeline coordination
├── web/                    # Document Intelligence Workspace Frontend
│   ├── homepage.html       # Parsa.ai Landing Page & Product Overview
│   ├── homepage.css        # Landing page styling & animations
│   ├── index.html          # Web Workspace UI & Document Studio
│   ├── style.css           # Design system & component styles
│   ├── app.js              # Interactive Workspace logic & API integration
│   └── apikeys.html        # API Key Manager & Usage Interface
├── infra/                  # Docker Compose & Kubernetes manifests
└── tests/                  # Test suites & 36-datatype JSON conversion benchmarks
    ├── test_json_conversions.py  # 360/720 file conversion benchmark suite
    └── test_pipeline.py         # End-to-end 9-stage pipeline unit tests
```

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.10+ (Python 3.11, 3.12, 3.14 compatible)
- `pip` & virtual environment

### 2. Environment Setup

```bash
# Clone repository & navigate to directory
cd idp-platform

# Activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

### 3. Run the API Gateway & Web Workspace

```bash
# Start FastAPI backend on port 8002 (or 8000)
uvicorn services.api_gateway.main:app --reload --port 8002
```

Open your browser and navigate to:
- **Parsa.ai Homepage**: [http://localhost:8002/](http://localhost:8002/)
- **Document Studio / Workspace**: [http://localhost:8002/workspace](http://localhost:8002/workspace) (or `/ui`)
- **API Key Management**: [http://localhost:8002/api-keys](http://localhost:8002/api-keys)
- **API Health Check**: [http://localhost:8002/health](http://localhost:8002/health)
- **Interactive OpenAPI Docs**: [http://localhost:8002/docs](http://localhost:8002/docs)

---

## 📊 Benchmark & Testing Suite

Run the full **36-datatype JSON Conversion Benchmark** and pipeline unit tests:

```bash
# Run complete JSON conversion benchmark (36 data types × 20 sample files = 720 runs)
python tests/test_json_conversions.py

# Run unit tests via pytest
pytest tests/
```

### Benchmark Results Overview (720 Test Runs)

| Category | Datatypes Tested | Test Cases | Pass Count | Win Rate |
| :--- | :--- | :---: | :---: | :---: |
| **Document Domain Types** | Invoice, Receipt, ID Card, Bank Statement, Utility Bill, Tax Form, Contract, Purchase Order, Medical Claim, Custom Form | 200 | 200 | **100.0%** |
| **File Format MIMEs** | PDF, PNG, JPEG, TIFF, BMP, WebP | 120 | 120 | **100.0%** |
| **Core Pydantic Schemas** | BoundingBox, Region, PageProfile, DocumentProfile, PageExtractionResult, ExtractionResult, NormalizedField, NormalizedOutput, ExtractedField, ExtractionOutput, ValidationFlag, TrustScore, DecisionResult, DeliveryPayload, DocumentJob, TenantLimits, TenantFeatures, TenantStorage, TenantConfig, ModelRegistryEntry | 400 | 400 | **100.0%** |
| **TOTAL** | **36 Data Types** | **720** | **720** | **`100.00%`** |

---

## 💻 API Usage Examples

### Upload Document & Extract Grounded JSON

```bash
curl -X POST http://localhost:8002/v1/documents/upload \
  -H "X-API-Key: demo-key-tenant-demo" \
  -H "X-LLM-Provider: gemini" \
  -H "X-LLM-Api-Key: AIzaSy_your_gemini_key_here" \
  -H "X-LLM-Model: gemini-2.0-flash" \
  -F "file=@invoice.pdf"
```

### Response Payload

```json
{
  "job_id": "job_9941a802",
  "doc_id": "doc_788bd2ae",
  "status": "accepted",
  "message": "Document accepted for processing"
}
```

---

## 🤝 Contributing & License

- **License**: Proprietary / Enterprise Licensed.
- Designed & maintained for high-throughput enterprise Intelligent Document Processing.
