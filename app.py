"""Command-line app for Virtual Air Canvas."""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

import cv2

from .canvas import AirCanvas, BGRColor
from .color_ranges import (
    DRAWING_COLORS,
    HSVRange,
    available_presets,
    format_hsv_range,
    get_preset_ranges,
)
from .tracker import ColorTracker, draw_tracking_feedback


WINDOW_NAME = "Virtual Air Canvas"
MASK_WINDOW_NAME = "Color Mask"
CALIBRATION_WINDOW_NAME = "HSV Controls"

BRUSH_KEYS = {
    ord("1"): "blue",
    ord("2"): "green",
    ord("3"): "red",
    ord("4"): "yellow",
    ord("5"): "white",
}


def parse_hsv_range(value: str) -> HSVRange:
    """Parse CLI HSV range values in hmin,smin,vmin,hmax,smax,vmax format."""

    try:
        parts = tuple(int(part.strip()) for part in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("HSV values must be integers.") from exc

    if len(parts) != 6:
        raise argparse.ArgumentTypeError(
            "Use exactly six comma-separated values: H_MIN,S_MIN,V_MIN,H_MAX,S_MAX,V_MAX."
        )

    try:
        return HSVRange(parts[:3], parts[3:])
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Draw in the air by tracking a colored object with OpenCV."
    )
    parser.add_argument("--camera", type=int, default=0, help="Webcam index to use.")
    parser.add_argument(
        "--color",
        choices=available_presets(),
        default="blue",
        help="Preset object color to track.",
    )
    parser.add_argument(
        "--hsv",
        type=parse_hsv_range,
        help="Custom HSV range as H_MIN,S_MIN,V_MIN,H_MAX,S_MAX,V_MAX.",
    )
    parser.add_argument("--width", type=int, default=1280, help="Requested webcam width.")
    parser.add_argument("--height", type=int, default=720, help="Requested webcam height.")
    parser.add_argument("--min-area", type=float, default=900.0, help="Minimum contour area.")
    parser.add_argument(
        "--kernel-size",
        type=int,
        default=5,
        help="Morphological kernel size for mask cleanup.",
    )
    parser.add_argument("--brush-size", type=int, default=8, help="Starting brush size.")
    parser.add_argument("--eraser-size", type=int, default=35, help="Eraser thickness.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("drawings"),
        help="Directory where saved drawings are written.",
    )
    parser.add_argument("--show-mask", action="store_true", help="Show the binary mask window.")
    parser.add_argument("--calibrate", action="store_true", help="Show HSV calibration sliders.")
    parser.add_argument("--no-mirror", action="store_true", help="Disable mirrored webcam view.")
    return parser


def create_calibration_controls(initial_range: HSVRange) -> None:
    cv2.namedWindow(CALIBRATION_WINDOW_NAME)
    labels = ["H min", "S min", "V min", "H max", "S max", "V max"]
    values = [*initial_range.lower, *initial_range.upper]
    maximums = [179, 255, 255, 179, 255, 255]

    for label, value, maximum in zip(labels, values, maximums):
        cv2.createTrackbar(label, CALIBRATION_WINDOW_NAME, value, maximum, lambda _: None)


def read_calibration_range() -> HSVRange:
    h_min = cv2.getTrackbarPos("H min", CALIBRATION_WINDOW_NAME)
    s_min = cv2.getTrackbarPos("S min", CALIBRATION_WINDOW_NAME)
    v_min = cv2.getTrackbarPos("V min", CALIBRATION_WINDOW_NAME)
    h_max = cv2.getTrackbarPos("H max", CALIBRATION_WINDOW_NAME)
    s_max = cv2.getTrackbarPos("S max", CALIBRATION_WINDOW_NAME)
    v_max = cv2.getTrackbarPos("V max", CALIBRATION_WINDOW_NAME)

    lower = (min(h_min, h_max), min(s_min, s_max), min(v_min, v_max))
    upper = (max(h_min, h_max), max(s_min, s_max), max(v_min, v_max))
    return HSVRange(lower, upper)


def draw_hud(
    frame,
    tracking_label: str,
    brush_label: str,
    brush_size: int,
    drawing_enabled: bool,
    erasing: bool,
    show_help: bool,
    last_message: str,
) -> None:
    height, width = frame.shape[:2]
    panel_height = 122 if show_help else 62
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (width, panel_height), (30, 30, 30), -1)
    cv2.addWeighted(overlay, 0.72, frame, 0.28, 0, frame)

    mode = "ERASER" if erasing else "DRAW"
    drawing_state = "ON" if drawing_enabled else "OFF"
    status = (
        f"Track: {tracking_label} | Brush: {brush_label} {brush_size}px | "
        f"Mode: {mode} | Drawing: {drawing_state}"
    )
    cv2.putText(frame, status, (16, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2)

    if last_message:
        cv2.putText(
            frame,
            last_message[:80],
            (16, height - 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (255, 255, 255),
            2,
        )

    if not show_help:
        cv2.putText(
            frame,
            "Press h for controls",
            (16, 52),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (210, 210, 210),
            1,
        )
        return

    help_lines = [
        "q/Esc quit | d draw on/off | c clear | s save | e eraser | h hide help",
        "1 blue | 2 green | 3 red | 4 yellow | 5 white | [ smaller | ] larger",
        "Use --show-mask or --calibrate if tracking needs tuning.",
    ]

    y_coord = 54
    for line in help_lines:
        cv2.putText(
            frame,
            line,
            (16, y_coord),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (220, 220, 220),
            1,
        )
        y_coord += 27


def initial_tracking_ranges(args: argparse.Namespace) -> Tuple[HSVRange, ...]:
    if args.hsv is not None:
        return (args.hsv,)
    return get_preset_ranges(args.color)


def open_camera(args: argparse.Namespace):
    capture = cv2.VideoCapture(args.camera)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    return capture


def run(args: argparse.Namespace) -> int:
    tracking_ranges = initial_tracking_ranges(args)
    tracking_label = "custom HSV" if args.hsv else args.color
    tracker = ColorTracker(
        tracking_ranges,
        min_area=args.min_area,
        kernel_size=args.kernel_size,
    )

    capture = open_camera(args)
    if not capture.isOpened():
        print(
            f"Could not open webcam index {args.camera}. Try --camera 1 or close other camera apps.",
            file=sys.stderr,
        )
        return 1

    if args.calibrate:
        create_calibration_controls(tracking_ranges[0])

    active_brush = "blue"
    brush_color: BGRColor = DRAWING_COLORS[active_brush]
    brush_size = max(1, args.brush_size)
    erasing = False
    drawing_enabled = True
    show_help = True
    last_message = ""
    mirror = not args.no_mirror
    canvas = None

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                print("Could not read a frame from the webcam.", file=sys.stderr)
                return 1

            if mirror:
                frame = cv2.flip(frame, 1)

            if canvas is None:
                height, width = frame.shape[:2]
                canvas = AirCanvas(width=width, height=height)
            else:
                canvas.ensure_size(frame)

            if args.calibrate:
                current_range = read_calibration_range()
                tracker.set_ranges((current_range,))

            result = tracker.track(frame)

            if result.point is not None and drawing_enabled:
                current_size = args.eraser_size if erasing else brush_size
                canvas.draw(result.point, brush_color, current_size, erasing=erasing)
            else:
                canvas.lift_brush()

            display = canvas.composite(frame)
            draw_tracking_feedback(display, result)
            draw_hud(
                display,
                tracking_label,
                active_brush,
                brush_size,
                drawing_enabled,
                erasing,
                show_help,
                last_message,
            )

            cv2.imshow(WINDOW_NAME, display)
            if args.show_mask or args.calibrate:
                cv2.imshow(MASK_WINDOW_NAME, result.mask)

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                break
            if key == 255:
                continue

            if key == ord("d"):
                drawing_enabled = not drawing_enabled
                canvas.lift_brush()
            elif key == ord("c"):
                canvas.clear()
                last_message = "Canvas cleared"
            elif key == ord("s"):
                path = canvas.save(args.output_dir)
                last_message = f"Saved {path}"
            elif key == ord("e"):
                erasing = not erasing
                canvas.lift_brush()
            elif key == ord("h"):
                show_help = not show_help
            elif key == ord("["):
                brush_size = max(1, brush_size - 2)
            elif key == ord("]"):
                brush_size = min(60, brush_size + 2)
            elif key == ord("k") and args.calibrate:
                calibration_range = read_calibration_range()
                formatted = format_hsv_range(calibration_range)
                print(f"Current HSV range: --hsv {formatted}")
                last_message = f"HSV printed: {formatted}"
            elif key in BRUSH_KEYS:
                active_brush = BRUSH_KEYS[key]
                brush_color = DRAWING_COLORS[active_brush]
                erasing = False
                canvas.lift_brush()

    finally:
        capture.release()
        cv2.destroyAllWindows()

    return 0


def main(argv: List[str] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run(args)
