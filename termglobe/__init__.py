"""
termglobe - Lightweight 3D ASCII globe renderer for terminal.

A minimal 3D rendering engine that displays a rotating globe
using ASCII characters, with geographic pin markers.

Basic usage:
    from termglobe import Globe, run

    globe = Globe()
    globe.add_pin(40.4168, -3.7038, "Madrid")
    run(globe)

Or from command line:
    python -m termglobe --pin 40.4168 -3.7038 Madrid --fps 30
"""

from .math_core import Vec3, Vec2, rot_y, rot_x, rot_z, project, latlon_to_xyz
from .renderer import Renderer, Buffer2D
from .globe_model import GlobeModel, GlobeWithGridlines, Pin
from .engine import Engine, RotationAxis
from .cli_adapter import CLIAdapter, main


class Globe:
    """High-level facade combining GlobeModel and Engine.

    Provides the simplest API for creating and running a globe.
    """

    def __init__(self, resolution: int = 20, use_gridlines: bool = True,
                 fps: float = 24.0, speed: float = 0.03,
                 camera_distance: float = 3.0):
        """
        Args:
            resolution: Sphere point density (default 20 = ~800 points).
            use_gridlines: Show meridian/parallel lines.
            fps: Target frames per second.
            speed: Rotation speed in radians/frame.
            camera_distance: Camera distance in radius units.
        """
        if use_gridlines:
            self._model = GlobeWithGridlines(resolution=resolution)
        else:
            self._model = GlobeModel(resolution=resolution)

        self._engine = Engine(
            globe=self._model,
            fps=fps,
            rotation_speed=speed,
            camera_distance=camera_distance,
            use_gridlines=False,  # globe already created
        )

    def add_pin(self, lat: float, lon: float, label: str = "") -> int:
        """Add a marker at geographic coordinates."""
        return self._engine.add_pin(lat, lon, label)

    def remove_pin(self, pid: int) -> bool:
        """Remove a marker by ID."""
        return self._engine.remove_pin(pid)

    def run(self):
        """Start the interactive render loop (blocking)."""
        adapter = CLIAdapter()
        adapter.engine = self._engine

        from .cli_adapter import KeyListener
        listener = KeyListener()
        listener.start()

        self._engine._cli_adapter = adapter
        adapter._listener = listener

        import sys
        sys.stderr.write("""
termglobe - 3D ASCII Globe
Controls:
  SPACE  Toggle rotation     r/s  Start/Stop
  +/-    Speed up/down       x/y/z  Rotation axis
  f      Cycle FPS           q    Quit
""")
        sys.stderr.flush()

        try:
            self._engine.start()
        finally:
            listener.stop()


def run(globe: Globe = None, **kwargs):
    """Convenience function to create and run a globe.

    Args:
        globe: Existing Globe instance (creates one if None).
        **kwargs: Passed to Globe() constructor if globe is None.
    """
    if globe is None:
        globe = Globe(**kwargs)
    globe.run()


__all__ = [
    "Globe",
    "run",
    "Vec3",
    "Vec2",
    "Renderer",
    "Buffer2D",
    "GlobeModel",
    "GlobeWithGridlines",
    "Pin",
    "Engine",
    "RotationAxis",
    "CLIAdapter",
    "main",
]

__version__ = "0.1.0"
