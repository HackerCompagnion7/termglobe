"""
termglobe.globe_model - Sphere point generation with Earth terrain.

Generates the point cloud for the globe surface with realistic
terrain classification: ocean, land, ice, desert. Each surface
point knows its terrain type for colored rendering.
"""

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .math_core import Vec3, latlon_to_xyz, TrigCache
from .renderer import T_OCEAN, T_LAND, T_ICE, T_DESERT


@dataclass
class Pin:
    """A geographic marker on the globe."""
    lat: float
    lon: float
    label: str = ""
    _id: int = 0

    def xyz(self, r: float = 1.0) -> Vec3:
        return latlon_to_xyz(self.lat, self.lon, r)


_next_pin_id = 0


def _new_pin_id() -> int:
    global _next_pin_id
    _next_pin_id += 1
    return _next_pin_id


# ---------------------------------------------------------------------------
# Simplified Earth continent map
# Each entry: (lat_min, lat_max, lon_min, lon_max, terrain_type)
# This is a rough approximation of Earth's land masses.
# ---------------------------------------------------------------------------

_CONTINENTS = [
    # North America
    (25, 50, -130, -65, T_LAND),      # USA main
    (50, 72, -170, -55, T_LAND),      # Canada/Alaska
    (15, 25, -105, -80, T_LAND),      # Mexico
    (7, 15, -90, -77, T_LAND),        # Central America
    # Greenland
    (60, 84, -75, -10, T_ICE),
    # South America
    (-5, 12, -80, -50, T_LAND),       # Northern SA
    (-25, -5, -80, -35, T_LAND),      # Brazil etc
    (-40, -25, -72, -48, T_LAND),     # Southern SA
    (-55, -40, -75, -62, T_LAND),     # Patagonia
    # Europe
    (36, 45, -10, 3, T_LAND),         # Iberia
    (43, 60, -10, 30, T_LAND),        # Western/Central Europe
    (55, 72, 5, 40, T_LAND),          # Scandinavia/Russia west
    (36, 43, 10, 30, T_LAND),         # Italy/Balkans
    (36, 42, 25, 45, T_LAND),         # Turkey
    # Africa
    (20, 37, -17, 40, T_DESERT),      # North Africa (Sahara)
    (5, 20, -17, 50, T_LAND),         # West/Central Africa
    (-5, 5, 8, 42, T_LAND),           # East Africa
    (-35, -5, 12, 42, T_LAND),        # Southern Africa
    # Middle East
    (12, 37, 35, 60, T_DESERT),       # Arabian Peninsula/Iran
    (37, 45, 40, 75, T_LAND),         # Central Asia
    # Russia / Siberia
    (45, 75, 30, 180, T_LAND),        # Russia
    (50, 75, -180, -170, T_LAND),     # Russia far east
    # South/Southeast Asia
    (8, 35, 68, 92, T_LAND),          # India
    (20, 55, 75, 135, T_LAND),        # China/Mongolia
    (10, 20, 92, 110, T_LAND),        # Indochina
    (-8, 10, 95, 140, T_LAND),        # Indonesia/Malaysia
    (30, 45, 128, 146, T_LAND),       # Japan/Korea
    # Australia
    (-40, -12, 112, 155, T_DESERT),   # Australia (arid interior)
    (-48, -34, 165, 179, T_LAND),     # New Zealand
    # Antarctica
    (-90, -65, -180, 180, T_ICE),     # Antarctica
    # Arctic ice
    (80, 90, -180, 180, T_ICE),       # North pole ice
]

# Ice cap regions
_ICE_REGIONS = [
    (75, 90, -180, 180),
    (-90, -60, -180, 180),
]


def classify_terrain(lat: float, lon: float) -> int:
    """Classify a lat/lon point as ocean, land, ice, or desert.

    Uses the simplified continent map above.
    """
    for lat_min, lat_max, lon_min, lon_max, terrain in _CONTINENTS:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return terrain
    return T_OCEAN


class GlobeModel:
    """Sphere model with terrain classification and pin markers.

    Each surface point is stored as (x, y, z, terrain) for colored rendering.
    """

    def __init__(self, resolution: int = 40, radius: float = 1.0):
        self.resolution = resolution
        self.radius = radius
        self._pins: List[Pin] = []
        # Surface points: list of (x, y, z) tuples
        self._surface_xyz: List[Tuple[float, float, float]] = []
        # Terrain classification per surface point
        self._surface_terrain: List[int] = []
        # Lat/lon for each surface point (for terrain lookup)
        self._surface_latlon: List[Tuple[float, float]] = []
        self._generate_surface()

    def _generate_surface(self):
        """Generate sphere point cloud with terrain classification."""
        self._surface_xyz = []
        self._surface_terrain = []
        self._surface_latlon = []

        cache = TrigCache(self.resolution)
        n_lat = self.resolution
        n_lon = 2 * self.resolution

        for i in range(n_lat):
            cos_phi = cache.cos_phi[i]
            sin_phi = cache.sin_phi[i]
            # Convert index to latitude in degrees
            lat_deg = -90.0 + 180.0 * i / (n_lat - 1)

            for j in range(n_lon):
                cos_lam = cache.cos_lam[j]
                sin_lam = cache.sin_lam[j]
                # Convert index to longitude in degrees
                lon_deg = -180.0 + 360.0 * j / n_lon

                x = self.radius * cos_phi * cos_lam
                y = self.radius * sin_phi
                z = self.radius * cos_phi * sin_lam

                self._surface_xyz.append((x, y, z))
                self._surface_terrain.append(classify_terrain(lat_deg, lon_deg))
                self._surface_latlon.append((lat_deg, lon_deg))

    def set_resolution(self, resolution: int):
        self.resolution = resolution
        self._generate_surface()

    def add_pin(self, lat: float, lon: float, label: str = "") -> int:
        pid = _new_pin_id()
        pin = Pin(lat=lat, lon=lon, label=label, _id=pid)
        self._pins.append(pin)
        return pid

    def remove_pin(self, pid: int) -> bool:
        for i, pin in enumerate(self._pins):
            if pin._id == pid:
                self._pins.pop(i)
                return True
        return False

    def clear_pins(self):
        self._pins.clear()

    def get_surface_points(self) -> List[Vec3]:
        """Return cached surface points as Vec3 objects."""
        return [Vec3(x, y, z) for x, y, z in self._surface_xyz]

    def get_pin_points(self) -> List[Tuple[Vec3, Pin]]:
        return [(pin.xyz(self.radius), pin) for pin in self._pins]

    @property
    def point_count(self) -> int:
        return len(self._surface_xyz) + len(self._pins)

    @property
    def pin_count(self) -> int:
        return len(self._pins)


class GlobeWithGridlines(GlobeModel):
    """Extended globe with meridian and parallel lines."""

    def __init__(self, resolution: int = 40, radius: float = 1.0,
                 meridians: Optional[List[float]] = None,
                 parallels: Optional[List[float]] = None):
        self._meridians = meridians or [0, -30, 30, -60, 60, -90, 90, -120, 120, -150, 150]
        self._parallels = parallels or [0, 23.44, -23.44, 45, -45, 66.56, -66.56]
        self._grid_points: List[Tuple[float, float, float]] = []
        super().__init__(resolution, radius)
        self._generate_gridlines()

    def _generate_gridlines(self):
        """Generate points along meridians and parallels."""
        self._grid_points = []
        for lon in self._meridians:
            for lat_step in range(-90, 91, 5):
                v = latlon_to_xyz(lat_step, lon, self.radius)
                self._grid_points.append((v.x, v.y, v.z))
        for lat in self._parallels:
            for lon_step in range(-180, 181, 5):
                v = latlon_to_xyz(lat, lon_step, self.radius)
                self._grid_points.append((v.x, v.y, v.z))

    def get_grid_points(self) -> List[Tuple[float, float, float]]:
        return self._grid_points

    def set_resolution(self, resolution: int):
        super().set_resolution(resolution)
        self._generate_gridlines()
