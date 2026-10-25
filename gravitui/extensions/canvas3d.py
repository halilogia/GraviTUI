"""3D poligon projeksiyon widget'i: yazilim rasterizer, z-buffer, flat shading.

Her terminal hucresi yari-blok (▀) ile iki dikey piksel tasir.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from ..core.buffer import Buffer
from ..core.style import Color, Style
from ..layout.rect import Rect
from ..widgets.base import Widget


@dataclass(frozen=True)
class Vector3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, o): return Vector3(self.x + o.x, self.y + o.y, self.z + o.z)
    def __sub__(self, o): return Vector3(self.x - o.x, self.y - o.y, self.z - o.z)
    def __mul__(self, k: float): return Vector3(self.x * k, self.y * k, self.z * k)
    def __neg__(self): return Vector3(-self.x, -self.y, -self.z)

    def dot(self, o: "Vector3") -> float:
        return self.x * o.x + self.y * o.y + self.z * o.z

    def cross(self, o: "Vector3") -> "Vector3":
        return Vector3(self.y * o.z - self.z * o.y, self.z * o.x - self.x * o.z,
                       self.x * o.y - self.y * o.x)

    def length(self) -> float:
        return math.sqrt(self.dot(self))

    def normalized(self) -> "Vector3":
        n = self.length()
        return self * (1.0 / n) if n > 1e-12 else Vector3()


@dataclass(frozen=True)
class Quaternion:
    w: float = 1.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    @staticmethod
    def from_axis_angle(axis: Vector3, angle: float) -> "Quaternion":
        a = axis.normalized()
        s = math.sin(angle / 2)
        return Quaternion(math.cos(angle / 2), a.x * s, a.y * s, a.z * s)

    @staticmethod
    def from_euler(rx: float, ry: float, rz: float) -> "Quaternion":
        qx = Quaternion.from_axis_angle(Vector3(1, 0, 0), rx)
        qy = Quaternion.from_axis_angle(Vector3(0, 1, 0), ry)
        qz = Quaternion.from_axis_angle(Vector3(0, 0, 1), rz)
        return qz * qy * qx

    def __mul__(self, o: "Quaternion") -> "Quaternion":
        return Quaternion(
            self.w * o.w - self.x * o.x - self.y * o.y - self.z * o.z,
            self.w * o.x + self.x * o.w + self.y * o.z - self.z * o.y,
            self.w * o.y - self.x * o.z + self.y * o.w + self.z * o.x,
            self.w * o.z + self.x * o.y - self.y * o.x + self.z * o.w)

    def conjugate(self) -> "Quaternion":
        return Quaternion(self.w, -self.x, -self.y, -self.z)

    def normalized(self) -> "Quaternion":
        n = math.sqrt(self.w ** 2 + self.x ** 2 + self.y ** 2 + self.z ** 2)
        return Quaternion(self.w / n, self.x / n, self.y / n, self.z / n) if n > 1e-12 else Quaternion()

    def rotate(self, v: Vector3) -> Vector3:
        q = self.normalized()
        p = Quaternion(0, v.x, v.y, v.z)
        r = q * p * q.conjugate()
        return Vector3(r.x, r.y, r.z)

    def slerp(self, o: "Quaternion", t: float) -> "Quaternion":
        a, b = self.normalized(), o.normalized()
        d = a.w * b.w + a.x * b.x + a.y * b.y + a.z * b.z
        if d < 0:
            b, d = Quaternion(-b.w, -b.x, -b.y, -b.z), -d
        if d > 0.9995:
            return Quaternion(a.w + (b.w - a.w) * t, a.x + (b.x - a.x) * t,
                              a.y + (b.y - a.y) * t, a.z + (b.z - a.z) * t).normalized()
        th = math.acos(d)
        s0, s1 = math.sin((1 - t) * th) / math.sin(th), math.sin(t * th) / math.sin(th)
        return Quaternion(a.w * s0 + b.w * s1, a.x * s0 + b.x * s1,
                          a.y * s0 + b.y * s1, a.z * s0 + b.z * s1)


class Matrix4:
    """Satir-majorlu 4x4; sutun vektor (M @ v) konvansiyonu."""

    def __init__(self, m: Optional[Sequence[Sequence[float]]] = None):
        self.m = [list(r) for r in m] if m else [[1.0 if i == j else 0.0 for j in range(4)]
                                                for i in range(4)]

    @staticmethod
    def identity() -> "Matrix4":
        return Matrix4()

    @staticmethod
    def translation(x: float, y: float, z: float) -> "Matrix4":
        r = Matrix4()
        r.m[0][3], r.m[1][3], r.m[2][3] = x, y, z
        return r

    @staticmethod
    def scaling(x: float, y: float, z: float) -> "Matrix4":
        r = Matrix4()
        r.m[0][0], r.m[1][1], r.m[2][2] = x, y, z
        return r

    @staticmethod
    def rotation_x(a: float) -> "Matrix4":
        c, s = math.cos(a), math.sin(a)
        return Matrix4([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]])

    @staticmethod
    def rotation_y(a: float) -> "Matrix4":
        c, s = math.cos(a), math.sin(a)
        return Matrix4([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]])

    @staticmethod
    def rotation_z(a: float) -> "Matrix4":
        c, s = math.cos(a), math.sin(a)
        return Matrix4([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])

    @staticmethod
    def from_quaternion(q: Quaternion) -> "Matrix4":
        q = q.normalized()
        w, x, y, z = q.w, q.x, q.y, q.z
        return Matrix4([
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), 0],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), 0],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), 0],
            [0, 0, 0, 1]])

    def __matmul__(self, o: "Matrix4") -> "Matrix4":
        return Matrix4([[sum(self.m[i][k] * o.m[k][j] for k in range(4)) for j in range(4)]
                        for i in range(4)])

    def transform_point(self, v: Vector3) -> Vector3:
        m = self.m
        return Vector3(m[0][0] * v.x + m[0][1] * v.y + m[0][2] * v.z + m[0][3],
                       m[1][0] * v.x + m[1][1] * v.y + m[1][2] * v.z + m[1][3],
                       m[2][0] * v.x + m[2][1] * v.y + m[2][2] * v.z + m[2][3])

    def transform_dir(self, v: Vector3) -> Vector3:
        m = self.m
        return Vector3(m[0][0] * v.x + m[0][1] * v.y + m[0][2] * v.z,
                       m[1][0] * v.x + m[1][1] * v.y + m[1][2] * v.z,
                       m[2][0] * v.x + m[2][1] * v.y + m[2][2] * v.z)


@dataclass
class Face:
    indices: Tuple[int, ...]
    color: Color


class Mesh3D:
    def __init__(self, vertices: List[Vector3], faces: List[Face]):
        self.vertices = vertices
        self.faces = faces

    @staticmethod
    def cube(size: float = 1.5, colors: Optional[Sequence[Color]] = None) -> "Mesh3D":
        h = size / 2
        v = [Vector3(x * h, y * h, z * h) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
        # index = x*4 + y*2 + z (0/1); dis yone bakan (CCW) yuzler
        idx = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        pal = colors or [Color(230, 80, 80), Color(80, 200, 120), Color(80, 130, 240),
                         Color(240, 200, 70), Color(200, 100, 230), Color(80, 220, 230)]
        return Mesh3D(v, [Face(i, pal[k % len(pal)]) for k, i in enumerate(idx)])

    @staticmethod
    def icosahedron(radius: float = 1.0, colors: Optional[Sequence[Color]] = None) -> "Mesh3D":
        """d20 zari: 12 koseli, 20 ucgen yuzlu."""
        t = (1 + 5 ** 0.5) / 2
        raw = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t),
               (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
        v = [Vector3(*p).normalized() * radius for p in raw]
        tris = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
                (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
                (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
                (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
        pal = colors or [Color(110, 160, 255), Color(255, 120, 190), Color(120, 240, 180),
                         Color(255, 210, 100)]
        return Mesh3D(v, [Face(t_, pal[k % len(pal)]) for k, t_ in enumerate(tris)])

    @staticmethod
    def octahedron(radius: float = 1.0, color: Color = Color(120, 200, 255)) -> "Mesh3D":
        r = radius
        v = [Vector3(r, 0, 0), Vector3(-r, 0, 0), Vector3(0, r, 0),
             Vector3(0, -r, 0), Vector3(0, 0, r), Vector3(0, 0, -r)]
        tris = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4),
                (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]
        return Mesh3D(v, [Face(t_, color) for t_ in tris])


def face_normal(a: Vector3, b: Vector3, c: Vector3) -> Vector3:
    return (b - a).cross(c - a).normalized()


class Canvas3D(Widget):
    """Mesh'i modeli dondurup alana cizen widget."""

    def __init__(self, mesh: Mesh3D, rotation: Quaternion = Quaternion(),
                 camera_distance: float = 4.0, fov: float = 1.0,
                 light: Vector3 = Vector3(-0.4, 0.7, -1.0), ambient: float = 0.22,
                 background: Color = Color(8, 8, 14), cull_backfaces: bool = True):
        self.mesh = mesh
        self.rotation = rotation
        self.camera_distance = camera_distance
        self.fov = fov
        self.light = light.normalized()
        self.ambient = ambient
        self.background = background
        self.cull_backfaces = cull_backfaces

    def rasterize(self, pw: int, ph: int) -> List[List[Optional[Color]]]:
        """pw x ph piksel renk ızgarası uretir (None = bos)."""
        pix: List[List[Optional[Color]]] = [[None] * pw for _ in range(ph)]
        zbuf = [[float("inf")] * pw for _ in range(ph)]
        rot = Matrix4.from_quaternion(self.rotation)
        world = [rot.transform_point(v) + Vector3(0, 0, self.camera_distance)
                 for v in self.mesh.vertices]
        scale = min(pw, ph) * 0.5 * self.camera_distance / 1.6 * math.tan(0.5) / math.tan(self.fov / 2)
        cx, cy = pw / 2, ph / 2

        def project(p: Vector3):
            z = max(p.z, 1e-3)
            return (cx + p.x * scale / z, cy - p.y * scale / z, p.z)

        for face in self.mesh.faces:
            pts = [world[i] for i in face.indices]
            n = face_normal(pts[0], pts[1], pts[2])
            # kameradan yuze bakis: yuz kameraya donukse n . (kamera - p) > 0; kamera = origin
            facing = n.dot(Vector3() - pts[0])
            if self.cull_backfaces and facing <= 0:
                continue
            shade = self.ambient + (1 - self.ambient) * max(0.0, n.dot(self.light))
            color = face.color.scale(shade)
            proj = [project(p) for p in pts]
            for k in range(1, len(proj) - 1):
                _fill_triangle(pix, zbuf, proj[0], proj[k], proj[k + 1], color, pw, ph)
        return pix

    def render(self, area: Rect, buf: Buffer) -> None:
        if area.is_empty():
            return
        pix = self.rasterize(area.width, area.height * 2)
        bg = self.background
        for cy in range(area.height):
            top, bot = pix[cy * 2], pix[cy * 2 + 1]
            for cx in range(area.width):
                t, b = top[cx], bot[cx]
                if t is None and b is None:
                    continue
                buf.set_char(area.x + cx, area.y + cy, "▀", Style(fg=t or bg, bg=b or bg))


def _fill_triangle(pix, zbuf, p0, p1, p2, color, pw, ph) -> None:
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if abs(den) < 1e-9:
        return
    minx = max(0, int(math.floor(min(x0, x1, x2))))
    maxx = min(pw - 1, int(math.ceil(max(x0, x1, x2))))
    miny = max(0, int(math.floor(min(y0, y1, y2))))
    maxy = min(ph - 1, int(math.ceil(max(y0, y1, y2))))
    for y in range(miny, maxy + 1):
        py = y + 0.5
        for x in range(minx, maxx + 1):
            px = x + 0.5
            a = ((y1 - y2) * (px - x2) + (x2 - x1) * (py - y2)) / den
            b = ((y2 - y0) * (px - x2) + (x0 - x2) * (py - y2)) / den
            c = 1 - a - b
            if a < -1e-9 or b < -1e-9 or c < -1e-9:
                continue
            z = a * z0 + b * z1 + c * z2
            if z < zbuf[y][x]:
                zbuf[y][x] = z
                pix[y][x] = color
