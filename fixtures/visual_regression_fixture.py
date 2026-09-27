"""Playwright fixture for approved, threshold-based visual regression checks."""
import datetime
import html
import os
import re
import uuid
from pathlib import Path
from typing import List

from core.allure_helper import AllureHelper
from core.logger import logger
from core.visual_diff import compare_screenshots
from .ui_fixture import UiFixture


class VisualRegressionFixture(UiFixture):
    """Capture a stable browser view and compare it to an explicitly approved baseline."""

    def __init__(self, page_name: str = "Visual Regression") -> None:
        super().__init__(page_name)
        self._default_browser = "chromium"
        self._default_headless = True
        self._force_headless = True
        self._viewport = {"width": 1280, "height": 800}
        self._baseline_dir = os.path.join(self._workspace_dir, "tests", "visual_baselines")
        self._artifact_dir = os.path.join(self._fitnesse_root, "files", "testResults", "visual-regression")
        self._allowed_difference_percent = 0.2
        self._pixel_tolerance = 16
        self._mask_selectors: List[str] = []
        self._update_baselines = False

    def set_allowed_difference_percent(self, percent: str) -> None:
        value = float(percent)
        if not 0 <= value <= 100:
            raise ValueError("Allowed visual difference must be between 0 and 100 percent")
        self._allowed_difference_percent = value

    def setAllowedDifferencePercent(self, percent: str) -> None:
        self.set_allowed_difference_percent(percent)

    def set_pixel_tolerance(self, value: str) -> None:
        tolerance = int(value)
        if not 0 <= tolerance <= 255:
            raise ValueError("Pixel tolerance must be between 0 and 255")
        self._pixel_tolerance = tolerance

    def setPixelTolerance(self, value: str) -> None:
        self.set_pixel_tolerance(value)

    def set_mask_selectors(self, selectors: str) -> None:
        self._mask_selectors = [selector.strip() for selector in str(selectors).split("||") if selector.strip()]

    def setMaskSelectors(self, selectors: str) -> None:
        self.set_mask_selectors(selectors)

    def set_update_baselines(self, enabled: str) -> None:
        self._update_baselines = str(enabled).strip().lower() in ("true", "yes", "1", "approved")

    def setUpdateBaselines(self, enabled: str) -> None:
        self.set_update_baselines(enabled)

    def _safe_snapshot_name(self, name: str) -> str:
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", str(name).strip()).strip(".-_")
        if not safe_name:
            raise ValueError("Snapshot name must contain at least one letter or number")
        return safe_name

    def _write_artifact(self, filename: str, image_bytes: bytes) -> str:
        os.makedirs(self._artifact_dir, exist_ok=True)
        file_path = os.path.join(self._artifact_dir, filename)
        with open(file_path, "wb") as image_file:
            image_file.write(image_bytes)
        return "/files/testResults/visual-regression/" + filename

    def _record_visual_result(
        self,
        snapshot_name: str,
        passed: bool,
        summary: str,
        baseline_url: str,
        actual_url: str,
        diff_url: str,
        actual_png: bytes,
        diff_png: bytes,
        baseline_png: bytes = b"",
    ) -> None:
        from core.report_generator import add_record

        status = "PASSED" if passed else "FAILED"
        status_code = 200 if passed else 500
        details = html.escape(summary)
        image_cards = []
        if baseline_url:
            image_cards.append(("Approved baseline", baseline_url))
        image_cards.extend((("Current capture", actual_url), ("Difference map", diff_url)))
        gallery = "".join(
            f'<figure class="visual-image"><figcaption>{html.escape(label)}</figcaption>'
            f'<a href="{html.escape(url, quote=True)}" target="_blank">'
            f'<img src="{html.escape(url, quote=True)}" alt="{html.escape(label, quote=True)}"></a></figure>'
            for label, url in image_cards
        )
        record_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        add_record({
            "timestamp": record_time,
            "method": "VISUAL",
            "url": f"Visual comparison: {snapshot_name}",
            "status_code": status_code,
            "response_time_ms": 0,
            "request_body": summary,
            "response_body": f'<div class="visual-result-summary">{details}</div><div class="visual-image-gallery">{gallery}</div>',
            "curl": "",
            "page_name": self._test_name or "Visual Regression",
            "suite_name": self._suite_name or "Visual Regression",
            "json_file": "",
        })

        if self._allure:
            self._allure.add_step(f"Visual comparison: {snapshot_name} ({status.lower()})", "passed" if passed else "failed")
            if baseline_png:
                self._allure.add_attachment(f"{snapshot_name} baseline", baseline_png, "image/png", "png")
            self._allure.add_attachment(f"{snapshot_name} current", actual_png, "image/png", "png")
            self._allure.add_attachment(f"{snapshot_name} diff", diff_png, "image/png", "png")
            if not passed:
                self._allure.set_failed(summary)

    def capture_and_compare(self, snapshot_name: str) -> bool:
        """Compare the current viewport to a named baseline; only explicit update mode writes baselines."""
        if not self._page:
            logger.error("[VisualRegression] No active browser page; call start browser first.")
            self._log_simple_step("Visual comparison failed: no active browser page", status="FAILED")
            return False

        try:
            safe_name = self._safe_snapshot_name(snapshot_name)
        except ValueError as error:
            logger.error(f"[VisualRegression] {error}")
            self._log_simple_step(str(error), status="FAILED")
            return False

        baseline_path = os.path.join(self._baseline_dir, f"{safe_name}.png")
        mask_locators = [self._page.locator(selector) for selector in self._mask_selectors]
        try:
            self._page.wait_for_load_state("load", timeout=15000)
            self._page.emulate_media(color_scheme="light", reduced_motion="reduce")
            self._page.evaluate("() => document.fonts ? document.fonts.ready : Promise.resolve()")
            actual_png = self._page.screenshot(
                animations="disabled",
                caret="hide",
                mask=mask_locators or None,
                mask_color="#7c3aed",
            )
        except Exception as error:
            message = f"Could not capture visual snapshot '{safe_name}': {error}"
            logger.error(f"[VisualRegression] {message}")
            self._log_simple_step(message, status="FAILED", body=message)
            return False

        run_id = uuid.uuid4().hex[:10]
        actual_url = self._write_artifact(f"{run_id}-{safe_name}-actual.png", actual_png)

        if self._update_baselines:
            os.makedirs(self._baseline_dir, exist_ok=True)
            temporary_path = baseline_path + ".tmp"
            with open(temporary_path, "wb") as baseline_file:
                baseline_file.write(actual_png)
            os.replace(temporary_path, baseline_path)
            comparison = compare_screenshots(actual_png, actual_png, self._pixel_tolerance, 100)
            baseline_png = actual_png
            summary = f"Baseline created/updated for {safe_name} at {self._viewport['width']}x{self._viewport['height']}."
            passed = True
        elif os.path.isfile(baseline_path):
            with open(baseline_path, "rb") as baseline_file:
                baseline_png = baseline_file.read()
            comparison = compare_screenshots(
                baseline_png,
                actual_png,
                self._pixel_tolerance,
                self._allowed_difference_percent,
            )
            passed = comparison.passed
            summary = (
                f"{'PASS' if passed else 'FAIL'}: {safe_name} changed {comparison.changed_percent:.3f}% "
                f"({comparison.changed_pixels}/{comparison.total_pixels} pixels); "
                f"allowed {self._allowed_difference_percent:.3f}%. "
                f"Baseline {comparison.baseline_size[0]}x{comparison.baseline_size[1]}, "
                f"current {comparison.actual_size[0]}x{comparison.actual_size[1]}."
            )
        else:
            from PIL import Image
            from io import BytesIO

            current_image = Image.open(BytesIO(actual_png)).convert("RGB")
            red_image = Image.new("RGB", current_image.size, (255, 35, 75))
            current_image.paste(red_image, mask=Image.new("L", current_image.size, 255))
            diff_buffer = BytesIO()
            current_image.save(diff_buffer, format="PNG")
            comparison = None
            baseline_png = b""
            passed = False
            summary = f"FAIL: No approved baseline exists for {safe_name}. Run the separate VisualRegressionBaselineRefresh suite to approve one."

        if self._update_baselines:
            diff_png = comparison.diff_png
            baseline_url = self._write_artifact(f"{run_id}-{safe_name}-baseline.png", baseline_png)
        elif comparison:
            diff_png = comparison.diff_png
            baseline_url = self._write_artifact(f"{run_id}-{safe_name}-baseline.png", baseline_png)
        else:
            diff_png = diff_buffer.getvalue()
            baseline_url = ""

        diff_url = self._write_artifact(f"{run_id}-{safe_name}-diff.png", diff_png)
        self._record_visual_result(
            safe_name,
            passed,
            summary,
            baseline_url,
            actual_url,
            diff_url,
            actual_png,
            diff_png,
            baseline_png,
        )
        return passed

    def captureAndCompare(self, snapshot_name: str) -> bool:
        return self.capture_and_compare(snapshot_name)