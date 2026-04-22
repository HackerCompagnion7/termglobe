"""
termglobe.renderer - Terminal rendering with double buffering and ASCII shading.

Manages the 2D character buffer, depth buffer, shading gradient,
and ANSI escape sequences for flicker-free rendering.
"""

import sys
import os
from typing import Optional

# ASCII shading gradient: from dim (far) to bright (near)
DEFAULT_SHADE = " .:-=+*#%@"

# Pin marker character
PIN_CHAR = "\u25cf"  # ●

# ANSI escape codes
ESC_CURSOR_HOME = "\033[H"
ESC_HIDE_CURSOR = "\033[?25l"
ESC_SHOW_CURSOR = "\033[?25h"
ESC_RESET = "\033[0m"
ESC_CLEAR = "\033[2J"


def get_terminal_size() -> tuple:
    """Get terminal dimensions (columns, rows)."""
    try:
        size = os.get_terminal_size()
        return size.columns, size.lines
    except OSError:
        return 80, 24


class Buffer2D:
    """Double buffer with depth testing for ASCII rendering.

    Each cell stores a character and a depth value (z).
    When writing, a pixel is only accepted if its z is closer
    (lower) than the existing value.
    """

    def __init__(self, cols: int = 80, rows: int = 24):
        self.cols = cols
        self.rows = rows
        self._char_buf: list = []
        self._depth_buf: list = []
        self._allocate()

    def _allocate(self):
        """Allocate buffer arrays."""
        space = " "
        self._char_buf = [space] * (self.cols * self.rows)
        self._depth_buf = [float("inf")] * (self.cols * self.rows)

    def clear(self):
        """Reset both buffers for a new frame."""
        space = " "
        for i in range(self.cols * self.rows):
            self._char_buf[i] = space
            self._depth_buf[i] = float("inf")

    def resize(self, cols: int, rows: int):
        """Resize buffers (re-allocates)."""
        self.cols = cols
        self.rows = rows
        self._allocate()

    def set_pixel(self, col: int, row: int, z: float, char: str, force: bool = False):
        """Write a pixel if it passes the depth test.

        Args:
            col: Column index (0-based).
            row: Row index (0-based).
            z: Depth value (lower = closer).
            char: Character to write.
            force: If True, skip depth test (for pins etc.).
        """
        if col < 0 or col >= self.cols or row < 0 or row >= self.rows:
            return
        idx = row * self.cols + col
        if force or z < self._depth_buf[idx]:
            self._depth_buf[idx] = z
            self._char_buf[idx] = char

    def get_char(self, col: int, row: int) -> str:
        """Get character at position."""
        if col < 0 or col >= self.cols or row < 0 or row >= self.rows:
            return " "
        return self._char_buf[row * self.cols + col]

    def build_frame_string(self) -> str:
        """Build the complete frame as a single string with cursor movement.

        Uses ESC[H to move cursor home and writes row-by-row.
        """
        lines = []
        for row in range(self.rows):
            start = row * self.cols
            end = start + self.cols
            line = "".join(self._char_buf[start:end])
            lines.append(line)
        return ESC_CURSOR_HOME + "\n".join(lines)


class Renderer:
    """High-level renderer that combines buffer, shading, and output.

    Renders 3D points onto the ASCII buffer with perspective
    projection, depth testing, and ASCII shading.
    """

    def __init__(self, shade: str = DEFAULT_SHADE, pin_char: str = PIN_CHAR):
        self.shade = shade
        self.pin_char = pin_char
        cols, rows = get_terminal_size()
        self.buffer = Buffer2D(cols, rows)

    @property
    def cols(self) -> int:
        return self.buffer.cols

    @property
    def rows(self) -> int:
        return self.buffer.rows

    def shade_char(self, z_norm: float) -> str:
        """Map normalized depth [0,1] to ASCII shade character.

        Args:
            z_norm: 0 = farthest (edge), 1 = closest (front).

        Returns:
            Single character from the shade gradient.
        """
        if z_norm < 0:
            z_norm = 0.0
        if z_norm > 1:
            z_norm = 1.0
        idx = int(z_norm * (len(self.shade) - 1))
        return self.shade[idx]

    def clear(self):
        """Clear buffer for new frame."""
        self.buffer.clear()

    def draw_point(self, screen_x: float, screen_y: float,
                   z_depth: float, z_norm: float, is_pin: bool = False):
        """Project a screen-space point onto the buffer.

        Args:
            screen_x: Projected X coordinate (0 = center).
            screen_y: Projected Y coordinate (0 = center).
            z_depth: Raw z value for depth testing.
            z_norm: Normalized z [0,1] for shading.
            is_pin: If True, draw pin marker instead of shade.
        """
        # Convert from centered coords to buffer coords
        # Character aspect ratio: chars are ~2x taller than wide
        # so we compensate by halving the y offset
        col = int(screen_x + self.cols / 2)
        row = int(-screen_y * 0.5 + self.rows / 2)  # flip Y, half for aspect

        char = self.pin_char if is_pin else self.shade_char(z_norm)
        self.buffer.set_pixel(col, row, z_depth, char, force=is_pin)

    def flush(self, file=None):
        """Write the frame to stdout with cursor home positioning."""
        if file is None:
            file = sys.stdout
        frame = self.buffer.build_frame_string()
        file.write(frame)
        file.flush()

    def check_resize(self) -> bool:
        """Check if terminal resized and update buffers.

        Returns:
            True if resized.
        """
        cols, rows = get_terminal_size()
        if cols != self.buffer.cols or rows != self.buffer.rows:
            self.buffer.resize(cols, rows)
            return True
        return False

    def hide_cursor(self, file=None):
        """Hide the terminal cursor."""
        if file is None:
            file = sys.stdout
        file.write(ESC_HIDE_CURSOR)
        file.flush()

    def show_cursor(self, file=None):
        """Show the terminal cursor."""
        if file is None:
            file = sys.stdout
        file.write(ESC_SHOW_CURSOR)
        file.flush()

    def clear_screen(self, file=None):
        """Clear the entire terminal screen."""
        if file is None:
            file = sys.stdout
        file.write(ESC_CLEAR + ESC_CURSOR_HOME)
        file.flush()
