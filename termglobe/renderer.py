"""
termglobe.renderer - Terminal rendering with ANSI color support and double buffering.

Renders colored ASCII globe: blue oceans, green/brown land, white ice caps,
with proper circular outline and flicker-free double buffering.
"""

import sys
import os
from typing import Optional

# Pin marker character
PIN_CHAR = "\u25cf"  # ●

# ANSI escape codes
ESC_CURSOR_HOME = "\033[H"
ESC_HIDE_CURSOR = "\033[?25l"
ESC_SHOW_CURSOR = "\033[?25h"
ESC_RESET = "\033[0m"
ESC_CLEAR = "\033[2J"

# ANSI 256-color codes
# Ocean: deep blue to medium blue
COLOR_OCEAN_DEEP = "\033[38;5;17m"    # very dark blue (edge/far)
COLOR_OCEAN_MID = "\033[38;5;19m"     # dark blue
COLOR_OCEAN_LIGHT = "\033[38;5;26m"   # medium blue (front/near)
# Land: dark green to bright green
COLOR_LAND_DEEP = "\033[38;5;22m"     # dark green (edge)
COLOR_LAND_MID = "\033[38;5;28m"      # medium green
COLOR_LAND_LIGHT = "\033[38;5;34m"    # bright green (front)
# Ice/snow
COLOR_ICE = "\033[38;5;231m"          # white
# Desert/arid
COLOR_DESERT = "\033[38;5;136m"       # tan/brown
# Pin marker
COLOR_PIN = "\033[38;5;196m"          # red
# Grid lines
COLOR_GRID = "\033[38;5;59m"          # dim gray-blue
# Border/outline
COLOR_BORDER = "\033[38;5;75m"        # light blue outline

# Terrain type constants
T_OCEAN = 0
T_LAND = 1
T_ICE = 2
T_DESERT = 3


def get_terminal_size() -> tuple:
    """Get terminal dimensions (columns, rows)."""
    try:
        size = os.get_terminal_size()
        return size.columns, size.lines
    except OSError:
        return 80, 24


class Buffer2D:
    """Double buffer with depth testing and ANSI color support.

    Each cell stores: character, color code, and depth value.
    """

    def __init__(self, cols: int = 80, rows: int = 24):
        self.cols = cols
        self.rows = rows
        self._char_buf: list = []
        self._color_buf: list = []
        self._depth_buf: list = []
        self._allocate()

    def _allocate(self):
        space = " "
        self._char_buf = [space] * (self.cols * self.rows)
        self._color_buf = [""] * (self.cols * self.rows)
        self._depth_buf = [float("inf")] * (self.cols * self.rows)

    def clear(self):
        space = " "
        for i in range(self.cols * self.rows):
            self._char_buf[i] = space
            self._color_buf[i] = ""
            self._depth_buf[i] = float("inf")

    def resize(self, cols: int, rows: int):
        self.cols = cols
        self.rows = rows
        self._allocate()

    def set_pixel(self, col: int, row: int, z: float, char: str,
                  color: str = "", force: bool = False):
        if col < 0 or col >= self.cols or row < 0 or row >= self.rows:
            return
        idx = row * self.cols + col
        if force or z < self._depth_buf[idx]:
            self._depth_buf[idx] = z
            self._char_buf[idx] = char
            self._color_buf[idx] = color

    def build_frame_string(self) -> str:
        """Build frame with ANSI color codes, minimizing escape sequences."""
        parts = [ESC_CURSOR_HOME]
        prev_color = None
        total = self.cols * self.rows

        for row in range(self.rows):
            start = row * self.cols
            end = start + self.cols
            for i in range(start, end):
                ch = self._char_buf[i]
                color = self._color_buf[i]
                if color != prev_color:
                    if color:
                        parts.append(color)
                    else:
                        parts.append(ESC_RESET)
                    prev_color = color
                parts.append(ch)
            if row < self.rows - 1:
                parts.append("\n")

        parts.append(ESC_RESET)
        return "".join(parts)


class Renderer:
    """High-level renderer with ANSI color support."""

    # Ocean shading chars (dark to bright)
    OCEAN_SHADE = " .:-~=#%"
    # Land shading chars
    LAND_SHADE = " .:,;+*#"
    # Ice shading chars
    ICE_SHADE = " .:-=+*#"
    # Desert shading chars
    DESERT_SHADE = " .:-=+*#"

    def __init__(self, pin_char: str = PIN_CHAR):
        self.pin_char = pin_char
        cols, rows = get_terminal_size()
        self.buffer = Buffer2D(cols, rows)

    @property
    def cols(self) -> int:
        return self.buffer.cols

    @property
    def rows(self) -> int:
        return self.buffer.rows

    def get_shade(self, terrain: int, z_norm: float) -> tuple:
        """Get (character, ANSI color) for a terrain type and depth.

        Args:
            terrain: T_OCEAN, T_LAND, T_ICE, or T_DESERT
            z_norm: 0.0 = edge (far), 1.0 = front (near)
        """
        if z_norm < 0:
            z_norm = 0.0
        if z_norm > 1.0:
            z_norm = 1.0

        if terrain == T_OCEAN:
            shade = self.OCEAN_SHADE
            n = len(shade) - 1
            si = int(z_norm * n)
            if z_norm < 0.3:
                color = COLOR_OCEAN_DEEP
            elif z_norm < 0.65:
                color = COLOR_OCEAN_MID
            else:
                color = COLOR_OCEAN_LIGHT
            return shade[si], color

        elif terrain == T_LAND:
            shade = self.LAND_SHADE
            n = len(shade) - 1
            si = int(z_norm * n)
            if z_norm < 0.3:
                color = COLOR_LAND_DEEP
            elif z_norm < 0.65:
                color = COLOR_LAND_MID
            else:
                color = COLOR_LAND_LIGHT
            return shade[si], color

        elif terrain == T_ICE:
            shade = self.ICE_SHADE
            n = len(shade) - 1
            si = int(z_norm * n)
            return shade[si], COLOR_ICE

        elif terrain == T_DESERT:
            shade = self.DESERT_SHADE
            n = len(shade) - 1
            si = int(z_norm * n)
            return shade[si], COLOR_DESERT

        return " ", ""

    def clear(self):
        self.buffer.clear()

    def flush(self, file=None):
        if file is None:
            file = sys.stdout
        frame = self.buffer.build_frame_string()
        file.write(frame)
        file.flush()

    def check_resize(self) -> bool:
        cols, rows = get_terminal_size()
        if cols != self.buffer.cols or rows != self.buffer.rows:
            self.buffer.resize(cols, rows)
            return True
        return False

    def hide_cursor(self, file=None):
        if file is None:
            file = sys.stdout
        file.write(ESC_HIDE_CURSOR)
        file.flush()

    def show_cursor(self, file=None):
        if file is None:
            file = sys.stdout
        file.write(ESC_SHOW_CURSOR)
        file.flush()

    def clear_screen(self, file=None):
        if file is None:
            file = sys.stdout
        file.write(ESC_CLEAR + ESC_CURSOR_HOME)
        file.flush()
