"""Canvas layer for air drawing."""

from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np


Point = Tuple[int, int]
BGRColor = Tuple[int, int, int]


class AirCanvas:
    """Maintain a transparent drawing layer over the webcam frame."""

    def __init__(self, width: int, height: int) -> None:
        self.canvas = np.zeros((height, width, 3), dtype=np.uint8)
        self.previous_point: Optional[Point] = None

    @property
    def width(self) -> int:
        return int(self.canvas.shape[1])

    @property
    def height(self) -> int:
        return int(self.canvas.shape[0])

    def ensure_size(self, frame: np.ndarray) -> None:
        """Reset the canvas if the camera frame size changes."""

        height, width = frame.shape[:2]
        if height != self.height or width != self.width:
            self.canvas = np.zeros((height, width, 3), dtype=np.uint8)
            self.lift_brush()

    def lift_brush(self) -> None:
        """Break the current stroke so the next point starts a new line."""

        self.previous_point = None

    def clear(self) -> None:
        """Remove all drawing strokes."""

        self.canvas[:] = 0
        self.lift_brush()

    def draw(
        self,
        point: Point,
        color: BGRColor,
        thickness: int,
        erasing: bool = False,
    ) -> None:
        """Draw or erase a line segment between the previous and current point."""

        point = self._clamp_point(point)
        draw_color = (0, 0, 0) if erasing else color
        thickness = max(1, int(thickness))

        if self.previous_point is None:
            self.previous_point = point
            cv2.circle(self.canvas, point, max(1, thickness // 2), draw_color, -1, cv2.LINE_AA)
            return

        cv2.line(self.canvas, self.previous_point, point, draw_color, thickness, cv2.LINE_AA)
        cv2.circle(self.canvas, point, max(1, thickness // 2), draw_color, -1, cv2.LINE_AA)
        self.previous_point = point

    def composite(self, frame: np.ndarray) -> np.ndarray:
        """Overlay the drawing layer on top of a webcam frame."""

        self.ensure_size(frame)
        mask = self._drawing_mask()
        inverse_mask = cv2.bitwise_not(mask)
        background = cv2.bitwise_and(frame, frame, mask=inverse_mask)
        drawing = cv2.bitwise_and(self.canvas, self.canvas, mask=mask)
        return cv2.add(background, drawing)

    def to_image(self, background: BGRColor = (255, 255, 255)) -> np.ndarray:
        """Return the artwork on a solid background."""

        image = np.full_like(self.canvas, background, dtype=np.uint8)
        mask = self._drawing_mask()
        image[mask > 0] = self.canvas[mask > 0]
        return image

    def save(self, output_dir: Path) -> Path:
        """Save the artwork as a PNG and return the saved path."""

        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = output_dir / f"air_canvas_{timestamp}.png"
        cv2.imwrite(str(path), self.to_image())
        return path

    def _drawing_mask(self) -> np.ndarray:
        gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
        return mask

    def _clamp_point(self, point: Point) -> Point:
        x_coord = min(max(0, int(point[0])), self.width - 1)
        y_coord = min(max(0, int(point[1])), self.height - 1)
        return x_coord, y_coord
