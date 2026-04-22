"""
termglobe.math_core - Core mathematical primitives for 3D rendering.

Provides vector operations, rotation matrices, perspective projection,
and geographic coordinate conversion. All functions are pure and stateless.
"""

import math
from dataclasses import dataclass
from typing import Tuple


@dataclass
class Vec3:
    """Minimal 3D vector with arithmetic operations."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, other: 'Vec3') -> 'Vec3':
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'Vec3') -> 'Vec3':
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> 'Vec3':
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> 'Vec3':
        return self.__mul__(scalar)

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def normalized(self) -> 'Vec3':
        ln = self.length()
        if ln < 1e-10:
            return Vec3()
        return Vec3(self.x / ln, self.y / ln, self.z / ln)

    def dot(self, other: 'Vec3') -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z


@dataclass
class Vec2:
    """2D vector for screen coordinates."""
    x: float = 0.0
    y: float = 0.0


# ---------------------------------------------------------------------------
# Rotation functions
# ---------------------------------------------------------------------------

def rot_y(p: Vec3, theta: float) -> Vec3:
    """Rotate point around Y axis by angle theta (radians).

    Matrix:
        | cos(t)   0  sin(t) |
        |   0      1    0    |
        | -sin(t)  0  cos(t) |
    """
    c = math.cos(theta)
    s = math.sin(theta)
    return Vec3(
        p.x * c + p.z * s,
        p.y,
        -p.x * s + p.z * c,
    )


def rot_x(p: Vec3, theta: float) -> Vec3:
    """Rotate point around X axis by angle theta (radians).

    Matrix:
        | 1    0       0    |
        | 0  cos(t) -sin(t) |
        | 0  sin(t)  cos(t) |
    """
    c = math.cos(theta)
    s = math.sin(theta)
    return Vec3(
        p.x,
        p.y * c - p.z * s,
        p.y * s + p.z * c,
    )


def rot_z(p: Vec3, theta: float) -> Vec3:
    """Rotate point around Z axis by angle theta (radians).

    Matrix:
        | cos(t) -sin(t)  0 |
        | sin(t)  cos(t)   0 |
        |   0       0      1 |
    """
    c = math.cos(theta)
    s = math.sin(theta)
    return Vec3(
        p.x * c - p.y * s,
        p.x * s + p.y * c,
        p.z,
    )


# ---------------------------------------------------------------------------
# Projection
# ---------------------------------------------------------------------------

def project(p: Vec3, d: float) -> Tuple[Vec2, float]:
    """Perspective projection from 3D to 2D.

    Args:
        p: 3D point (already rotated).
        d: Camera distance from origin.

    Returns:
        (Vec2 screen_coords, z_depth) or raises if behind camera.
        z_depth is the original z for depth testing.

    Raises:
        ValueError: If point is behind the camera (z + d <= 0).
    """
    denom = p.z + d
    if denom <= 1e-6:
        raise ValueError("Point behind camera")
    return Vec2(p.x / denom, p.y / denom), p.z


# ---------------------------------------------------------------------------
# Geographic conversion
# ---------------------------------------------------------------------------

def latlon_to_xyz(lat: float, lon: float, r: float = 1.0) -> Vec3:
    """Convert latitude/longitude (degrees) to 3D cartesian.

    Args:
        lat: Latitude in degrees (-90 to 90).
        lon: Longitude in degrees (-180 to 180).
        r: Sphere radius.

    Returns:
        Vec3 with x pointing to (0,0), y to north pole, z to (0,90E).
    """
    phi = math.radians(lat)
    lam = math.radians(lon)
    cos_phi = math.cos(phi)
    return Vec3(
        r * cos_phi * math.cos(lam),
        r * math.sin(phi),
        r * cos_phi * math.sin(lam),
    )


# ---------------------------------------------------------------------------
# Trig cache
# ---------------------------------------------------------------------------

class TrigCache:
    """Precomputed sin/cos tables for sphere generation.

    Avoids repeated trig calls during point generation.
    """

    def __init__(self, resolution: int):
        self.res = resolution
        # Latitude steps: -pi/2 to pi/2
        n_lat = resolution
        self.cos_phi = [math.cos(-math.pi / 2 + math.pi * i / (n_lat - 1))
                        for i in range(n_lat)]
        self.sin_phi = [math.sin(-math.pi / 2 + math.pi * i / (n_lat - 1))
                        for i in range(n_lat)]
        # Longitude steps: 0 to 2*pi
        n_lon = 2 * resolution
        self.cos_lam = [math.cos(2 * math.pi * j / n_lon) for j in range(n_lon)]
        self.sin_lam = [math.sin(2 * math.pi * j / n_lon) for j in range(n_lon)]
