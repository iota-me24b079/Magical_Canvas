import pytest

from virtual_air_canvas.color_ranges import HSVRange, available_presets, get_preset_ranges


def test_hsv_range_rejects_invalid_hue():
    with pytest.raises(ValueError):
        HSVRange((180, 0, 0), (179, 255, 255))


def test_blue_preset_is_available():
    assert "blue" in available_presets()
    assert get_preset_ranges("blue")
