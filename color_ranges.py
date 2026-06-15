"""HSV tracking presets and drawing colors."""

from dataclasses import dataclass
from typing import Dict, Tuple


HSVTuple = Tuple[int, int, int]
BGRColor = Tuple[int, int, int]


def _validate_hsv_triplet(label: str, value: HSVTuple) -> None:
    if len(value) != 3:
        raise ValueError(f"{label} must contain exactly three values.")

    limits = (179, 255, 255)
    for channel_value, maximum in zip(value, limits):
        if channel_value < 0 or channel_value > maximum:
            raise ValueError(
                f"{label} values must be within HSV limits: H 0-179, S 0-255, V 0-255."
            )


@dataclass(frozen=True)
class HSVRange:
    """Inclusive HSV lower and upper bounds for color masking."""

    lower: HSVTuple
    upper: HSVTuple

    def __post_init__(self) -> None:
        _validate_hsv_triplet("lower", self.lower)
        _validate_hsv_triplet("upper", self.upper)


COLOR_PRESETS: Dict[str, Tuple[HSVRange, ...]] = {
    "blue": (HSVRange((95, 80, 50), (130, 255, 255)),),
    "green": (HSVRange((40, 60, 50), (85, 255, 255)),),
    "yellow": (HSVRange((20, 80, 80), (35, 255, 255)),),
    "orange": (HSVRange((5, 100, 80), (20, 255, 255)),),
    "purple": (HSVRange((130, 60, 50), (160, 255, 255)),),
    "pink": (HSVRange((145, 60, 80), (175, 255, 255)),),
    # Red wraps around the HSV hue boundary, so it needs two ranges.
    "red": (
        HSVRange((0, 80, 50), (10, 255, 255)),
        HSVRange((170, 80, 50), (179, 255, 255)),
    ),
}


DRAWING_COLORS: Dict[str, BGRColor] = {
    "blue": (255, 0, 0),
    "green": (0, 190, 0),
    "red": (0, 0, 255),
    "yellow": (0, 230, 255),
    "white": (255, 255, 255),
}


def available_presets() -> Tuple[str, ...]:
    """Return preset names sorted for stable command-line help."""

    return tuple(sorted(COLOR_PRESETS.keys()))


def get_preset_ranges(name: str) -> Tuple[HSVRange, ...]:
    """Return HSV ranges for a named preset."""

    try:
        return COLOR_PRESETS[name.lower()]
    except KeyError as exc:
        choices = ", ".join(available_presets())
        raise ValueError(f"Unknown color preset '{name}'. Choose one of: {choices}") from exc


def format_hsv_range(hsv_range: HSVRange) -> str:
    """Format an HSV range as CLI-friendly comma-separated values."""

    values = (*hsv_range.lower, *hsv_range.upper)
    return ",".join(str(value) for value in values)
