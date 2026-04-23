"""
termglobe.engine - Render loop, FPS control, and state management.

Orchestrates the globe rotation, point transformation pipeline,
and coordinates between GlobeModel and Renderer.
"""

import math
import time
import signal
import sys
from typing import Optional, Callable, List, Tuple
from enum import Enum

from .math_core import Vec3, latlon_to_xyz
from .renderer import Renderer, PIN_CHAR
from .globe_model import GlobeModel, GlobeWithGridlines


class RotationAxis(Enum):
    Y = "y"
    X = "x"
    Z = "z"


class Engine:
    """Main engine that drives the render loop.

    Manages globe state (rotation angle, speed), FPS timing,
    and the per-frame pipeline: rotate -> cull -> project -> rasterize -> flush.

    The render pipeline is inlined for performance: instead of calling
    rot_y/rot_x/project per point (which creates Vec3/Vec2 objects),
    we operate on raw float tuples directly.
    """

    def __init__(self, globe: Optional[GlobeModel] = None,
                 renderer: Optional[Renderer] = None,
                 fps: float = 24.0,
                 rotation_speed: float = 0.03,
                 camera_distance: float = 3.0,
                 use_gridlines: bool = True):
        if globe is not None:
            self.globe = globe
        else:
            if use_gridlines:
                self.globe = GlobeWithGridlines()
            else:
                self.globe = GlobeModel()

        self.renderer = renderer or Renderer()
        self.target_fps = fps
        self.rotation_speed = rotation_speed
        self.camera_distance = camera_distance * self.globe.radius

        # State
        self._angle_y = 0.0
        self._angle_x = 0.0
        self._angle_z = 0.0
        self._rotating = True
        self._running = False
        self._axis = RotationAxis.Y

        # FPS tracking
        self._frame_time = 1.0 / fps
        self._last_fps = 0.0
        self._frame_count = 0
        self._fps_timer = 0.0

        # Resize handling
        self._resize_count = 0
        self._check_resize_every = 10

        # Precomputed flat arrays for fast rendering
        # Each point is stored as (x, y, z) tuple
        self._surface_xyz: List[Tuple[float, float, float]] = []
        self._grid_xyz: List[Tuple[float, float, float]] = []
        self._pin_xyz: List[Tuple[float, float, float]] = []
        self._rebuild_arrays()

        # Shading gradient
        self._shade = " .:-=+*#%@"
        self._shade_len = len(self._shade) - 1

    def _rebuild_arrays(self):
        """Convert Vec3 points to flat tuples for fast access."""
        self._surface_xyz = [(p.x, p.y, p.z) for p in self.globe.get_surface_points()]
        if isinstance(self.globe, GlobeWithGridlines):
            self._grid_xyz = [(p.x, p.y, p.z) for p in self.globe.get_grid_points()]
        else:
            self._grid_xyz = []
        self._pin_xyz = [(pin.xyz(self.globe.radius).x,
                          pin.xyz(self.globe.radius).y,
                          pin.xyz(self.globe.radius).z)
                         for pin in self.globe._pins]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self):
        """Start the render loop (blocking)."""
        self._running = True
        self.renderer.hide_cursor()
        self.renderer.clear_screen()

        try:
            if hasattr(signal, 'SIGWINCH'):
                signal.signal(signal.SIGWINCH, self._on_sigwinch)
        except (OSError, ValueError, AttributeError):
            pass

        try:
            self._loop()
        except KeyboardInterrupt:
            pass
        finally:
            self._cleanup()

    def stop(self):
        self._running = False

    def toggle_rotation(self):
        self._rotating = not self._rotating

    def set_rotation(self, on: bool):
        self._rotating = on

    def set_fps(self, fps: float):
        self.target_fps = max(1.0, min(60.0, fps))
        self._frame_time = 1.0 / self.target_fps

    def set_rotation_speed(self, speed: float):
        self.rotation_speed = speed

    def set_axis(self, axis: RotationAxis):
        self._axis = axis

    def add_pin(self, lat: float, lon: float, label: str = "") -> int:
        pid = self.globe.add_pin(lat, lon, label)
        self._rebuild_arrays()
        return pid

    def remove_pin(self, pid: int) -> bool:
        result = self.globe.remove_pin(pid)
        if result:
            self._rebuild_arrays()
        return result

    @property
    def fps(self) -> float:
        return self._last_fps

    @property
    def rotating(self) -> bool:
        return self._rotating

    @property
    def angle(self) -> float:
        return self._angle_y

    @property
    def axis(self) -> RotationAxis:
        return self._axis

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_sigwinch(self, signum, frame):
        self._resize_count += 1

    def _loop(self):
        while self._running:
            frame_start = time.monotonic()

            self._frame_count += 1
            if self._resize_count > 0 or self._frame_count % self._check_resize_every == 0:
                if self.renderer.check_resize():
                    self._resize_count = 0

            if self._rotating:
                if self._axis == RotationAxis.Y:
                    self._angle_y += self.rotation_speed
                elif self._axis == RotationAxis.X:
                    self._angle_x += self.rotation_speed
                elif self._axis == RotationAxis.Z:
                    self._angle_z += self.rotation_speed

            self._render_frame()

            elapsed = time.monotonic() - frame_start
            if elapsed < self._frame_time:
                time.sleep(self._frame_time - elapsed)

            now = time.monotonic()
            if now - self._fps_timer >= 1.0:
                self._last_fps = self._frame_count / (now - self._fps_timer)
                self._frame_count = 0
                self._fps_timer = now

    def _render_frame(self):
        """Optimized render: inline rotation and projection for speed."""
        buf = self.renderer.buffer
        buf.clear()

        cols = buf.cols
        rows = buf.rows
        half_cols = cols * 0.5
        half_rows = rows * 0.5

        # Scale: fit globe in 80% of available width
        # Use cols as primary constraint for a wider, more visible globe
        scale = cols * 0.35
        d = self.camera_distance
        r = self.globe.radius
        inv_r = 1.0 / r if r > 0 else 1.0

        # Precompute rotation sines/cosines
        ay = self._angle_y
        ax = self._angle_x
        az = self._angle_z

        cy = math.cos(ay); sy = math.sin(ay)
        cx = math.cos(ax); sx = math.sin(ax)
        cz = math.cos(az); sz = math.sin(az)

        shade = self._shade
        shade_len = self._shade_len
        char_buf = buf._char_buf
        depth_buf = buf._depth_buf
        pin_char = PIN_CHAR

        # Process all point sets in one loop
        all_points = self._surface_xyz + self._grid_xyz

        for px, py, pz in all_points:
            # Rot Y
            x1 = px * cy + pz * sy
            y1 = py
            z1 = -px * sy + pz * cy

            # Rot X
            x2 = x1
            y2 = y1 * cx - z1 * sx
            z2 = y1 * sx + z1 * cx

            # Rot Z
            x3 = x2 * cz - y2 * sz
            y3 = x2 * sz + y2 * cz
            z3 = z2

            # Visibility
            if z3 <= 0:
                continue

            # Projection
            denom = z3 + d
            if denom <= 1e-6:
                continue

            sx_f = x3 / denom * scale + half_cols
            sy_f = -y3 / denom * scale * 0.5 + half_rows

            col = int(sx_f)
            row = int(sy_f)

            if col < 0 or col >= cols or row < 0 or row >= rows:
                continue

            idx = row * cols + col
            if z3 < depth_buf[idx]:
                depth_buf[idx] = z3
                # Shading
                z_norm = z3 * inv_r
                if z_norm > 1.0:
                    z_norm = 1.0
                si = int(z_norm * shade_len)
                char_buf[idx] = shade[si]

        # Process pins (force draw on top)
        for px, py, pz in self._pin_xyz:
            x1 = px * cy + pz * sy
            y1 = py
            z1 = -px * sy + pz * cy

            x2 = x1
            y2 = y1 * cx - z1 * sx
            z2 = y1 * sx + z1 * cx

            x3 = x2 * cz - y2 * sz
            y3 = x2 * sz + y2 * cz
            z3 = z2

            if z3 <= 0:
                continue

            denom = z3 + d
            if denom <= 1e-6:
                continue

            col = int(x3 / denom * scale + half_cols)
            row = int(-y3 / denom * scale * 0.5 + half_rows)

            if 0 <= col < cols and 0 <= row < rows:
                idx = row * cols + col
                depth_buf[idx] = z3
                char_buf[idx] = pin_char

        # Flush
        self.renderer.flush()

    def _cleanup(self):
        self.renderer.show_cursor()
        self.renderer.clear_screen()
        print(f"\ntermglobe stopped. Last FPS: {self._last_fps:.1f}")
