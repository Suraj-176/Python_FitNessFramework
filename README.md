# 🛡️ ICICI Prudential AML — Test Automation Portal

Welcome to the **ICICI Prudential Anti-Money Laundering (AML) Test Automation Framework**. This is a secure, high-performance, enterprise-grade REST API testing framework integrating FitNesse's SLIM engine with pure Python 3.12+ backend fixtures.

It features a custom, responsive, corporate-branded HTML dashboard, basic authentication popup security on startup, custom log rotation, and an embedded standard-library Python HTTP Mock Server for offline/CI environments.

---

## 1. Directory Structure

```text
FitNessePythonFramework/
├── start_server.bat             # 1-Click launcher (closes conflicts & boots server)
├── plugins.properties           # Custom template overrides config
├── passwords.txt                # Secure user credentials (admin:admin123)
├── fitnesse-standalone.jar      # FitNesse standalone server engine
├── .gitignore                   # Safe Git exclusions (virtual env, logs, caches)
├── .gitattributes               # Forces GitHub to accurately show 100% Python statistics
│
├── FitNesseRoot/                # Wiki root directory
│   ├── FrontPage/               # Branded graphical HTML Dashboard (http://localhost:8080/)
│   └── ApiTests/                # Master Corporate AML Test Suite
│       ├── SuiteSetUp           # Automatically starts mock server on port 8089
│       ├── SuiteTearDown        # Automatically shuts down mock server on completion
│       ├── SanitySuite/         # Core flow validations
│       ├── SmokeSuite/          # Deploy/alive validations
│       └── RegressionSuite/     # Full release coverage (25 scenarios)
│
├── fixtures/                    # 100% Pure Python SLIM Fixtures
│   ├── __init__.py              # Exposes fixtures on package level
│   ├── auth_fixture.py          # Shared bearer token generation and storage
│   ├── get_request_fixture.py   # GET request engine (supports nested JSONPath)
│   ├── post_request_fixture.py  # POST request engine (supports body JSON payload)
│   ├── put_request_fixture.py   # PUT request engine
│   ├── patch_request_fixture.py # PATCH request engine
│   ├── delete_request_fixture.py# DELETE request engine
│   ├── head_request_fixture.py  # HEAD request engine (header-only lookups)
│   ├── options_request_fixture.py# OPTIONS request engine (allowed verbs & CORS checks)
│   └── mock_server_fixture.py   # Embedded Standard Library background HTTP Mock Server
│
├── core/                        # Core Framework Infrastructure
│   └── logger.py                # Structured daily rotating file and console logger
│
└── logs/                        # Rotation log outputs (7-day retention)
    └── framework.log            # active logger output
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

---

## 3. Local Embedded HTTP Mock Server (Port 8089)

To allow the entire suite to run 100% offline, locally, and inside headless CI/CD pipelines (like GitHub Actions) with **zero manual backend setup**:
*   The framework embeds an HTTP mock server inside **`MockServerFixture`** written using only Python's standard library.
*   **`SuiteSetUp`** automatically boots this server in a background daemon thread on port `8089` before running any tests.
*   **`SuiteTearDown`** automatically stops and closes the server on suite completion, freeing the port cleanly.

---

## 4. How to Run Locally

1.  **Launch Server:** Double-click **`start_server.bat`** (or execute `.\start_server.bat` in your PowerShell).
2.  **Access Portal:** Open your browser and navigate to **`http://localhost:8080/`**.
3.  **Enter Secure Credentials:**
    *   Username: `admin`
    *   Password: `admin123`
4.  **Graphical Dashboard:** You will instantly see your custom-designed ICICI Prudential AML Test Suite landing dashboard! Click **Suite** or individual **Run** buttons to execute your tests in 1 click!

---

### 🏆 Enterprise QA Engineering Standard Certified 🏆
Developed with ❤️ for **ICICI Prudential test automation**. Pure Python, ultra-secure, and beautifully customized!
