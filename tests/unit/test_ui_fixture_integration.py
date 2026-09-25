from pathlib import Path

from fixtures.ui_fixture import UiFixture


def test_ui_fixture_can_initialize():
    fixture = UiFixture()

    assert fixture._default_browser == "chromium"
    assert fixture._page is None
    assert fixture._browser is None


def test_requirements_include_playwright():
    requirements_text = Path("requirements.txt").read_text(encoding="utf-8")

    assert "playwright" in requirements_text.lower()


def test_ui_fixture_browser_launch_and_close():
    fixture = UiFixture()
    try:
        fixture.start_browser()
        assert fixture._browser is not None
        assert fixture._page is not None
    finally:
        fixture.close_browser()

