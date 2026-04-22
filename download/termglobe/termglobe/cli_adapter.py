"""
termglobe.cli_adapter - Command-line interface and keyboard interaction.

Provides argument parsing, interactive keyboard control,
and the main entry point for running termglobe from the shell.
"""

import argparse
import sys
import os
import select
import termios
import tty
from typing import Optional

from .engine import Engine, RotationAxis
from .globe_model import GlobeModel, GlobeWithGridlines
from .renderer import Renderer


def _non_blocking_read() -> Optional[str]:
    """Read a single keypress from stdin without blocking.

    Returns None if no input available.
    Works on Linux/macOS with termios.
    """
    try:
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        if dr:
            return sys.stdin.read(1)
    except (OSError, ValueError):
        pass
    return None


class KeyListener:
    """Non-blocking keyboard listener using raw terminal mode.

    Sets terminal to raw mode for immediate key detection,
    restores original settings on cleanup.
    """

    def __init__(self):
        self._old_settings = None

    def start(self):
        """Enable raw terminal mode for key reading."""
        try:
            self._old_settings = termios.tcgetattr(sys.stdin.fileno())
            tty.setraw(sys.stdin.fileno())
        except (termios.error, AttributeError):
            self._old_settings = None

    def stop(self):
        """Restore original terminal settings."""
        if self._old_settings is not None:
            try:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN,
                                  self._old_settings)
            except (termios.error, AttributeError):
                pass

    def read_key(self) -> Optional[str]:
        """Read a key if available, non-blocking."""
        return _non_blocking_read()


class CLIAdapter:
    """Command-line interface for termglobe.

    Parses arguments, starts the engine with keyboard control,
    and provides the main() entry point.
    """

    def __init__(self):
        self.engine: Optional[Engine] = None
        self._listener = KeyListener()
        self._help_shown = False

    def build_parser(self) -> argparse.ArgumentParser:
        """Build the argument parser."""
        parser = argparse.ArgumentParser(
            prog="termglobe",
            description="Lightweight 3D ASCII globe renderer for terminal",
        )
        parser.add_argument("--pin", nargs="+", action="append",
                            metavar=("LAT", "LON"),
                            help="Add a pin: --pin LAT LON [LABEL]")
        parser.add_argument("--stop", action="store_true",
                            help="Start with rotation stopped")
        parser.add_argument("--fps", type=float, default=24.0,
                            help="Target FPS (default: 24)")
        parser.add_argument("--speed", type=float, default=0.03,
                            help="Rotation speed radians/frame (default: 0.03)")
        parser.add_argument("--axis", choices=["x", "y", "z"], default="y",
                            help="Rotation axis (default: y)")
        parser.add_argument("--resolution", type=int, default=20,
                            help="Sphere resolution (default: 20)")
        parser.add_argument("--distance", type=float, default=3.0,
                            help="Camera distance multiplier (default: 3.0)")
        parser.add_argument("--no-grid", action="store_true",
                            help="Disable meridian/parallel gridlines")
        parser.add_argument("--camera-distance", type=float, default=3.0,
                            help="Camera distance in radii (default: 3.0)")
        return parser

    def run(self, args=None):
        """Parse args and start the engine."""
        parser = self.build_parser()
        opts = parser.parse_args(args)

        # Create globe
        if opts.no_grid:
            globe = GlobeModel(resolution=opts.resolution)
        else:
            globe = GlobeWithGridlines(resolution=opts.resolution)

        # Add pins from command line
        if opts.pin:
            for pin_args in opts.pin:
                if len(pin_args) >= 2:
                    try:
                        lat = float(pin_args[0])
                        lon = float(pin_args[1])
                        label = pin_args[2] if len(pin_args) > 2 else ""
                        globe.add_pin(lat, lon, label)
                    except ValueError:
                        print(f"Invalid pin coordinates: {pin_args}", file=sys.stderr)

        # Create engine
        renderer = Renderer()
        self.engine = Engine(
            globe=globe,
            renderer=renderer,
            fps=opts.fps,
            rotation_speed=opts.speed,
            camera_distance=opts.camera_distance,
        )

        # Set initial state
        if opts.stop:
            self.engine.set_rotation(False)
        self.engine.set_axis(RotationAxis(opts.axis))

        # Add keyboard control to engine loop
        self.engine._on_key = self._handle_key

        # Start with help
        self._print_help()
        self._help_shown = True

        # Start keyboard listener
        self._listener.start()

        try:
            self.engine.start()
        finally:
            self._listener.stop()

    def _handle_key(self, key: str):
        """Handle keyboard input during render loop."""
        if key is None:
            return

        if key == " ":
            self.engine.toggle_rotation()
        elif key == "q" or key == "\x03":  # q or Ctrl+C
            self.engine.stop()
        elif key == "r":
            self.engine.set_rotation(True)
        elif key == "s":
            self.engine.set_rotation(False)
        elif key == "+":
            self.engine.set_rotation_speed(self.engine.rotation_speed + 0.005)
        elif key == "-":
            self.engine.set_rotation_speed(max(0.001, self.engine.rotation_speed - 0.005))
        elif key == "x":
            self.engine.set_axis(RotationAxis.X)
        elif key == "y":
            self.engine.set_axis(RotationAxis.Y)
        elif key == "z":
            self.engine.set_axis(RotationAxis.Z)
        elif key == "h" or key == "?":
            if not self._help_shown:
                self._print_help()
                self._help_shown = True
        elif key == "f":
            # Toggle FPS display (cycle fps)
            if self.engine.target_fps < 30:
                self.engine.set_fps(30)
            elif self.engine.target_fps < 50:
                self.engine.set_fps(50)
            else:
                self.engine.set_fps(20)

    def _print_help(self):
        """Print keyboard controls to stderr (won't interfere with render)."""
        help_text = """
termglobe - Controls:
  SPACE  Toggle rotation
  r/s    Start/Stop rotation
  +/-    Speed up / Slow down
  x/y/z  Change rotation axis
  f      Cycle FPS (20 -> 30 -> 50)
  h      Show this help
  q      Quit
"""
        sys.stderr.write(help_text)
        sys.stderr.flush()


# ---------------------------------------------------------------------------
# Engine integration: patch engine loop to read keys
# ---------------------------------------------------------------------------

_original_loop = Engine._loop


def _patched_loop(self):
    """Engine loop with keyboard reading."""
    listener = None
    adapter = getattr(self, '_cli_adapter', None)
    if adapter:
        listener = adapter._listener

    self._running = True
    self.renderer.hide_cursor()
    self.renderer.clear_screen()

    import time
    try:
        signal.signal(signal.SIGWINCH, self._on_sigwinch)
    except (OSError, ValueError):
        pass

    try:
        while self._running:
            frame_start = time.monotonic()

            # Check resize
            self._frame_count += 1
            if self._resize_count > 0 or self._frame_count % self._check_resize_every == 0:
                if self.renderer.check_resize():
                    self._resize_count = 0

            # Read keyboard
            if listener:
                key = listener.read_key()
                if key:
                    self._handle_key(key)

            # Update rotation
            if self._rotating:
                if self._axis == RotationAxis.Y:
                    self._angle_y += self.rotation_speed
                elif self._axis == RotationAxis.X:
                    self._angle_x += self.rotation_speed
                elif self._axis == RotationAxis.Z:
                    self._angle_z += self.rotation_speed

            # Render
            self._render_frame()

            # FPS control
            elapsed = time.monotonic() - frame_start
            if elapsed < self._frame_time:
                time.sleep(self._frame_time - elapsed)

            # FPS measurement
            now = time.monotonic()
            if now - self._fps_timer >= 1.0:
                self._last_fps = self._frame_count / (now - self._fps_timer)
                self._frame_count = 0
                self._fps_timer = now
    except KeyboardInterrupt:
        pass
    finally:
        self._cleanup()


# Patch the engine
Engine._loop = _patched_loop


def _handle_key(self, key: str):
    """Key handler attached to engine from CLIAdapter."""
    adapter = getattr(self, '_cli_adapter', None)
    if adapter:
        adapter._handle_key(key)


Engine._handle_key = _handle_key


def main():
    """Entry point for the termglobe command."""
    import signal

    adapter = CLIAdapter()

    # Create engine with keyboard support
    parser = adapter.build_parser()
    opts = parser.parse_args()

    # Create globe
    if opts.no_grid:
        globe = GlobeModel(resolution=opts.resolution)
    else:
        globe = GlobeWithGridlines(resolution=opts.resolution)

    # Add pins
    if opts.pin:
        for pin_args in opts.pin:
            if len(pin_args) >= 2:
                try:
                    lat = float(pin_args[0])
                    lon = float(pin_args[1])
                    label = pin_args[2] if len(pin_args) > 2 else ""
                    globe.add_pin(lat, lon, label)
                except ValueError:
                    sys.stderr.write(f"Invalid pin: {pin_args}\n")

    # Create engine
    renderer = Renderer()
    engine = Engine(
        globe=globe,
        renderer=renderer,
        fps=opts.fps,
        rotation_speed=opts.speed,
        camera_distance=opts.camera_distance,
    )
    engine._cli_adapter = adapter

    if opts.stop:
        engine.set_rotation(False)
    engine.set_axis(RotationAxis(opts.axis))

    # Add default pins for demo
    globe.add_pin(40.4168, -3.7038, "Madrid")
    globe.add_pin(40.7128, -74.0060, "NYC")
    globe.add_pin(-33.8688, 151.2093, "Sydney")
    globe.add_pin(35.6762, 139.6503, "Tokyo")

    adapter.engine = engine

    # Print help
    sys.stderr.write("""
termglobe - 3D ASCII Globe
Controls:
  SPACE  Toggle rotation     r/s  Start/Stop
  +/-    Speed up/down       x/y/z  Rotation axis
  f      Cycle FPS           q    Quit
""")
    sys.stderr.flush()

    # Start keyboard listener
    listener = KeyListener()
    listener.start()

    # Patch engine with listener
    engine._cli_adapter = adapter
    adapter._listener = listener

    try:
        engine.start()
    finally:
        listener.stop()


if __name__ == "__main__":
    main()
