# Test Strategy Document  : Created By Ridhima Dhawan
## Cloud Storage Tiering System

## 1. Overview

This document defines the test strategy for validating the Cloud Storage Tiering System. The system manages uploaded files across storage tiers: HOT, WARM, and COLD based on file access patterns and business rules.
The objective of this test framework is to validate API correctness, tier transition behavior, metadata consistency, stats accuracy, edge cases, concurrency behavior, and basic performance characteristics using Pytest.
I have created pytest fixtures in conftest.py to prepate a clean test setup and additionally installed allure reports to capture structured reporting.

---

## 2. Scope

### In Scope

- File upload API
- File download API
- File metadata API
- File delete API
- Admin tiering API
- Admin stats API
- Tier transition validation
- Boundary and edge cases
- Concurrency scenarios
- Basic performance benchmarking
- Bug reporting and test documentation

### Out of Scope

- UI testing
- Authentication and authorization testing, since auth is not implemented
- Real cloud storage backend validation
- Large-scale production load testing
- Long-duration soak testing

---

## 3. Technology Stack

| Area | Tool / Framework |
|---|---|
| Programming Language | Python |
| Test Framework | Pytest |
| API Testing | FastAPI TestClient / HTTP client wrapper |
| Reporting | Pytest output, coverage report, Allure results |
| Coverage | pytest-cov |
| Performance | pytest-benchmark / custom timing |
| CI | GitHub Actions |

---

## 4. Framework Structure

```text
project-root/
│
├── src/
│   ├── storage_service
│   
│
├── tests/
│   ├── functional/
│   ├── fault_injection/
│   └── performance/
│
├── fixtures/
├── run_test.py
├── reports/
├── docs/
├── conftest.py
├── requirements.txt
└── .github/workflows/tests.yml