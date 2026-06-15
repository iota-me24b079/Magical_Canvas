"""Color tracking utilities for Virtual Air Canvas."""

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

import cv2
import numpy as np

from .color_ranges import HSVRange


Point = Tuple[int, int]


@dataclass(frozen=True)
class TrackingResult:
    """Result produced by the color tracker for one frame."""

    point: Optional[Point]
    contour: Optional[np.ndarray]
    mask: np.ndarray
    area: float = 0.0
    radius: float = 0.0


class ColorTracker:
    """Track the largest object matching one or more HSV ranges."""

    def __init__(
        self,
        hsv_ranges: Sequence[HSVRange],
        min_area: float = 900.0,
        kernel_size: int = 5,
    ) -> None:
        self.min_area = float(min_area)
        self.kernel_size = max(1, int(kernel_size))
        self.kernel = np.ones((self.kernel_size, self.kernel_size), dtype=np.uint8)
        self.set_ranges(hsv_ranges)

    def set_ranges(self, hsv_ranges: Sequence[HSVRange]) -> None:
        """Update the HSV ranges used for masking."""

        if not hsv_ranges:
            raise ValueError("At least one HSV range is required.")
        self.hsv_ranges = tuple(hsv_ranges)

    def build_mask(self, frame_bgr: np.ndarray) -> np.ndarray:
        """Create a cleaned binary mask for the configured HSV color ranges."""

        hsv_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        mask = np.zeros(hsv_frame.shape[:2], dtype=np.uint8)

        for hsv_range in self.hsv_ranges:
            lower = np.array(hsv_range.lower, dtype=np.uint8)
            upper = np.array(hsv_range.upper, dtype=np.uint8)
            range_mask = cv2.inRange(hsv_frame, lower, upper)
            mask = cv2.bitwise_or(mask, range_mask)

        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.kernel, iterations=2)
        return mask

    def track(self, frame_bgr: np.ndarray) -> TrackingResult:
        """Find the largest matching contour and return its center point."""

        mask = self.build_mask(frame_bgr)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return TrackingResult(point=None, contour=None, mask=mask)

        largest = max(contours, key=cv2.contourArea)
        area = float(cv2.contourArea(largest))

        if area < self.min_area:
            return TrackingResult(point=None, contour=largest, mask=mask, area=area)

        moments = cv2.moments(largest)
        if moments["m00"] != 0:
            center = (
                int(moments["m10"] / moments["m00"]),
                int(moments["m01"] / moments["m00"]),
            )
        else:
            (x_coord, y_coord), _ = cv2.minEnclosingCircle(largest)
            center = (int(x_coord), int(y_coord))

        _, radius = cv2.minEnclosingCircle(largest)
        return TrackingResult(
            point=center,
            contour=largest,
            mask=mask,
            area=area,
            radius=float(radius),
        )


def draw_tracking_feedback(frame: np.ndarray, result: TrackingResult) -> None:
    """Draw contour and center markers on a frame in place."""

    if result.contour is not None and result.area > 0:
        cv2.drawContours(frame, [result.contour], -1, (0, 255, 255), 2)

    if result.point is not None:
        cv2.circle(frame, result.point, 8, (0, 255, 255), -1)
        cv2.circle(frame, result.point, 14, (0, 255, 255), 2)
