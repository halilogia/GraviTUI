import math
import unittest

from gravitui import Buffer, Canvas3D, Color, Mesh3D, Matrix4, Quaternion, Rect, Vector3
from gravitui.extensions.canvas3d import face_normal


class TestMath(unittest.TestCase):
    def test_vector(self):
        a, b = Vector3(1, 0, 0), Vector3(0, 1, 0)
        self.assertEqual(a.cross(b), Vector3(0, 0, 1))
        self.assertAlmostEqual(Vector3(3, 4, 0).length(), 5)
        self.assertAlmostEqual(Vector3(0, 0, 9).normalized().z, 1)

    def test_matrix_transform(self):
        m = Matrix4.translation(1, 2, 3) @ Matrix4.scaling(2, 2, 2)
        self.assertEqual(m.transform_point(Vector3(1, 1, 1)), Vector3(3, 4, 5))
        self.assertEqual(m.transform_dir(Vector3(1, 0, 0)), Vector3(2, 0, 0))

    def test_rotation_z(self):
        v = Matrix4.rotation_z(math.pi / 2).transform_point(Vector3(1, 0, 0))
        self.assertAlmostEqual(v.x, 0)
        self.assertAlmostEqual(v.y, 1)

    def test_quaternion_matches_matrix(self):
        q = Quaternion.from_axis_angle(Vector3(0, 1, 0), 0.7)
        v = Vector3(1, 2, 3)
        a, b = q.rotate(v), Matrix4.from_quaternion(q).transform_point(v)
        self.assertAlmostEqual(a.x, b.x)
        self.assertAlmostEqual(a.z, b.z)
        c = Matrix4.rotation_y(0.7).transform_point(v)
        self.assertAlmostEqual(c.x, a.x)
        self.assertAlmostEqual(c.z, a.z)

    def test_quaternion_compose_slerp(self):
        qa = Quaternion.from_axis_angle(Vector3(0, 0, 1), 0.0)
        qb = Quaternion.from_axis_angle(Vector3(0, 0, 1), math.pi / 2)
        mid = qa.slerp(qb, 0.5).rotate(Vector3(1, 0, 0))
        self.assertAlmostEqual(mid.x, math.cos(math.pi / 4))
        both = (qb * qb).rotate(Vector3(1, 0, 0))
        self.assertAlmostEqual(both.x, -1)


class TestMesh(unittest.TestCase):
    def _outward(self, mesh):
        for f in mesh.faces:
            pts = [mesh.vertices[i] for i in f.indices]
            c = Vector3()
            for p in pts:
                c = c + p
            c = c * (1 / len(pts))
            self.assertGreater(face_normal(*pts[:3]).dot(c), 0)

    def test_cube(self):
        m = Mesh3D.cube()
        self.assertEqual((len(m.vertices), len(m.faces)), (8, 6))
        self._outward(m)

    def test_d20(self):
        m = Mesh3D.icosahedron()
        self.assertEqual((len(m.vertices), len(m.faces)), (12, 20))
        self._outward(m)
        for v in m.vertices:
            self.assertAlmostEqual(v.length(), 1.0)

    def test_octahedron(self):
        m = Mesh3D.octahedron()
        self.assertEqual(len(m.faces), 8)
        self._outward(m)


class TestCanvas(unittest.TestCase):
    def test_renders_something_centered(self):
        b = Buffer(20, 10)
        Canvas3D(Mesh3D.cube(), Quaternion.from_euler(0.4, 0.6, 0)).render(b.area, b)
        drawn = [(x, y) for y in range(10) for x in range(20) if b.get(x, y).char == "▀"]
        self.assertGreater(len(drawn), 20)
        xs = [x for x, _ in drawn]
        self.assertLess(min(xs), 10)
        self.assertGreater(max(xs), 9)

    def test_empty_corners(self):
        b = Buffer(20, 10)
        Canvas3D(Mesh3D.icosahedron()).render(b.area, b)
        self.assertEqual(b.get(0, 0).char, " ")

    def test_rotation_changes_frame(self):
        def frame(a):
            b = Buffer(24, 12)
            q = Quaternion.from_axis_angle(Vector3(1, 1, 0), a)
            Canvas3D(Mesh3D.cube(), q).render(b.area, b)
            return b.cells
        self.assertNotEqual(frame(0.3), frame(0.9))

    def test_flat_shading_varies_by_face(self):
        mesh = Mesh3D.cube(colors=[Color(200, 200, 200)])
        pix = Canvas3D(mesh, Quaternion.from_euler(0.5, 0.7, 0)).rasterize(40, 40)
        shades = {c for row in pix for c in row if c is not None}
        self.assertGreaterEqual(len(shades), 2)

    def test_zbuffer_hides_back(self):
        m = Mesh3D.cube()
        pix = Canvas3D(m, cull_backfaces=False).rasterize(30, 30)
        front = Canvas3D(m).rasterize(30, 30)
        self.assertEqual(pix[15][15], front[15][15])

    def test_zero_area(self):
        b = Buffer(1, 1)
        Canvas3D(Mesh3D.cube()).render(Rect(0, 0, 0, 0), b)
        self.assertEqual(b.to_lines(), [" "])


if __name__ == "__main__":
    unittest.main()
