from io import BytesIO

from PIL import Image

from core.visual_diff import compare_screenshots


def make_png(color, size=(8, 8)):
    image = Image.new("RGB", size, color)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_identical_images_pass_with_zero_changed_pixels():
    image = make_png((30, 60, 90))

    result = compare_screenshots(image, image)

    assert result.passed
    assert result.changed_pixels == 0
    assert result.changed_percent == 0


def test_changed_pixels_fail_when_over_the_allowed_percentage():
    baseline = make_png((30, 60, 90))
    changed_pixel = Image.new("RGB", (8, 8), (30, 60, 90))
    changed_pixel.putpixel((3, 4), (255, 0, 0))
    actual_buffer = BytesIO()
    changed_pixel.save(actual_buffer, format="PNG")

    result = compare_screenshots(
        baseline,
        actual_buffer.getvalue(),
        pixel_tolerance=0,
        allowed_difference_percent=0,
    )

    assert not result.passed
    assert result.changed_pixels == 1
    assert result.changed_percent > 0
    assert result.diff_png.startswith(b"\x89PNG")


def test_dimension_change_is_a_visual_failure():
    result = compare_screenshots(make_png((0, 0, 0), (8, 8)), make_png((0, 0, 0), (9, 8)))

    assert not result.passed
    assert result.changed_percent == 100
    assert result.baseline_size != result.actual_size