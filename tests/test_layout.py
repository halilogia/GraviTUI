import unittest

from gravitui import (Layout, Rect, Percentage, Length, Ratio, Min, Max, Fill,
                      HORIZONTAL, VERTICAL)


class TestRect(unittest.TestCase):
    def test_basic(self):
        r = Rect(2, 3, 10, 5)
        self.assertEqual((r.right, r.bottom, r.area), (12, 8, 50))
        self.assertTrue(r.contains(2, 3))
        self.assertFalse(r.contains(12, 3))

    def test_pad_intersect(self):
        r = Rect(0, 0, 10, 10)
        self.assertEqual(r.pad(1, 2, 3, 4), Rect(1, 2, 6, 4))
        self.assertEqual(r.pad(20, 0, 0, 0).width, 0)
        self.assertEqual(r.intersect(Rect(5, 5, 10, 10)), Rect(5, 5, 5, 5))
        self.assertTrue(r.intersect(Rect(20, 20, 2, 2)).is_empty())

    def test_split_centered(self):
        a, b = Rect(0, 0, 10, 4).split_h(3)
        self.assertEqual((a.width, b.x, b.width), (3, 3, 7))
        self.assertEqual(Rect(0, 0, 10, 10).centered(4, 2), Rect(3, 4, 4, 2))


class TestLayout(unittest.TestCase):
    def test_percentage_length(self):
        r = Layout.split(Rect(0, 0, 100, 10), HORIZONTAL, [Percentage(30), Length(20), Fill()])
        self.assertEqual([x.width for x in r], [30, 20, 50])
        self.assertEqual([x.x for x in r], [0, 30, 50])

    def test_vertical(self):
        r = Layout.split(Rect(0, 0, 10, 20), VERTICAL, [Length(3), Min(0), Length(1)])
        self.assertEqual([x.height for x in r], [3, 16, 1])
        self.assertEqual(r[2].y, 19)

    def test_ratio(self):
        r = Layout.split(Rect(0, 0, 90, 1), HORIZONTAL, [Ratio(1, 3), Ratio(2, 3)])
        self.assertEqual([x.width for x in r], [30, 60])

    def test_min_takes_rest(self):
        r = Layout.split(Rect(0, 0, 50, 1), HORIZONTAL, [Length(10), Min(5)])
        self.assertEqual([x.width for x in r], [10, 40])

    def test_max_caps(self):
        r = Layout.split(Rect(0, 0, 50, 1), HORIZONTAL, [Max(10), Fill()])
        self.assertEqual([x.width for x in r], [10, 40])

    def test_fill_weights(self):
        r = Layout.split(Rect(0, 0, 40, 1), HORIZONTAL, [Fill(1), Fill(3)])
        self.assertEqual([x.width for x in r], [10, 30])

    def test_overflow_truncates(self):
        r = Layout.split(Rect(0, 0, 10, 1), HORIZONTAL, [Length(8), Length(8)])
        self.assertEqual(sum(x.width for x in r), 10)

    def test_spacing_margin(self):
        r = Layout.split(Rect(0, 0, 22, 12), HORIZONTAL, [Fill(), Fill()], margin=1, spacing=2)
        self.assertEqual((r[0].x, r[0].width, r[1].x, r[1].width), (1, 9, 12, 9))
        self.assertEqual(r[0].height, 10)

    def test_never_exceeds_area(self):
        for total in range(0, 30):
            cs = [Percentage(33), Min(4), Max(6), Length(5), Fill(2)]
            r = Layout.split(Rect(0, 0, total, 1), HORIZONTAL, cs)
            self.assertLessEqual(sum(x.width for x in r), total)

    def test_empty(self):
        self.assertEqual(Layout.split(Rect(0, 0, 5, 5), VERTICAL, []), [])


if __name__ == "__main__":
    unittest.main()
