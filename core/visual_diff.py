"""Pixel-level screenshot comparison for local visual regression checks."""
from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageChops, ImageDraw


@dataclass(frozen=True)
class VisualDiffResult:
    passed: bool
    changed_pixels: int
    total_pixels: int
    changed_percent: float
    baseline_size: tuple[int, int]
    actual_size: tuple[int, int]
    diff_png: bytes


def compare_screenshots(
    baseline_png: bytes,
    actual_png: bytes,
    pixel_tolerance: int = 16,
    allowed_difference_percent: float = 0.2,
) -> VisualDiffResult:
    """Compare two PNG screenshots and return a red-highlighted diff image."""
    if not 0 <= pixel_tolerance <= 255:
        raise ValueError("pixel_tolerance must be between 0 and 255")
    if not 0 <= allowed_difference_percent <= 100:
        raise ValueError("allowed_difference_percent must be between 0 and 100")

    with Image.open(BytesIO(baseline_png)) as baseline_image:
        baseline = baseline_image.convert("RGB")
    with Image.open(BytesIO(actual_png)) as actual_image:
        actual = actual_image.convert("RGB")

    baseline_size = baseline.size
    actual_size = actual.size
    if baseline_size != actual_size:
        output_width = max(baseline.width, actual.width) * 2
        output_height = max(baseline.height, actual.height)
        diff_image = Image.new("RGB", (output_width, output_height), (24, 32, 40))
        diff_image.paste(baseline, (0, 0))
        diff_image.paste(actual, (max(baseline.width, actual.width), 0))
        draw = ImageDraw.Draw(diff_image)
        draw.rectangle((0, 0, baseline.width - 1, baseline.height - 1), outline=(255, 45, 80), width=4)
        draw.rectangle(
            (max(baseline.width, actual.width), 0,
             max(baseline.width, actual.width) + actual.width - 1, actual.height - 1),
            outline=(255, 45, 80),
            width=4,
        )
        output = BytesIO()
        diff_image.save(output, format="PNG")
        return VisualDiffResult(
            passed=False,
            changed_pixels=max(baseline.width * baseline.height, actual.width * actual.height),
            total_pixels=max(baseline.width * baseline.height, actual.width * actual.height),
            changed_percent=100.0,
            baseline_size=baseline_size,
            actual_size=actual_size,
            diff_png=output.getvalue(),
        )

    difference = ImageChops.difference(baseline, actual)
    channel_masks = [
        channel.point(lambda value: 255 if value > pixel_tolerance else 0)
        for channel in difference.split()
    ]
    mask = ImageChops.lighter(ImageChops.lighter(channel_masks[0], channel_masks[1]), channel_masks[2])
    changed_pixels = mask.histogram()[255]
    total_pixels = baseline.width * baseline.height
    changed_percent = (changed_pixels / total_pixels * 100) if total_pixels else 0.0

    diff_image = actual.copy()
    diff_image.paste(Image.new("RGB", actual.size, (255, 35, 75)), mask=mask)
    output = BytesIO()
    diff_image.save(output, format="PNG")

    return VisualDiffResult(
        passed=changed_percent <= allowed_difference_percent,
        changed_pixels=changed_pixels,
        total_pixels=total_pixels,
        changed_percent=changed_percent,
        baseline_size=baseline_size,
        actual_size=actual_size,
        diff_png=output.getvalue(),
    )