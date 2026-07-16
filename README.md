# 🚀 FitNesse API — Test Automation Framework

[![codecov](https://codecov.io/gh/Suraj-176/Python_FitNessFramework/branch/main/graph/badge.svg?token=YOUR_TOKEN)](https://codecov.io/gh/Suraj-176/Python_FitNessFramework)
[![Tests Status](https://github.com/Suraj-176/Python_FitNessFramework/actions/workflows/tests.yml/badge.svg)](https://github.com/Suraj-176/Python_FitNessFramework/actions)

Welcome to the **FitNesse API Test Automation Framework**. This is a secure, high-performance, enterprise-grade REST API testing framework integrating FitNesse's SLIM engine with pure Python 3.10+ backend fixtures.

It features a custom, responsive HTML dashboard, basic authentication popup security on startup, custom log rotation, an embedded standard-library Python HTTP Mock Server for offline/CI environments, and a suite of advanced enterprise-level testing capabilities.

---

## 1. Directory Structure

```text
FitNessePythonFramework/
├── start_server.bat             # 1-Click launcher (closes conflicts, frees ports 8080/8089 & boots server)
├── plugins.properties           # Custom template overrides config
├── passwords.txt                # Secure user credentials (admin:admin123)
├── fitnesse-standalone.jar      # FitNesse standalone server engine
├── .gitignore                   # Safe Git exclusions (virtual env, logs, caches)
├── .gitattributes               # Forces GitHub to accurately show 100% Python statistics
├── Jenkinsfile                  # Declarative Jenkins CI/CD Pipeline (Windows Node)
│
├── .venv/                       # Isolated Python Virtual Environment with locked dependencies
│
├── FitNesseRoot/                # Wiki root directory
│   ├── FrontPage/               # Custom HTML Dashboard (http://localhost:8080/)
│   └── ApiTests/                # Master Corporate Test Suite
│       ├── SuiteSetUp           # Automatically starts mock server on port 8089
│       └── SuiteTearDown        # Automatically shuts down mock server on completion
│
├── fixtures/                    # 100% Pure Python SLIM Fixtures
│   ├── __init__.py              # Exposes fixtures on package level
│   ├── auth_fixture.py          # Shared bearer token generation and storage
│   ├── base_fixture.py          # Core request engine (handles headers, uploads, cURL logs, SSL verify)
│   ├── delete_request_fixture.py# DELETE request engine
│   ├── get_request_fixture.py   # GET request engine (supports nested JSONPath)
│   ├── post_request_fixture.py  # POST request engine (supports body JSON payload)
│   ├── put_request_fixture.py   # PUT request engine
│   ├── patch_request_fixture.py # PATCH request engine
│   ├── delete_request_fixture.py# DELETE request engine
│   ├── head_request_fixture.py  # HEAD request engine
│   ├── options_request_fixture.py# OPTIONS request engine
│   ├── json_utils.py            # JSON extractor with ValueError safety handling
│   ├── mock_server_fixture.py   # Embedded background HTTP Mock Server
│   ├── grpc_request_fixture.py  # GRPC request engine
│   ├── graphql_request_fixture.py # GraphQL request engine
│   └── oauth2_fixture.py        # Dedicated OAuth2 request engine
│
├── core/                        # Core Framework Infrastructure
│   ├── logger.py                # Structured daily rotating file and console logger
│   ├── fitnesse_watcher.py      # Real-time folder-sync and self-healing watcher
│   ├── report_generator.py      # Stub report generator hook
│   ├── validators.py            # Input validation helper
│   ├── config.py                # Environment configuration loader
│   ├── token_encryption.py      # Token encryption & storage helper
│   └── data_factory.py          # Faker test data generator helper
│
├── tests/                       # Automated Test Suite (pytest)
│   ├── unit/                    # Unit tests for core functions
│   └── integration/             # Integration tests for requests/fixtures
│
└── logs/                        # Rotation log outputs (7-day retention)
    └── framework.log            # Active logger output
```

---

## 2. Generic HTTP Request Engine

Instead of writing custom fixtures for every endpoint, this framework utilizes **Generic HTTP Decision Table Fixtures**. This allows any QA engineer to automate and test any REST API endpoint dynamically directly inside the FitNesse wiki with **zero code changes**:

*   **`fixtures.AuthFixture`**: Authenticates and stores the token inside a static class variable, which is automatically appended as a `Bearer` token to all other request fixtures.
*   **`fixtures.GetRequestFixture`**: Executes GET calls. Supports response times, status code list matches (`200,201`), and nested JSONPath lookups (e.g., `$.status`).
*   **`fixtures.PostRequestFixture`** / **`PutRequestFixture`** / **`PatchRequestFixture`**: Executes write verbs, parsing raw body JSON strings.
*   **`fixtures.DeleteRequestFixture`**: Executes DELETE calls and checks status codes.
*   **`fixtures.HeadRequestFixture`**: Executes HEAD calls to fetch and validate header keys.
*   **`fixtures.OptionsRequestFixture`**: Executes OPTIONS calls to validate server-supported HTTP verbs and CORS origin rules.
*   **`fixtures.GraphqlRequestFixture`**: Executes GraphQL calls, packing your raw queries and variables dynamically.
*   **`fixtures.Oauth2Fixture`**: Dedicated OAuth2 request engine supporting password & client credentials grant flows.

---

## 3. Enterprise-Grade Capabilities

This framework is built for enterprise scalability:
*   **SSL Verification Control (`setSslVerify`):** Set `setSslVerify` to `false` in FitNesse tables to bypass self-signed SSL warnings on corporate internal UAT/staging endpoints.
*   **Response Header Verification (`setHeaderLookup`):** Inspect and validate returned HTTP headers (like tokens, content types, or redirects) directly from wiki tables.
*   **Multipart File Uploads (`setFilePath`):** Upload files (e.g. PDFs or image attachments) using multipart requests automatically.
*   **cURL Replicator:** Automatically compiles and logs the exact `curl` command equivalent for **every request** executed, allowing developers to copy-paste and debug failures in 1 click.
*   **ValueError Safety:** The JSON extractor is designed to handle invalid queries gracefully without crashing the runner process.

---

## 4. Local Embedded HTTP Mock Server (Port 8089)

To allow the entire suite to run 100% offline, locally, and inside headless CI/CD pipelines (like GitHub Actions) with **zero manual backend setup**:
*   The framework embeds an HTTP mock server inside **`MockServerFixture`** written using only Python's standard library.
*   **`SuiteSetUp`** automatically boots this server in a background daemon thread on port `8089` before running any tests.
*   **`SuiteTearDown`** automatically stops and closes the server on suite completion, freeing the port cleanly.

---

## 5. How to Run Locally

1.  **Launch Server:** Double-click **`start_server.bat`** (or execute `.\start_server.bat` in your PowerShell).
2.  **Access Portal:** Open your browser and navigate to **`http://localhost:8080/`**.
3.  **Enter Secure Credentials:**
    *   Username: `admin`
    *   Password: `admin123`
4.  **Graphical Dashboard:** You will instantly see your custom-designed FitNesse API Test Suite landing dashboard! Click **Suite** or individual **Run** buttons to execute your tests in 1 click!

---

## 6. How to Run Unit & Integration Tests (pytest)

1.  **Activate virtual environment:**
    ```powershell
    .venv\Scripts\Activate.ps1
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run all unit and integration tests:**
    ```bash
    pytest
    ```
4.  **Run with coverage reporting:**
    ```bash
    pytest --cov --cov-report=html
    ```
    Open `htmlcov/index.html` in your web browser to view the interactive line-by-line coverage reports!

---

### 🏆 Enterprise QA Engineering Standard Certified 🏆
Developed for **highly scalable, secure API test automation**. Pure Python, ultra-secure, and beautifully customized!
