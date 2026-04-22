#!/usr/bin/env python3
"""
termglobe demo - Render one static frame to verify the globe looks correct.

This is a non-interactive test that prints a single frame to stdout.
For the interactive version, use: python -m termglobe
"""

import sys
import os

# Force a known terminal size for consistent output
os.environ.setdefault("COLUMNS", "80")
os.environ.setdefault("LINES", "24")

from termglobe.globe_model import GlobeWithGridlines
from termglobe.engine import Engine
from termglobe.renderer import Renderer, ESC_CURSOR_HOME, ESC_SHOW_CURSOR


def main():
    # Create globe with gridlines
    globe = GlobeWithGridlines(resolution=20)

    # Add some famous cities as pins
    globe.add_pin(40.4168, -3.7038, "Madrid")
    globe.add_pin(51.5074, -0.1278, "London")
    globe.add_pin(48.8566, 2.3522, "Paris")
    globe.add_pin(40.7128, -74.0060, "New York")
    globe.add_pin(35.6762, 139.6503, "Tokyo")
    globe.add_pin(-33.8688, 151.2093, "Sydney")
    globe.add_pin(-22.9068, -43.1729, "Rio")
    globe.add_pin(55.7558, 37.6173, "Moscow")

    # Create renderer and engine
    renderer = Renderer()
    engine = Engine(globe=globe, renderer=renderer, fps=24,
                    rotation_speed=0.03, camera_distance=3.0)

    # Render frames at different angles
    angles = [0.0, 0.8, 1.6, 2.4, 3.2, 4.0, 5.0]

    print("termglobe - Static Frame Demo")
    print(f"Resolution: {globe.resolution} | Points: {globe.point_count} | Pins: {globe.pin_count}")
    print("=" * 60)

    for i, angle in enumerate(angles):
        engine._angle_y = angle
        engine._render_frame()

        # Get the frame as plain text (strip ANSI)
        frame = renderer.buffer.build_frame_string()
        # Remove ESC sequences for display
        clean = frame.replace(ESC_CURSOR_HOME, "")
        print(f"\n--- Frame {i+1}, angle={angle:.1f} rad ---")
        print(clean)

    print(f"\n{ESC_SHOW_CURSOR}")
    print("Demo complete! For interactive mode: python -m termglobe")


if __name__ == "__main__":
    main()
