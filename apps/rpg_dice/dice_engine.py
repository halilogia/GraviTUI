"""3D engine: rotation matrices / quaternions, polyhedral dice geometry, projection, shaded rasteriser, roll physics."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from collections.abc import Sequence
from typing import Dict, List, Optional, Tuple

from rpg_colors import RGB, ScreenBuffer, add, desaturate, lerp, luminance, scale

Vec = Tuple[float, float, float]
Quat = Tuple[float, float, float, float]
Mat = Tuple[Vec, Vec, Vec]

PHI = (1 + 5 ** 0.5) / 2
CAMERA = 4.2  # camera distance in die-radius units (perspective strength)

# ------------------------------------------------------------------ vectors / matrices


def v_sub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def v_dot(a: Vec, b: Vec) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def v_cross(a: Vec, b: Vec) -> Vec:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def v_len(a: Vec) -> float:
    return math.sqrt(v_dot(a, a))


def v_norm(a: Vec) -> Vec:
    n = v_len(a) or 1.0
    return (a[0] / n, a[1] / n, a[2] / n)


def rot_x(a: float) -> Mat:
    c, s = math.cos(a), math.sin(a)
    return ((1, 0, 0), (0, c, -s), (0, s, c))


def rot_y(a: float) -> Mat:
    c, s = math.cos(a), math.sin(a)
    return ((c, 0, s), (0, 1, 0), (-s, 0, c))


def rot_z(a: float) -> Mat:
    c, s = math.cos(a), math.sin(a)
    return ((c, -s, 0), (s, c, 0), (0, 0, 1))


def mat_mul(a: Mat, b: Mat) -> Mat:
    def cell(i: int, j: int) -> float:
        return sum(a[i][k] * b[k][j] for k in range(3))
    return ((cell(0, 0), cell(0, 1), cell(0, 2)),
            (cell(1, 0), cell(1, 1), cell(1, 2)),
            (cell(2, 0), cell(2, 1), cell(2, 2)))


def mat_vec(m: Mat, v: Vec) -> Vec:
    return (m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
            m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
            m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2])


# ------------------------------------------------------------------ quaternions


def q_mul(a: Quat, b: Quat) -> Quat:
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    return (w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2)


def q_normalize(q: Quat) -> Quat:
    n = math.sqrt(sum(c * c for c in q)) or 1.0
    return (q[0] / n, q[1] / n, q[2] / n, q[3] / n)


def q_axis(axis: Vec, angle: float) -> Quat:
    ax = v_norm(axis)
    s = math.sin(angle / 2)
    return (math.cos(angle / 2), ax[0] * s, ax[1] * s, ax[2] * s)


def q_slerp(a: Quat, b: Quat, t: float) -> Quat:
    d = sum(x * y for x, y in zip(a, b))
    if d < 0:
        b = (-b[0], -b[1], -b[2], -b[3])
        d = -d
    if d > 0.9995:
        return q_normalize((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
                            a[2] + (b[2] - a[2]) * t, a[3] + (b[3] - a[3]) * t))
    th = math.acos(min(1.0, d))
    s = math.sin(th)
    w1, w2 = math.sin((1 - t) * th) / s, math.sin(t * th) / s
    return (w1 * a[0] + w2 * b[0], w1 * a[1] + w2 * b[1], w1 * a[2] + w2 * b[2], w1 * a[3] + w2 * b[3])


def q_matrix(q: Quat) -> Mat:
    w, x, y, z = q
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)),
            (2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)),
            (2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)))


def q_from_to(u: Vec, v: Vec) -> Quat:
    """Shortest rotation taking unit vector u onto unit vector v."""
    d = v_dot(u, v)
    if d > 0.999999:
        return (1.0, 0.0, 0.0, 0.0)
    if d < -0.999999:
        axis = v_cross(u, (1, 0, 0))
        if v_len(axis) < 1e-6:
            axis = v_cross(u, (0, 1, 0))
        return q_axis(axis, math.pi)
    c = v_cross(u, v)
    return q_normalize((1 + d, c[0], c[1], c[2]))


def q_random(rng: random.Random) -> Quat:
    return q_normalize((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)))


# ------------------------------------------------------------------ geometry


def _hull_faces(verts: List[Vec]) -> List[Tuple[List[int], Vec]]:
    """Faces of a convex polyhedron centred on the origin: planes through vertex triples with all vertices behind."""
    n = len(verts)
    found: Dict[Tuple[int, ...], Vec] = {}
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                nrm = v_cross(v_sub(verts[j], verts[i]), v_sub(verts[k], verts[i]))
                ln = v_len(nrm)
                if ln < 1e-9:
                    continue
                nrm = (nrm[0] / ln, nrm[1] / ln, nrm[2] / ln)
                d = v_dot(nrm, verts[i])
                if d < 0:
                    nrm, d = (-nrm[0], -nrm[1], -nrm[2]), -d
                if d < 1e-9:
                    continue
                dots = [v_dot(nrm, v) for v in verts]
                if max(dots) > d + 1e-6:
                    continue
                members = tuple(m for m in range(n) if abs(dots[m] - d) < 1e-6)
                found[members] = nrm
    faces = []
    for members, nrm in found.items():
        pts = [verts[m] for m in members]
        c = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts), sum(p[2] for p in pts) / len(pts))
        u = v_norm(v_sub(pts[0], c))
        w = v_cross(nrm, u)
        order = sorted(range(len(members)),
                       key=lambda m: math.atan2(v_dot(v_sub(pts[m], c), w), v_dot(v_sub(pts[m], c), u)))
        faces.append(([members[m] for m in order], nrm))
    faces.sort(key=lambda f: (-round(f[1][1], 3), round(f[1][0], 3), round(f[1][2], 3)))
    return faces


def _raw_vertices(kind: int) -> List[Vec]:
    if kind == 4:
        return [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]
    if kind == 6:
        return [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    if kind == 8:
        return [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    if kind == 12:
        iv = 1 / PHI
        v = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
        for a in (-1, 1):
            for b in (-1, 1):
                v += [(0, a * iv, b * PHI), (a * iv, b * PHI, 0), (b * PHI, 0, a * iv)]
        return v
    if kind == 20:
        v = []
        for a in (-1, 1):
            for b in (-1, 1):
                v += [(0, a, b * PHI), (a, b * PHI, 0), (b * PHI, 0, a)]
        return v
    if kind == 10:  # pentagonal trapezohedron with planar kite faces
        c36 = math.cos(math.radians(36))
        a = (1 - c36) / (1 + c36)
        v = [(0.0, 0.0, 1.0), (0.0, 0.0, -1.0)]
        for k in range(5):
            u, l = math.radians(72 * k), math.radians(72 * k + 36)
            v.append((math.cos(u), math.sin(u), a))
            v.append((math.cos(l), math.sin(l), -a))
        return [(x, z, y) for x, y, z in v]  # poles along Y
    raise ValueError(kind)


DIE_BASE: Dict[int, RGB] = {
    20: (44, 190, 232), 12: (214, 56, 82), 10: (64, 204, 128), 8: (244, 150, 38),
    6: (152, 92, 236), 4: (236, 204, 72), 100: (232, 88, 172),
}


@dataclass
class Shape:
    sides: int
    verts: List[Vec]
    faces: List[List[int]]
    normals: List[Vec]
    labels: List[str]
    base: RGB


_SHAPES: Dict[int, Shape] = {}


def build_shape(sides: int) -> Shape:
    if sides in _SHAPES:
        return _SHAPES[sides]
    kind = 10 if sides == 100 else sides
    raw = _raw_vertices(kind)
    r = max(v_len(v) for v in raw)
    verts = [(v[0] / r, v[1] / r, v[2] / r) for v in raw]
    hull = _hull_faces(verts)
    faces = [f for f, _ in hull]
    normals = [n for _, n in hull]
    if sides == 100:
        labels = [f"{i * 10:02d}" for i in range(10)]
    else:
        labels = [str(i + 1) for i in range(len(faces))]
    shape = Shape(sides, verts, faces, normals, labels, DIE_BASE[sides])
    _SHAPES[sides] = shape
    return shape


# ------------------------------------------------------------------ pixel canvas (2 pixels per cell via ▀)


class PixelCanvas:
    def __init__(self, w: int, rows: int):
        self.w, self.h = w, rows * 2
        self.px: List[Optional[RGB]] = [None] * (self.w * self.h)
        self.min_y, self.max_y = self.h, -1
        self.min_x, self.max_x = self.w, -1

    def set(self, x: int, y: int, c: RGB) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y * self.w + x] = c
            if y < self.min_y:
                self.min_y = y
            if y > self.max_y:
                self.max_y = y
            if x < self.min_x:
                self.min_x = x
            if x > self.max_x:
                self.max_x = x

    def fill_poly(self, pts: Sequence[Tuple[float, float]], c: RGB) -> None:
        n = len(pts)
        ys = [p[1] for p in pts]
        y0 = max(0, math.ceil(min(ys) - 0.5))
        y1 = min(self.h - 1, math.floor(max(ys) - 0.5))
        w = self.w
        for y in range(y0, y1 + 1):
            yc = y + 0.5
            xs = []
            for i in range(n):
                ax, ay = pts[i]
                bx, by = pts[(i + 1) % n]
                if (ay <= yc < by) or (by <= yc < ay):
                    xs.append(ax + (yc - ay) * (bx - ax) / (by - ay))
            if len(xs) >= 2:
                xl = max(0, math.ceil(min(xs) - 0.5))
                xr = min(w - 1, math.floor(max(xs) - 0.5))
                if xr >= xl:
                    base = y * w
                    for x in range(xl, xr + 1):
                        self.px[base + x] = c
                    if y < self.min_y:
                        self.min_y = y
                    if y > self.max_y:
                        self.max_y = y
                    if xl < self.min_x:
                        self.min_x = xl
                    if xr > self.max_x:
                        self.max_x = xr

    def fill_ellipse(self, cx: float, cy: float, rx: float, ry: float, c: RGB) -> None:
        for y in range(int(cy - ry), int(cy + ry) + 1):
            dy = (y + 0.5 - cy) / ry if ry else 2
            if abs(dy) > 1:
                continue
            half = rx * math.sqrt(1 - dy * dy)
            for x in range(int(cx - half), int(cx + half) + 1):
                self.set(x, y, c)

    def blit(self, buf: ScreenBuffer, ox: int, oy: int) -> None:
        if self.max_y < 0:
            return
        w, px = self.w, self.px
        for cy in range(self.min_y // 2, self.max_y // 2 + 1):
            by = oy + cy
            if not 0 <= by < buf.h:
                continue
            for x in range(self.min_x, self.max_x + 1):
                top = px[2 * cy * w + x]
                bot = px[(2 * cy + 1) * w + x]
                if top is None and bot is None:
                    continue
                bx = ox + x
                if not 0 <= bx < buf.w:
                    continue
                i = by * buf.w + bx
                under = buf.bg[i]
                buf.ch[i] = "▀"
                buf.fg[i] = top if top is not None else under
                buf.bg[i] = bot if bot is not None else under


# ------------------------------------------------------------------ shaded polyhedron renderer

LIGHT = v_norm((-0.45, 0.6, 0.8))
HALF = v_norm((LIGHT[0], LIGHT[1], LIGHT[2] + 1.0))


@dataclass
class FaceLabel:
    x: int
    y: int  # canvas cell coordinates
    text: str
    fg: RGB
    bg: RGB


def render_die(canvas: PixelCanvas, shape: Shape, q: Quat, cx: float, cy: float, radius: float,
               tint: Optional[Tuple[RGB, float]] = None, dim: float = 0.0, jitter: float = 0.0,
               rng: Optional[random.Random] = None) -> List[FaceLabel]:
    """Draw a lit, bevelled, perspective-projected die. Returns labels of the faces turned towards the camera."""
    m = q_matrix(q)
    base = shape.base
    if tint is not None:
        base = lerp(base, tint[0], tint[1])
    if dim:
        base = scale(desaturate(base, dim), 1.0 - 0.45 * dim)
    rv = [mat_vec(m, v) for v in shape.verts]
    proj = []
    for x, y, z in rv:
        k = CAMERA / (CAMERA - z)
        proj.append((cx + x * radius * k, cy - y * radius * k))
    visible = []
    for fi, face in enumerate(shape.faces):
        n = mat_vec(m, shape.normals[fi])
        if n[2] <= 0.02:
            continue
        depth = sum(rv[i][2] for i in face) / len(face)
        visible.append((depth, fi, n))
    visible.sort()
    labels: List[FaceLabel] = []
    for _, fi, n in visible:
        face = shape.faces[fi]
        pts = [proj[i] for i in face]
        if jitter and rng is not None:
            pts = [(px + rng.uniform(-jitter, jitter), py + rng.uniform(-jitter, jitter)) for px, py in pts]
        lam = max(0.0, v_dot(n, LIGHT))
        spec = max(0.0, v_dot(n, HALF)) ** 28
        face_col = add(scale(base, 0.16 + 0.84 * lam), (255, 255, 255), spec * 0.5)
        edge_col = lerp(face_col, (255, 244, 214), 0.42)
        canvas.fill_poly(pts, edge_col)
        mx = sum(p[0] for p in pts) / len(pts)
        my = sum(p[1] for p in pts) / len(pts)
        inner = [(mx + (px - mx) * 0.80, my + (py - my) * 0.80) for px, py in pts]
        canvas.fill_poly(inner, face_col)
        area = 0.5 * abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                             for i in range(len(pts))))
        if area > 26 and n[2] > 0.25:
            txt = shape.labels[fi]
            fg_ = (255, 248, 226) if luminance(face_col) < 150 else (24, 14, 20)
            labels.append(FaceLabel(int(mx) - len(txt) // 2 + (1 if len(txt) % 2 == 0 else 0), int(my // 2), txt,
                                    fg_, face_col))
    return labels


# ------------------------------------------------------------------ roll physics


def _smooth(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


class DiceBody:
    """One die: idle hover, then a scripted throw (fall, decaying bounces, tumbling spin, final slerp onto the face)."""

    H0 = 1.7  # drop height in die diameters
    FALL = 0.42  # seconds for the first fall
    RESTITUTION = 0.52

    def __init__(self, shape: Shape, rng: random.Random):
        self.shape = shape
        self.rng = rng
        self.state = "idle"  # idle | rolling | settled
        self.idle_t = rng.random() * 10
        self.q: Quat = q_random(rng)
        self.x = 0.0  # horizontal offset, -1..1 of the die slot
        self.h = 0.1  # height above the table in diameters
        self.t = 0.0
        self.duration = 3.6
        self._impacts: List[Tuple[float, float]] = []
        self._segments: List[Tuple[float, float, float]] = []

    def throw(self, face_idx: int, duration: float = 3.6, side: float = 1.0, delay: float = 0.0) -> None:
        rng = self.rng
        n = self.shape.normals[face_idx]
        self.target = q_mul(q_axis((0, 0, 1), rng.uniform(0, math.tau)), q_from_to(n, (0.0, 0.0, 1.0)))
        self.q0 = q_random(rng)
        self.spin_axis = v_norm((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)))
        self.spin_total = rng.uniform(17, 26) * rng.choice((-1, 1))
        self.x0 = side * rng.uniform(0.6, 1.0)
        self.duration = duration
        self.t = -delay
        self.state = "rolling"
        g = 2 * self.H0 / self.FALL ** 2
        self._impacts = [(self.FALL, 1.0)]
        self._segments = []
        t, v, v0 = self.FALL, g * self.FALL, g * self.FALL
        for _ in range(4):
            v *= self.RESTITUTION
            dur = 2 * v / g
            self._segments.append((t, dur, v * v / (2 * g)))
            t += dur
            self._impacts.append((t, v / v0))
        self._next_impact = 0

    def _height(self, t: float) -> float:
        if t < 0:
            return self.H0
        if t < self.FALL:
            return self.H0 * (1 - (t / self.FALL) ** 2)
        for start, dur, peak in self._segments:
            if start <= t < start + dur:
                tau = (t - start) / dur
                return peak * 4 * tau * (1 - tau)
        return 0.0

    def update(self, dt: float) -> List[float]:
        """Advance the simulation; returns the strengths (0..1) of table impacts that happened this step."""
        hits: List[float] = []
        if self.state == "idle":
            self.idle_t += dt
            self.q = q_mul(q_axis((0, 1, 0), self.idle_t * 0.7), q_axis((1, 0, 0), 0.5 + 0.12 * math.sin(self.idle_t)))
            self.h = 0.12 + 0.05 * math.sin(self.idle_t * 1.7)
            self.x = 0.0
            return hits
        if self.state == "settled":
            return hits
        self.t += dt
        t = self.t
        u = max(0.0, min(1.0, t / self.duration))
        if u >= 1.0:
            self.state, self.q, self.h, self.x = "settled", self.target, 0.0, 0.0
            return hits
        while self._next_impact < len(self._impacts) and t >= self._impacts[self._next_impact][0]:
            hits.append(self._impacts[self._next_impact][1])
            self._next_impact += 1
        self.h = self._height(t)
        self.x = self.x0 * (1 - _smooth(t / (0.78 * self.duration)))
        theta = self.spin_total * (1 - (1 - u) ** 3) if t > 0 else 0.0
        qs = q_mul(q_axis(self.spin_axis, theta), self.q0)
        qs = q_mul(q_axis((0, 1, 0), theta * 0.5), qs)
        b = max(0.0, (u - 0.46) / 0.54)
        b = b * b * b * (b * (6 * b - 15) + 10)  # smootherstep: slow, tense approach to the final face
        self.q = q_slerp(qs, self.target, b)
        return hits

    @property
    def settled(self) -> bool:
        return self.state == "settled"
