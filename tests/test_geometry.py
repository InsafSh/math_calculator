"""Эталонные ответы для решателей аналитической геометрии (сверены вручную и с ответами задачников)."""

import pytest
import sympy as sp

from mathcalc.core.geometry import (
    PlaneSolver, LineSolver, RelationsSolver, DistancesAndProjections, PlanePencilSolver,
    SegmentSolver, TriangleSolver, PlaneLineSolver, ConicSolver, SpaceTaskSolver,
)


# ----------------------------------------------------------------------------- пространство
def test_plane_three_points():
    res = PlaneSolver.by_three_points((2, 0, 0), (0, -4, 0), (0, 0, 2))
    assert res['equation_str'] == "2x - y + 2z - 4 = 0"


def test_plane_three_collinear_points_raise():
    with pytest.raises(ValueError):
        PlaneSolver.by_three_points((0, 0, 0), (1, 1, 1), (2, 2, 2))


def test_plane_point_normal():
    res = PlaneSolver.by_point_and_normal(1, -2, 3, 2, -1, 4)
    assert (res['A'], res['B'], res['C'], res['D']) == (2, -1, 4, -16)


def test_line_from_general():
    res = LineSolver.from_general_to_canonical((2, -1, 1, -2), (2, -1, -1, 0))
    m, p, q = res['s']
    assert sp.Matrix([m, p, q]).cross(sp.Matrix([1, 2, 0])) == sp.zeros(3, 1)
    x0, y0, z0 = res['M0']
    assert 2 * x0 - y0 + z0 - 2 == 0 and 2 * x0 - y0 - z0 == 0


def test_point_to_plane():
    res = DistancesAndProjections.point_to_plane((5, -2, 5), (2, -1, 2, -4))
    assert res['distance'] == 6
    assert tuple(res['projection']) == (1, 0, 1)
    assert tuple(res['symmetric']) == (-3, 2, -3)


def test_point_to_line():
    res = DistancesAndProjections.point_to_line((1, 0, 0), (0, 0, 0), (0, 0, 1))
    assert res['distance'] == 1
    assert tuple(res['projection']) == (0, 0, 0)


def test_two_planes_parallel_distance():
    res = RelationsSolver.two_planes((2, -1, 2, -4), (4, -2, 4, 10))
    assert res['is_parallel'] and res['distance'] == 3


def test_two_lines_skew_distance():
    # ось Oz и прямая y = 1, z = 0 вдоль Ox: скрещиваются на расстоянии 1
    res = RelationsSolver.two_lines((0, 0, 0), (0, 0, 1), (0, 1, 0), (1, 0, 0))
    assert res.get('is_skew') and res['distance'] == 1


def test_line_plane_angle():
    res = RelationsSolver.line_and_plane((2, 0, 0), (3, -2, 5), (2, -1, 2, -4))
    assert sp.simplify(res['sin_theta'] - 3 * sp.sqrt(38) / 19) == 0


def test_pencil_through_point():
    res = PlanePencilSolver.pencil_through_point((1, 2, -1, 3), (2, -1, 1, -4), (1, 1, 1))
    assert res['A'] * 1 + res['B'] * 1 + res['C'] * 1 + res['D'] == 0


# ----------------------------------------------------------------------------- плоскость
def test_segment_division():
    res = SegmentSolver.solve((-3, 2), (7, -3), (2, 4), 3, 2)
    assert res['C'] == (3, -1) and res['D'] == (17, -8) and res['G'] == (2, 1)


def test_triangle():
    res = TriangleSolver.solve((1, 2), (4, 6), (6, -10), "A", "B", "A")
    assert res['median_eq'] == "x + y - 3 = 0"
    assert res['altitude_eq'] == "5x - 12y + 52 = 0"
    assert res['bisector_eq'] == "x + 8y - 17 = 0"
    assert res['cos_angle'] == sp.Rational(-33, 65)
    assert res['area'] == 28


def test_triangle_degenerate_raises():
    with pytest.raises(ValueError):
        TriangleSolver.solve((0, 0), (1, 1), (2, 2))


def test_line_and_point_2d():
    res = PlaneLineSolver.solve(3, -4, 12, (6, -5))
    assert res['parallel'] == "3x - 4y - 38 = 0"
    assert res['perpendicular'] == "4x + 3y - 9 = 0"
    assert res['H'] == (0, 3) and res['distance'] == 10 and res['symmetric'] == (-6, 11)


# ----------------------------------------------------------------------------- кривые
@pytest.mark.parametrize("coef, kind, canonical", [
    ((4, 0, 9, -16, 54, 61), "Эллипс", "X²/9 + Y²/4 = 1"),
    ((0, 0, 1, -8, -4, 20), "Парабола", "Y² = 8·X"),
    ((9, 0, -16, -18, -64, -199), "Гипербола", "X²/16 − Y²/9 = 1"),
    ((5, 2, 5, -12, -12, 0), "Эллипс", "X²/2 + Y²/3 = 1"),
    ((1, 0, 1, -2, -4, -4), "Окружность", "X²/9 + Y²/9 = 1"),
])
def test_conic_canonical(coef, kind, canonical):
    res = ConicSolver.solve(*coef)
    assert res['type'].startswith(kind)
    assert res['canonical'] == canonical


def test_conic_parabola_focus_and_directrix():
    res = ConicSolver.solve(0, 0, 1, -8, -4, 20)  # (y − 2)² = 8(x − 2)
    assert res['info']['vertex'] == (2, 2)
    assert res['info']['focus'] == (4, 2)
    assert res['info']['p'] == 4


def test_conic_rotation_angle():
    res = ConicSolver.solve(5, 2, 5, -12, -12, 0)
    assert abs(res['theta_deg'] - 45) < 1e-9


@pytest.mark.parametrize("coef, kind", [
    ((1, 0, -1, 0, 0, 0), "пара пересекающихся"),
    ((1, 0, 1, 0, 0, 0), "единственная точка"),
    ((1, 0, 1, 0, 0, 1), "Мнимый эллипс"),
    ((1, 0, 0, 0, 0, -1), "пара параллельных"),
])
def test_conic_degenerate(coef, kind):
    assert kind in ConicSolver.solve(*coef)['type']


# ----------------------------------------------------------------------------- комплексная
def test_space_task():
    res = SpaceTaskSolver.solve((2, 0, 0), (0, -4, 0), (0, 0, 2), (5, -2, 5), (2, -1, 1, -2), (2, -1, -1, 0))
    assert res['plane'] == (2, -1, 2, -4)
    assert tuple(res['H']) == (1, 0, 1) and res['distance'] == 6
    assert res['parallel_plane'] == (2, -1, 2, -22)
    assert res['intercept_eq'] == "x/(2) + y/(-4) + z/(2) = 1"
