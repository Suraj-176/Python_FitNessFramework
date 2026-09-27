import datetime

from core.report_generator import match_request_to_page


def test_match_request_to_page_accepts_steps_running_after_page_start():
    page = {
        "name": "FrontPage.SwagLabs.LoginPage",
        "timestamp_raw": "20260926202238",
    }
    req = {
        "timestamp": "2026-09-26 20:22:54",
        "page_name": "LoginPage",
        "suite_name": "SwagLabs",
    }

    matched = match_request_to_page(req, [page])

    assert matched is page


def test_match_request_to_page_rejects_stale_history_from_older_runs():
    page = {
        "name": "FrontPage.SwagLabs.LoginPage",
        "timestamp_raw": "20260926182318",
    }
    req = {
        "timestamp": "2026-09-26 20:22:54",
        "page_name": "LoginPage",
        "suite_name": "SwagLabs",
    }

    matched = match_request_to_page(req, [page])

    assert matched is None


def test_record_api_request_adds_allure_style_steps_with_fitnesse_page_context(monkeypatch):
    import core.report_generator as report_generator

    recorded = []
    monkeypatch.setattr(report_generator, "add_record", recorded.append)
    monkeypatch.setenv("FITNESSE_PAGE_NAME", "AuthenticateUser")
    monkeypatch.setenv("FITNESSE_PAGE_PATH", "FrontPage.DummyAPI.AuthenticateUser")

    report_generator.record_api_request({
        "timestamp": "2026-09-27 17:17:06",
        "method": "POST",
        "url": "https://api.example.test/auth/login",
        "status_code": 200,
        "response_time_ms": 42,
        "right": 1,
        "wrong": 0,
        "exceptions": 0,
    })

    assert [record["method"] for record in recorded] == ["STEP", "STEP", "POST"]
    assert [record["url"] for record in recorded[:2]] == [
        "Prepare Request Headers & Body",
        "Send HTTP POST Request",
    ]
    assert all(record["page_name"] == "AuthenticateUser" for record in recorded)
    assert all(record["suite_name"] == "DummyAPI" for record in recorded)


def test_record_api_request_marks_failed_send_step(monkeypatch):
    import core.report_generator as report_generator

    recorded = []
    monkeypatch.setattr(report_generator, "add_record", recorded.append)
    report_generator.record_api_request({
        "timestamp": "2026-09-27 17:17:06",
        "method": "POST",
        "url": "https://api.example.test/auth/login",
        "status_code": 0,
        "response_time_ms": 0,
        "right": 0,
        "wrong": 0,
        "exceptions": 1,
        "failure_detail": "connection failed",
    })

    assert recorded[1]["status_code"] == 500
    assert recorded[1]["response_body"] == "connection failed"


def test_auth_fixture_records_non_200_response_in_simple_report(monkeypatch):
    import fixtures.auth_fixture as auth_module
    import core.report_generator as report_generator

    class UnauthorizedResponse:
        status_code = 401
        text = '{"message":"Invalid credentials"}'
        headers = {"Content-Type": "application/json"}

        def json(self):
            return {"message": "Invalid credentials"}

    recorded = []
    monkeypatch.setattr(auth_module.requests, "post", lambda *args, **kwargs: UnauthorizedResponse())
    monkeypatch.setattr(report_generator, "add_record", recorded.append)
    monkeypatch.setenv("FITNESSE_PAGE_NAME", "AuthenticateUser")
    monkeypatch.setenv("FITNESSE_PAGE_PATH", "FrontPage.DummyAPI.AuthenticateUser")

    fixture = auth_module.AuthFixture()
    fixture.set_token_url("https://api.example.test/auth/login")

    assert fixture.generate_token() is False
    assert recorded[1]["url"] == "Send HTTP POST Request"
    assert recorded[1]["status_code"] == 500
    assert recorded[1]["page_name"] == "AuthenticateUser"
    assert recorded[1]["suite_name"] == "DummyAPI"
    assert recorded[2]["status_code"] == 401


def test_simple_report_renders_visual_comparison_images(monkeypatch, tmp_path):
    import core.report_generator as report_generator

    page = {
        "name": "VisualRegression.LoginScreen",
        "timestamp": "2026-09-27 18:00:00",
        "timestamp_raw": "20260927180000",
        "right": 1,
        "wrong": 0,
        "ignored": 0,
        "exceptions": 0,
    }
    record = {
        "timestamp": "2026-09-27 18:00:02",
        "method": "VISUAL",
        "url": "Visual comparison: swaglabs-login-screen",
        "status_code": 500,
        "response_time_ms": 0,
        "request_body": "FAIL: 1.25% of pixels changed",
        "response_body": (
            '<div class="visual-image-gallery">'
            '<img src="/files/testResults/visual-regression/baseline.png">'
            '<img src="/files/testResults/visual-regression/actual.png">'
            '<img src="/files/testResults/visual-regression/diff.png">'
            '</div>'
        ),
        "curl": "",
        "page_name": "LoginScreen",
        "suite_name": "VisualRegression",
        "json_file": "",
    }
    monkeypatch.setattr(report_generator, "scan_test_results", lambda: [page])
    monkeypatch.setattr(report_generator, "REPORT_FILE", str(tmp_path / "visual-report.html"))
    monkeypatch.setattr(report_generator, "report_history", [record])

    report_generator.generate_html_report()

    rendered = (tmp_path / "visual-report.html").read_text(encoding="utf-8")
    assert "Visual comparison: swaglabs-login-screen" in rendered
    assert "FAIL: 1.25% of pixels changed" in rendered
    assert rendered.count("/files/testResults/visual-regression/") == 3
    assert "CHANGED" in rendered
