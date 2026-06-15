# Virtual Air Canvas

Virtual Air Canvas is a beginner-friendly OpenCV project that lets you draw on your screen by moving a colored object in front of your webcam. It tracks the object with HSV color masking, cleans the mask with morphological transformations, finds the largest contour, and converts the tracked movement into brush strokes.

## What You Will Learn

- Real-time webcam capture with OpenCV
- HSV color masking for object tracking
- Morphological opening and closing to clean noisy masks
- Contour detection and centroid tracking
- Drawing on a digital canvas with keyboard controls

## Features

- Track a colored object such as a blue cap, marker cap, or sticky note
- Draw, erase, clear, and save artwork
- Switch brush colors with keyboard shortcuts
- Optional mask preview window for learning and debugging
- Calibration mode with HSV sliders
- Clean project layout ready for GitHub

## Project Structure

```text
virtual-air-canvas/
├── main.py
├── pyproject.toml
├── requirements.txt
├── README.md
├── drawings/
│   └── .gitkeep
├── src/
│   └── virtual_air_canvas/
│       ├── __init__.py
│       ├── __main__.py
│       ├── app.py
│       ├── canvas.py
│       ├── color_ranges.py
│       └── tracker.py
└── tests/
    ├── conftest.py
    └── test_tracker.py
```

## Requirements

- Python 3.9 or newer
- A webcam
- A brightly colored object to track

## Setup

Clone the repository, create a virtual environment, and install the dependencies.

```bash
git clone https://github.com/your-username/virtual-air-canvas.git
cd virtual-air-canvas

python -m venv .venv
```

Activate the environment:

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the App

Start with the default blue object tracker:

```bash
python main.py
```

Show the mask window while running:

```bash
python main.py --show-mask
```

Track a different preset color:

```bash
python main.py --color green
python main.py --color red
python main.py --color yellow
```

Available tracking presets:

```text
blue, green, red, yellow, orange, purple, pink
```

## Controls

| Key | Action |
| --- | --- |
| `q` or `Esc` | Quit |
| `d` | Toggle drawing on or off |
| `c` | Clear the canvas |
| `s` | Save the drawing to `drawings/` |
| `e` | Toggle eraser mode |
| `1` | Blue brush |
| `2` | Green brush |
| `3` | Red brush |
| `4` | Yellow brush |
| `5` | White brush |
| `[` | Decrease brush size |
| `]` | Increase brush size |
| `h` | Toggle help overlay |
| `k` | Print HSV range in calibration mode |

## Calibration Mode

Lighting and cameras differ, so the default color ranges may need tuning. Calibration mode opens HSV sliders and a mask preview.

```bash
python main.py --calibrate --show-mask
```

Move your colored object in front of the webcam. Adjust the sliders until the object appears white in the mask window and the background stays mostly black.

Press `k` while the app is running to print the current HSV range in the terminal. Then run the app with that range:

```bash
python main.py --hsv 95,80,50,130,255,255
```

The format is:

```text
H_MIN,S_MIN,V_MIN,H_MAX,S_MAX,V_MAX
```

## Useful Command Options

```bash
python main.py --camera 1
python main.py --min-area 1200
python main.py --brush-size 12
python main.py --output-dir my_drawings
python main.py --no-mirror
```

| Option | Description |
| --- | --- |
| `--camera` | Webcam index, usually `0` for the default webcam |
| `--color` | Preset object color to track |
| `--hsv` | Custom HSV range that overrides `--color` |
| `--show-mask` | Show the binary mask window |
| `--calibrate` | Open HSV slider controls |
| `--min-area` | Ignore contours smaller than this area |
| `--brush-size` | Starting brush size |
| `--eraser-size` | Eraser thickness |
| `--output-dir` | Folder for saved drawings |
| `--no-mirror` | Disable mirror-style webcam display |

## Install as a CLI

You can also install the project in editable mode:

```bash
pip install -e .
air-canvas --color blue --show-mask
```

## Run Tests

Install the optional development dependency and run tests:

```bash
pip install -e ".[dev]"
pytest
```

The tests generate synthetic colored objects and verify that the tracker can detect or ignore them correctly.

## How It Works

1. The webcam frame is converted from BGR to HSV.
2. The selected HSV range creates a binary mask.
3. Morphological opening removes small white noise.
4. Morphological closing fills small gaps in the detected object.
5. The largest contour is selected as the tracked object.
6. The contour centroid becomes the brush position.
7. Consecutive brush positions are connected with lines on a canvas layer.

## Troubleshooting

- If the object is not detected, try `--show-mask` or `--calibrate`.
- If random background objects are detected, increase `--min-area` or improve lighting.
- If the webcam does not open, try `--camera 1` or close other apps using the camera.
- If drawing jumps around, use a larger object and keep it well lit.
- If colors look wrong, avoid shadows and reflective objects.

## Privacy

All webcam processing happens locally on your computer. The app does not upload frames or drawings anywhere.

## License

This project’s source code is released under the MIT License.
