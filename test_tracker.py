import pytest

cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")

from virtual_air_canvas.color_ranges import get_preset_ranges
from virtual_air_canvas.tracker import ColorTracker


def test_blue_object_is_detected_near_its_center():
    frame = np.zeros((180, 240, 3), dtype=np.uint8)
    cv2.circle(frame, (120, 90), 22, (255, 0, 0), -1)

    tracker = ColorTracker(get_preset_ranges("blue"), min_area=100)
    result = tracker.track(frame)

    assert result.point is not None
    assert abs(result.point[0] - 120) <= 2
    assert abs(result.point[1] - 90) <= 2
    assert result.area > 100


def test_small_object_below_min_area_is_ignored():
    frame = np.zeros((180, 240, 3), dtype=np.uint8)
    cv2.circle(frame, (120, 90), 4, (255, 0, 0), -1)

    tracker = ColorTracker(get_preset_ranges("blue"), min_area=500)
    result = tracker.track(frame)

    assert result.point is None
    assert result.area < 500
