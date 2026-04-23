"""
termglobe.engine - Render loop with colored Earth globe rendering.

Orchestrates rotation, perspective projection, terrain-based coloring,
circular outline drawing, and depth-sorted ASCII rendering.
"""

import math
import time
import signal
import sys
from typing import Optional, Callable, List, Tuple
from enum import Enum

from .math_core import Vec3, latlon_to_xyz
from .renderer import (Renderer, PIN_CHAR, T_OCEAN, T_LAND, T_ICE, T_DESERT,
                       COLOR_PIN, COLOR_GRID, COLOR_BORDER, COLOR_OCEAN_DEEP)
from .globe_model import GlobeModel, GlobeWithGridlines


class RotationAxis(Enum):
    Y = "y"
    X = "x"
    Z = "z"


class Engine:
    """Main engine that drives the colored render loop.

    Renders an Earth-like globe with:
    - Blue oceans, green land, white ice, tan desert
    - Proper circular outline
    - Perspective shading (brighter = closer)
    - Pin markers in red
    - Gridlines in dim gray
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

        # Precomputed flat arrays
        self._surface_xyz: List[Tuple[float, float, float]] = []
        self._surface_terrain: List[int] = []
        self._grid_xyz: List[Tuple[float, float, float]] = []
        self._pin_xyz: List[Tuple[float, float, float]] = []
        self._rebuild_arrays()

    def _rebuild_arrays(self):
        """Convert model data to flat arrays for fast rendering."""
        self._surface_xyz = [(p.x, p.y, p.z) for p in self.globe.get_surface_points()]
        self._surface_terrain = list(self.globe._surface_terrain)
        if isinstance(self.globe, GlobeWithGridlines):
            self._grid_xyz = list(self.globe.get_grid_points())
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
        """Render the colored Earth globe with proper circular shape."""
        buf = self.renderer.buffer
        buf.clear()

        cols = buf.cols
        rows = buf.rows
        half_cols = cols * 0.5
        half_rows = rows * 0.5

        # Scale: make the globe fill the terminal nicely
        # Characters are ~2:1 (taller than wide), so we adjust
        min_dim = min(cols, rows * 2)  # account for char aspect ratio
        scale = min_dim * 0.7
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

        char_buf = buf._char_buf
        color_buf = buf._color_buf
        depth_buf = buf._depth_buf

        # ---- Step 1: Draw circular outline ----
        # The outline is the silhouette of the sphere.
        # For a sphere of radius r at camera distance d,
        # the projected radius is: r * scale / d
        proj_r = r / d * scale
        proj_r_y = proj_r * 0.5  # aspect ratio correction

        # Draw outline using Bresenham-like circle algorithm
        n_outline = max(60, int(proj_r * 4))
        for i in range(n_outline):
            angle = 2 * math.pi * i / n_outline
            oc = int(half_cols + proj_r * math.cos(angle))
            orow = int(half_rows - proj_r_y * math.sin(angle))
            if 0 <= oc < cols and 0 <= orow < rows:
                idx = orow * cols + oc
                # Outline goes at depth = 0 (edge of sphere)
                if depth_buf[idx] > 0.01:
                    depth_buf[idx] = 0.01
                    char_buf[idx] = "@"
                    color_buf[idx] = COLOR_BORDER

        # ---- Step 2: Render surface points with terrain colors ----
        surface = self._surface_xyz
        terrain = self._surface_terrain
        n_pts = len(surface)

        for pi in range(n_pts):
            px, py, pz = surface[pi]
            t = terrain[pi]

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

            # Only render front-facing points
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
                # Normalized depth for shading
                z_norm = z3 * inv_r
                if z_norm > 1.0:
                    z_norm = 1.0
                # Get shade char and color from renderer
                ch, color = self.renderer.get_shade(t, z_norm)
                char_buf[idx] = ch
                color_buf[idx] = color

        # ---- Step 3: Render gridlines ----
        for px, py, pz in self._grid_xyz:
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
                # Gridlines only overwrite ocean, not land
                if depth_buf[idx] != float("inf") and char_buf[idx] != "@" :
                    if z3 < depth_buf[idx] * 1.05:  # slight tolerance
                        depth_buf[idx] = z3
                        char_buf[idx] = ":"
                        color_buf[idx] = COLOR_GRID

        # ---- Step 4: Render pins (always on top) ----
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
                char_buf[idx] = PIN_CHAR
                color_buf[idx] = COLOR_PIN

        # Flush
        self.renderer.flush()

    def _cleanup(self):
        self.renderer.show_cursor()
        self.renderer.clear_screen()
        print(f"\ntermglobe stopped. Last FPS: {self._last_fps:.1f}")
