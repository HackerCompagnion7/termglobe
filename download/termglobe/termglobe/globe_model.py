"""
termglobe.globe_model - Sphere point generation and geographic markers.

Generates the point cloud for the globe surface, manages pin markers
at geographic coordinates, and provides meridian/parallel lines.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .math_core import Vec3, latlon_to_xyz, TrigCache


@dataclass
class Pin:
    """A geographic marker on the globe."""
    lat: float
    lon: float
    label: str = ""
    _id: int = 0

    def xyz(self, r: float = 1.0) -> Vec3:
        return latlon_to_xyz(self.lat, self.lon, r)


# Pin ID counter
_next_pin_id = 0


def _new_pin_id() -> int:
    global _next_pin_id
    _next_pin_id += 1
    return _next_pin_id


class GlobeModel:
    """Sphere model with configurable resolution and pin markers.

    Points are generated once and cached. Pins are added/removed
    dynamically. The get_points() method returns the combined
    list of surface points and pin points.
    """

    def __init__(self, resolution: int = 20, radius: float = 1.0):
        self.resolution = resolution
        self.radius = radius
        self._pins: List[Pin] = []
        self._surface_points: List[Vec3] = []
        self._generate_surface()

    def _generate_surface(self):
        """Generate sphere point cloud from trig cache."""
        self._surface_points = []
        cache = TrigCache(self.resolution)
        n_lat = self.resolution
        n_lon = 2 * self.resolution

        for i in range(n_lat):
            cos_phi = cache.cos_phi[i]
            sin_phi = cache.sin_phi[i]
            for j in range(n_lon):
                cos_lam = cache.cos_lam[j]
                sin_lam = cache.sin_lam[j]
                self._surface_points.append(Vec3(
                    self.radius * cos_phi * cos_lam,
                    self.radius * sin_phi,
                    self.radius * cos_phi * sin_lam,
                ))

    def set_resolution(self, resolution: int):
        """Change resolution and regenerate."""
        self.resolution = resolution
        self._generate_surface()

    def add_pin(self, lat: float, lon: float, label: str = "") -> int:
        """Add a marker at geographic coordinates.

        Args:
            lat: Latitude in degrees (-90 to 90).
            lon: Longitude in degrees (-180 to 180).
            label: Optional label text.

        Returns:
            Pin ID for later removal.
        """
        pid = _new_pin_id()
        pin = Pin(lat=lat, lon=lon, label=label, _id=pid)
        self._pins.append(pin)
        return pid

    def remove_pin(self, pid: int) -> bool:
        """Remove a pin by its ID.

        Returns:
            True if found and removed.
        """
        for i, pin in enumerate(self._pins):
            if pin._id == pid:
                self._pins.pop(i)
                return True
        return False

    def clear_pins(self):
        """Remove all pins."""
        self._pins.clear()

    def get_surface_points(self) -> List[Vec3]:
        """Return cached surface points."""
        return self._surface_points

    def get_pin_points(self) -> List[Tuple[Vec3, Pin]]:
        """Return pin 3D positions with their Pin objects."""
        return [(pin.xyz(self.radius), pin) for pin in self._pins]

    @property
    def point_count(self) -> int:
        return len(self._surface_points) + len(self._pins)

    @property
    def pin_count(self) -> int:
        return len(self._pins)


class GlobeWithGridlines(GlobeModel):
    """Extended globe with meridian and parallel lines.

    Generates extra points along key geographic lines,
    marked with a distinct character.
    """

    def __init__(self, resolution: int = 20, radius: float = 1.0,
                 meridians: Optional[List[float]] = None,
                 parallels: Optional[List[float]] = None):
        """
        Args:
            resolution: Base sphere resolution.
            radius: Sphere radius.
            meridians: Longitudes for meridian lines (degrees).
            parallels: Latitudes for parallel lines (degrees).
        """
        self._meridians = meridians or [0, -30, 30, -60, 60, -90, 90, -120, 120, -150, 150, 180]
        self._parallels = parallels or [0, 23.44, -23.44, 45, -45, 66.56, -66.56]
        self._grid_points: List[Vec3] = []
        super().__init__(resolution, radius)
        self._generate_gridlines()

    def _generate_gridlines(self):
        """Generate points along meridians and parallels.

        Uses coarse step (8 degrees) to keep point count low.
        Grid points are only visual accents, not high-res lines.
        """
        self._grid_points = []
        # Meridians: lines of constant longitude (every 8 degrees of lat)
        for lon in self._meridians:
            for lat_step in range(-90, 91, 8):
                self._grid_points.append(latlon_to_xyz(lat_step, lon, self.radius))
        # Parallels: lines of constant latitude (every 8 degrees of lon)
        for lat in self._parallels:
            for lon_step in range(-180, 181, 8):
                self._grid_points.append(latlon_to_xyz(lat, lon_step, self.radius))

    def get_grid_points(self) -> List[Vec3]:
        """Return gridline points."""
        return self._grid_points

    def set_resolution(self, resolution: int):
        """Override to also regenerate gridlines."""
        super().set_resolution(resolution)
        self._generate_gridlines()
