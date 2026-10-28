"""
Раздел «Аналитическая геометрия»: регистрация задач, примеры и построение сцен для визуализации.
"""

from typing import Any, Sequence

from ..core.common import parse_number
from ..core.result import Result, Scene3D
from ..core.geometry import (
    PlaneSolver, LineSolver, RelationsSolver, DistancesAndProjections, PlanePencilSolver,
    SegmentSolver, TriangleSolver, PlaneLineSolver, ConicSolver, SpaceTaskSolver,
)
from .registry import Task, Preset, register, point2, point3, vec, plane, choice

SECTION = "Аналитическая геометрия"

BLUE, RED, GREEN, AMBER, GRAY, PINK = "#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#64748B", "#EC4899"


def f3(p: Sequence[Any]):
    """Координаты из полей ввода → кортеж float."""
    return tuple(float(parse_number(c)) for c in p)


def _add(task_id, group, title, fields, solve, description="", presets=None):
    register(Task(
        id=f"geometry.{task_id}", section=SECTION, group=group, title=title, fields=fields, solve=solve,
        description=description,
        presets=[Preset(n, v) for n, v in (presets or [])],
    ))


# =============================================================================
# Плоскость
# =============================================================================
G_PLANE = "Плоскость"


def _plane_point_normal(v):
    res = PlaneSolver.by_point_and_normal(*v['M0'], *v['n'])
    sc = Scene3D().add_plane(res['A'], res['B'], res['C'], res['D'], "Плоскость P")
    sc.add_point(res['point'], "M₀").add_vector(res['point'], res['normal'], "n⃗", color=RED)
    return Result(res['steps'], f"Плоскость: {res['equation_str']}", res, scene3d=sc)


def _plane_three_points(v):
    res = PlaneSolver.by_three_points(v['M1'], v['M2'], v['M3'])
    sc = Scene3D().add_plane(res['A'], res['B'], res['C'], res['D'], "Плоскость P")
    for i, p in enumerate(res['points'], 1):
        sc.add_point(p, f"M{i}")
    return Result(res['steps'], f"Плоскость: {res['equation_str']}", res, scene3d=sc)


def _plane_intercepts(v):
    res = PlaneSolver.in_intercepts(v['a'], v['b'], v['c'])
    a, b, c = f3(res['intercepts'])
    sc = Scene3D().add_plane(res['A'], res['B'], res['C'], res['D'], "Плоскость P")
    sc.add_point((a, 0, 0), "A").add_point((0, b, 0), "B").add_point((0, 0, c), "C")
    return Result(res['steps'], f"Плоскость: {res['equation_str']}", res, scene3d=sc)


def _plane_two_vectors(v):
    res = PlaneSolver.by_point_and_two_vectors(v['M0'], v['u'], v['v'])
    sc = Scene3D().add_plane(res['A'], res['B'], res['C'], res['D'], "Плоскость P").add_point(res['point'], "M₀")
    sc.add_vector(res['point'], f3(v['u']), "u⃗", color=GREEN).add_vector(res['point'], f3(v['v']), "v⃗", color=AMBER)
    return Result(res['steps'], f"Плоскость: {res['equation_str']}", res, scene3d=sc)


def _plane_parallel(v):
    res = PlaneSolver.by_point_parallel_to_plane(v['M0'], *v['P1'])
    sc = Scene3D().add_plane(*f3(v['P1']), "P₁ (исходная)", color=GRAY)
    sc.add_plane(res['A'], res['B'], res['C'], res['D'], "P₂ (параллельная)", color=BLUE).add_point(res['point'], "M₀")
    return Result(res['steps'], f"Плоскость: {res['equation_str']}", res, scene3d=sc)


def _plane_perp_two(v):
    res = PlaneSolver.by_point_perp_two_planes(v['M0'], v['P1'], v['P2'])
    sc = Scene3D().add_plane(*f3(v['P1']), "P₁", color=GRAY).add_plane(*f3(v['P2']), "P₂", color=AMBER)
    sc.add_plane(res['A'], res['B'], res['C'], res['D'], "P (искомая)", color=RED).add_point(res['point'], "M₀")
    return Result(res['steps'], f"Плоскость: {res['equation_str']}", res, scene3d=sc)


def _plane_line_point(v):
    res = PlaneSolver.by_line_and_point(v['ML'], v['s'], v['M1'])
    sc = Scene3D().add_plane(res['A'], res['B'], res['C'], res['D'], "Плоскость P")
    sc.add_line(f3(v['ML']), f3(v['s']), "Прямая L", color=GREEN).add_point(f3(v['M1']), "M₁")
    return Result(res['steps'], f"Плоскость: {res['equation_str']}", res, scene3d=sc)


def _plane_normal_form(v):
    res = PlaneSolver.normal_form(*v['P'])
    sc = Scene3D().add_plane(*f3(v['P']), "Плоскость")
    return Result(res['steps'], "Нормальное уравнение плоскости найдено", res, scene3d=sc)


_add("plane.point_normal", G_PLANE, "По точке и вектору нормали",
     [point3('M0', "Точка M₀", (1, -2, 3)), vec('n', "Вектор нормали n⃗", (2, -1, 4), ("A", "B", "C"))],
     _plane_point_normal, "A(x − x₀) + B(y − y₀) + C(z − z₀) = 0",
     [("Пример 1", {'M0': ("1", "-2", "3"), 'n': ("2", "-1", "4")}),
      ("Пример 2", {'M0': ("2", "-1", "5"), 'n': ("3", "4", "-1")})])
_add("plane.three_points", G_PLANE, "Через три точки",
     [point3('M1', "Точка M₁", (1, 2, 0)), point3('M2', "Точка M₂", (2, 1, 1)), point3('M3', "Точка M₃", (0, 3, 2))],
     _plane_three_points, "Определитель третьего порядка; проверка коллинеарности точек.",
     [("Пример 1", {'M1': ("1", "2", "0"), 'M2': ("2", "1", "1"), 'M3': ("0", "3", "2")}),
      ("Пример 2", {'M1': ("1", "2", "-1"), 'M2': ("0", "1", "2"), 'M3': ("-2", "3", "0")})])
_add("plane.intercepts", G_PLANE, "В отрезках на осях",
     [vec('abc', "Отрезки на осях", (2, -3, 4), ("a", "b", "c"))],
     lambda v: _plane_intercepts({'a': v['abc'][0], 'b': v['abc'][1], 'c': v['abc'][2]}),
     "x/a + y/b + z/c = 1",
     [("Пример 1", {'abc': ("2", "-3", "4")})])
_add("plane.two_vectors", G_PLANE, "Через точку параллельно двум векторам",
     [point3('M0', "Точка M₀", (2, -1, 1)), vec('u', "Вектор u⃗", (1, 2, -1)), vec('v', "Вектор v⃗", (-2, 0, 3))],
     _plane_two_vectors, "Нормаль n⃗ = u⃗ × v⃗",
     [("Пример 1", {'M0': ("2", "-1", "1"), 'u': ("1", "2", "-1"), 'v': ("-2", "0", "3")})])
_add("plane.parallel", G_PLANE, "Через точку параллельно плоскости",
     [point3('M0', "Точка M₀", (3, 4, -2)), plane('P1', "Исходная плоскость", (3, -2, 5, -14))],
     _plane_parallel, "Вектор нормали сохраняется: n⃗₁ = n⃗₂",
     [("Пример 1", {'M0': ("3", "4", "-2"), 'P1': ("3", "-2", "5", "-14")})])
_add("plane.perp_two_planes", G_PLANE, "Через точку перпендикулярно двум плоскостям",
     [point3('M0', "Точка M₀", (1, -1, 2)), plane('P1', "Плоскость P₁", (2, -3, 1, 5)), plane('P2', "Плоскость P₂", (1, 4, -2, -1))],
     _plane_perp_two, "Нормаль n⃗ = n⃗₁ × n⃗₂",
     [("Пример 1", {'M0': ("1", "-1", "2"), 'P1': ("2", "-3", "1", "5"), 'P2': ("1", "4", "-2", "-1")})])
_add("plane.line_point", G_PLANE, "Через прямую и точку вне её",
     [point3('ML', "Точка прямой M_L", (1, 0, -1)), vec('s', "Направляющий вектор s⃗", (2, -1, 3), ("m", "p", "q")),
      point3('M1', "Точка вне прямой M₁", (3, 2, 1))],
     _plane_line_point, "Нормаль n⃗ = s⃗ × M_LM₁⃗",
     [("Пример 1", {'ML': ("1", "0", "-1"), 's': ("2", "-1", "3"), 'M1': ("3", "2", "1")})])
_add("plane.normal_form", G_PLANE, "Нормальное уравнение плоскости",
     [plane('P', "Плоскость", (2, -2, 1, -12))],
     _plane_normal_form, "Нормирующий множитель μ, направляющие косинусы, расстояние p от начала координат.",
     [("Пример 1", {'P': ("2", "-2", "1", "-12")})])


# =============================================================================
# Прямая в пространстве
# =============================================================================
G_LINE = "Прямая в пространстве"


def _line_point_vector(v):
    res = LineSolver.by_point_and_vector(*v['M0'], *v['s'])
    sc = Scene3D().add_line(res['M0'], res['s'], "Прямая L").add_point(res['M0'], "M₀")
    sc.add_vector(res['M0'], res['s'], "s⃗", color=GREEN)
    return Result(res['steps'], f"Прямая: {res['canonical_str']}", res, scene3d=sc)


def _line_two_points(v):
    res = LineSolver.by_two_points(v['M1'], v['M2'])
    sc = Scene3D().add_line(f3(v['M1']), res['s'], "Прямая L").add_point(f3(v['M1']), "M₁").add_point(f3(v['M2']), "M₂")
    return Result(res['steps'], f"Прямая: {res['canonical_str']}", res, scene3d=sc)


def _line_general(v):
    res = LineSolver.from_general_to_canonical(v['P1'], v['P2'])
    sc = Scene3D().add_plane(*f3(v['P1']), "P₁", color=GRAY).add_plane(*f3(v['P2']), "P₂", color=AMBER)
    sc.add_line(res['M0'], res['s'], "Прямая пересечения", color=GREEN)
    return Result(res['steps'], f"Прямая: {res['canonical_str']}", res, scene3d=sc)


_add("line.point_vector", G_LINE, "По точке и направляющему вектору",
     [point3('M0', "Точка M₀", (2, -3, 1)), vec('s', "Направляющий вектор s⃗", (3, 4, -2), ("m", "p", "q"))],
     _line_point_vector, "Канонические и параметрические уравнения прямой.",
     [("Пример 1", {'M0': ("2", "-3", "1"), 's': ("3", "4", "-2")}),
      ("Пример 2", {'M0': ("-1", "4", "2"), 's': ("2", "-3", "5")})])
_add("line.two_points", G_LINE, "Через две точки",
     [point3('M1', "Точка M₁", (1, -2, 4)), point3('M2', "Точка M₂", (3, 1, 2))],
     _line_two_points, "Направляющий вектор s⃗ = M₁M₂⃗",
     [("Пример 1", {'M1': ("1", "-2", "4"), 'M2': ("3", "1", "2")})])
_add("line.general", G_LINE, "Из общих уравнений (пересечение плоскостей)",
     [plane('P1', "Плоскость P₁", (2, -1, 3, -4)), plane('P2', "Плоскость P₂", (1, 2, -1, 3))],
     _line_general, "s⃗ = n⃗₁ × n⃗₂ и частная точка M₀.",
     [("Пример 1", {'P1': ("2", "-1", "3", "-4"), 'P2': ("1", "2", "-1", "3")})])


# =============================================================================
# Взаимное расположение
# =============================================================================
G_REL = "Взаимное расположение"


def _two_planes(v, labels=("P₁", "P₂")):
    res = RelationsSolver.two_planes(v['P1'], v['P2'])
    sc = Scene3D().add_plane(*f3(v['P1']), labels[0], color=BLUE).add_plane(*f3(v['P2']), labels[1], color=AMBER)
    if not res['is_parallel'] and 'intersection_line' in res:
        sc.add_line(res['intersection_line']['M0'], res['intersection_line']['s'], "Линия пересечения", color=GREEN)
    return Result(res['steps'], res['status'], res, scene3d=sc)


def _line_plane(v):
    res = RelationsSolver.line_and_plane(v['M0'], v['s'], v['P'])
    sc = Scene3D().add_plane(*f3(v['P']), "Плоскость P", color=BLUE).add_line(f3(v['M0']), f3(v['s']), "Прямая L", color=RED)
    if 'intersection_point' in res:
        sc.add_point(res['intersection_point'], "K", color=GREEN)
    return Result(res['steps'], res['status'], res, scene3d=sc)


def _two_lines(v):
    res = RelationsSolver.two_lines(v['M1'], v['s1'], v['M2'], v['s2'])
    sc = Scene3D().add_line(f3(v['M1']), f3(v['s1']), "Прямая L₁", color=BLUE)
    sc.add_line(f3(v['M2']), f3(v['s2']), "Прямая L₂", color=RED)
    if res.get('is_intersecting') and 'intersection_point' in res:
        sc.add_point(res['intersection_point'], "Точка пересечения", color=GREEN)
    return Result(res['steps'], res['status'], res, scene3d=sc)


_add("rel.two_planes", G_REL, "Две плоскости",
     [plane('P1', "Плоскость P₁", (2, -1, 3, -5)), plane('P2', "Плоскость P₂", (1, 4, -1, 2))],
     _two_planes, "Параллельность, совпадение, угол, линия пересечения, биссекторные плоскости.",
     [("Пример 1", {'P1': ("2", "-1", "3", "-5"), 'P2': ("1", "4", "-1", "2")})])
_add("rel.line_plane", G_REL, "Прямая и плоскость",
     [point3('M0', "Точка прямой M₀", (1, 2, 3)), vec('s', "Направляющий вектор s⃗", (2, -1, 1), ("m", "p", "q")),
      plane('P', "Плоскость P", (1, 1, -1, -5))],
     _line_plane, "Принадлежность, параллельность, точка пересечения, угол.",
     [("Пример 1", {'M0': ("1", "2", "3"), 's': ("2", "-1", "1"), 'P': ("1", "1", "-1", "-5")})])
_add("rel.two_lines", G_REL, "Две прямые",
     [point3('M1', "Точка M₁ прямой L₁", (1, 0, -2)), vec('s1', "Вектор s⃗₁", (2, -1, 4), ("m", "p", "q")),
      point3('M2', "Точка M₂ прямой L₂", (3, -1, 2)), vec('s2', "Вектор s⃗₂", (1, 2, -3), ("m", "p", "q"))],
     _two_lines, "Совпадение, параллельность, пересечение или скрещивание; угол и расстояние.",
     [("Пример 1", {'M1': ("1", "0", "-2"), 's1': ("2", "-1", "4"), 'M2': ("3", "-1", "2"), 's2': ("1", "2", "-3")})])


# =============================================================================
# Расстояния и проекции
# =============================================================================
G_DIST = "Расстояния и проекции"


def _point_plane(v):
    res = DistancesAndProjections.point_to_plane(v['M0'], v['P'])
    p0, h, s = f3(v['M0']), f3(res['projection']), f3(res['symmetric'])
    sc = Scene3D().add_plane(*f3(v['P']), "Плоскость P", color=BLUE)
    sc.add_point(p0, "M₀", color=RED).add_point(h, "H", color=GREEN).add_point(s, "M'", color=AMBER)
    sc.add_segment(p0, h, "d", color=RED).add_segment(h, s, "", color=AMBER)
    return Result(res['steps'], "Расстояние, проекция и симметричная точка найдены", res, scene3d=sc)


def _point_line(v):
    res = DistancesAndProjections.point_to_line(v['M0'], v['M1'], v['s'])
    p0, h, s = f3(v['M0']), f3(res['projection']), f3(res['symmetric'])
    sc = Scene3D().add_line(f3(v['M1']), f3(v['s']), "Прямая L", color=BLUE)
    sc.add_point(p0, "M₀", color=RED).add_point(h, "H", color=GREEN).add_point(s, "M'", color=AMBER)
    sc.add_segment(p0, h, "d", color=RED)
    return Result(res['steps'], "Расстояние, проекция и симметричная точка найдены", res, scene3d=sc)


_add("dist.point_plane", G_DIST, "От точки до плоскости",
     [point3('M0', "Точка M₀", (1, 2, 3)), plane('P', "Плоскость P", (2, -2, 1, -5))],
     _point_plane, "Расстояние d, проекция H, симметричная точка M'.",
     [("Пример 1", {'M0': ("1", "2", "3"), 'P': ("2", "-2", "1", "-5")})])
_add("dist.point_line", G_DIST, "От точки до прямой",
     [point3('M0', "Точка M₀", (3, -1, 2)), point3('M1', "Точка прямой M₁", (1, 2, -1)),
      vec('s', "Направляющий вектор s⃗", (2, 1, -2), ("m", "p", "q"))],
     _point_line, "d = |M₁M₀⃗ × s⃗| / |s⃗|, проекция H, симметричная точка M'.",
     [("Пример 1", {'M0': ("3", "-1", "2"), 'M1': ("1", "2", "-1"), 's': ("2", "1", "-2")})])
_add("dist.parallel_planes", G_DIST, "Между параллельными плоскостями",
     [plane('P1', "Плоскость P₁", (2, -1, 2, -4)), plane('P2', "Плоскость P₂", (4, -2, 4, 10))],
     _two_planes, "d = |D₁ − k·D₂| / √(A² + B² + C²)",
     [("Пример 1", {'P1': ("2", "-1", "2", "-4"), 'P2': ("4", "-2", "4", "10")})])
_add("dist.skew_lines", G_DIST, "Между скрещивающимися прямыми",
     [point3('M1', "Точка M₁ прямой L₁", (1, -2, 1)), vec('s1', "Вектор s⃗₁", (2, 3, 1), ("m", "p", "q")),
      point3('M2', "Точка M₂ прямой L₂", (0, 1, -3)), vec('s2', "Вектор s⃗₂", (1, -2, 2), ("m", "p", "q"))],
     _two_lines, "d = |(M₁M₂⃗, s⃗₁, s⃗₂)| / |s⃗₁ × s⃗₂|",
     [("Пример 1", {'M1': ("1", "-2", "1"), 's1': ("2", "3", "1"), 'M2': ("0", "1", "-3"), 's2': ("1", "-2", "2")})])


# =============================================================================
# Пучок плоскостей
# =============================================================================
def _pencil(v):
    res = PlanePencilSolver.pencil_through_point(v['P1'], v['P2'], v['M0'])
    sc = Scene3D().add_plane(*f3(v['P1']), "P₁", color=GRAY).add_plane(*f3(v['P2']), "P₂", color=AMBER)
    sc.add_plane(res['A'], res['B'], res['C'], res['D'], "Плоскость из пучка", color=GREEN).add_point(f3(v['M0']), "M₀")
    return Result(res['steps'], f"Плоскость: {res['equation_str']}", res, scene3d=sc)


_add("pencil.through_point", "Пучок плоскостей", "Плоскость пучка через точку",
     [plane('P1', "Плоскость P₁", (1, 2, -1, 3)), plane('P2', "Плоскость P₂", (2, -1, 1, -4)), point3('M0', "Точка M₀", (1, 1, 1))],
     _pencil, "α·P₁ + β·P₂ = 0, проходящая через M₀.",
     [("Пример 1", {'P1': ("1", "2", "-1", "3"), 'P2': ("2", "-1", "1", "-4"), 'M0': ("1", "1", "1")})])


# =============================================================================
# Геометрия на плоскости
# =============================================================================
G_2D = "Геометрия на плоскости"


def _segment(v):
    res = SegmentSolver.solve(v['A'], v['B'], v['K'], *v['ratio'])
    return Result(res['steps'], "Точки C, D и центр масс G найдены", res, scene2d=res['plot2d'])


def _triangle(v):
    res = TriangleSolver.solve(v['A'], v['B'], v['C'], v['median'], v['altitude'], v['angle'])
    return Result(res['steps'], f"Площадь треугольника S = {res['area']}", res, scene2d=res['plot2d'])


def _line_point_2d(v):
    a, b, c = v['l']
    res = PlaneLineSolver.solve(a, b, c, v['M'])
    return Result(res['steps'], "Параллельная, перпендикуляр, проекция и симметричная точка найдены", res, scene2d=res['plot2d'])


_add("planar.segment", G_2D, "Деление отрезка, середина, центр масс",
     [point2('A', "Точка A", (-3, 2)), point2('B', "Точка B", (7, -3)), point2('K', "Точка K", (2, 4)),
      vec('ratio', "Отношение AC : CB", (3, 2), ("m", "n"), hint="Отрицательное отношение — внешнее деление")],
     _segment, "Точка C делит AB в отношении m : n; D — если B середина AD; центр масс треугольника ABK.",
     [("Пример 1", {'A': ("-3", "2"), 'B': ("7", "-3"), 'K': ("2", "4"), 'ratio': ("3", "2")}),
      ("Пример 2", {'A': ("4", "-1"), 'B': ("-6", "4"), 'K': ("-1", "3"), 'ratio': ("2", "3")}),
      ("Пример 3", {'A': ("-2", "-5"), 'B': ("6", "7"), 'K': ("5", "1"), 'ratio': ("1", "3")})])
_add("planar.triangle", G_2D, "Треугольник: стороны, медиана, высота, биссектриса",
     [point2('A', "Вершина A", (1, 2)), point2('B', "Вершина B", (4, 6)), point2('C', "Вершина C", (6, -10)),
      choice('median', "Медиана из вершины", ("A", "B", "C"), "A"),
      choice('altitude', "Высота из вершины", ("A", "B", "C"), "B"),
      choice('angle', "Угол и биссектриса при вершине", ("A", "B", "C"), "A")],
     _triangle, "Уравнения и длины сторон, медиана, высота с основанием, внутренний угол, биссектриса.",
     [("Пример 1", {'A': ("1", "2"), 'B': ("4", "6"), 'C': ("6", "-10")}),
      ("Пример 2", {'A': ("-2", "1"), 'B': ("2", "4"), 'C': ("3", "13")}),
      ("Пример 3", {'A': ("1", "-1"), 'B': ("-2", "3"), 'C': ("13", "4")})])
_add("planar.line_point", G_2D, "Прямая и точка на плоскости",
     [vec('l', "Прямая l", (3, -4, 12), ("A", "B", "C"), hint="A·x + B·y + C = 0"), point2('M', "Точка M", (6, -5))],
     _line_point_2d, "Параллельная и перпендикулярная прямые через M, проекция H, расстояние, симметричная точка M'.",
     [("Пример 1", {'l': ("3", "-4", "12"), 'M': ("6", "-5")}),
      ("Пример 2", {'l': ("4", "3", "-6"), 'M': ("7", "1")}),
      ("Пример 3", {'l': ("5", "-12", "2"), 'M': ("7", "-11")})])


# =============================================================================
# Кривые второго порядка
# =============================================================================
def _conic(v):
    res = ConicSolver.solve(*v['coef'])
    return Result(res['steps'], f"{res['type']}: {res['canonical']}", res, scene2d=res['plot2d'])


_add("conics.canonical", "Кривые второго порядка", "Приведение к каноническому виду",
     [vec('coef', "Коэффициенты", (4, 0, 9, -16, 54, 61), ("A", "B", "C", "D", "E", "F"),
          hint="A·x² + B·xy + C·y² + D·x + E·y + F = 0")],
     _conic, "Тип кривой, поворот и перенос осей, каноническое уравнение, центр или вершина, полуоси, фокусы, "
             "эксцентриситет, асимптоты, директрисы, вырожденные случаи.",
     [("Эллипс", {'coef': ("4", "0", "9", "-16", "54", "61")}),
      ("Парабола", {'coef': ("0", "0", "1", "-8", "-4", "20")}),
      ("Гипербола", {'coef': ("9", "0", "-16", "36", "32", "-124")}),
      ("Парабола (ветви вниз)", {'coef': ("1", "0", "0", "6", "4", "1")}),
      ("Эллипс (большая ось по y)", {'coef': ("25", "0", "16", "50", "-64", "-311")}),
      ("Парабола (ветви влево)", {'coef': ("0", "0", "1", "6", "2", "-11")}),
      ("Эллипс с поворотом осей", {'coef': ("5", "2", "5", "-12", "-12", "0")}),
      ("Гипербола с поворотом осей", {'coef': ("2", "2*sqrt(3)", "0", "-4", "-2*sqrt(3)", "-1")})])


# =============================================================================
# Комплексные задачи
# =============================================================================
def _space_task(v):
    res = SpaceTaskSolver.solve(v['A'], v['B'], v['C'], v['D'], v['P1'], v['P2'])
    sc = Scene3D()
    sc.add_plane(*f3(res['plane']), "Плоскость ABC", color=BLUE)
    sc.add_plane(*f3(res['parallel_plane']), "Параллельная через D", color=GREEN)
    for nm, p in res['points'].items():
        sc.add_point(f3(p), nm, color=RED if nm == 'D' else AMBER)
    sc.add_point(f3(res['H']), "H", color=GREEN).add_segment(f3(res['points']['D']), f3(res['H']), "DH", color=RED)
    A, s = res['line_AD']
    sc.add_line(f3(A), f3(s), "Прямая AD", color=AMBER)
    M0, s2 = res['line_l']
    sc.add_line(f3(M0), f3(s2), "Прямая l", color=PINK)
    return Result(res['steps'], f"Расстояние от D до плоскости ABC: d = {res['distance']}", res, scene3d=sc)


_add("composite.plane_abc", "Комплексные задачи", "Плоскость ABC, прямая AD, перпендикуляр DH, прямая l",
     [point3('A', "Точка A", (2, 0, 0)), point3('B', "Точка B", (0, -4, 0)), point3('C', "Точка C", (0, 0, 2)),
      point3('D', "Точка D", (5, -2, 5)),
      plane('P1', "Прямая l: плоскость 1", (2, -1, 1, -2)), plane('P2', "Прямая l: плоскость 2", (2, -1, -1, 0))],
     _space_task, "Плоскость ABC (общее уравнение и в отрезках), прямая AD и угол с плоскостью, перпендикуляр DH, "
                  "расстояние, параллельная плоскость через D, прямая l из общих уравнений и её положение.",
     [("Пример 1", {'A': ("2", "0", "0"), 'B': ("0", "-4", "0"), 'C': ("0", "0", "2"), 'D': ("5", "-2", "5"),
                    'P1': ("2", "-1", "1", "-2"), 'P2': ("2", "-1", "-1", "0")}),
      ("Пример 2", {'A': ("-2", "0", "0"), 'B': ("0", "-1", "0"), 'C': ("0", "0", "1"), 'D': ("4", "3", "-3"),
                    'P1': ("1", "1", "-1", "-1"), 'P2': ("1", "-1", "-1", "1")}),
      ("Пример 3", {'A': ("3", "0", "0"), 'B': ("0", "3", "0"), 'C': ("0", "0", "-6"), 'D': ("-3", "-3", "0"),
                    'P1': ("1", "1", "0", "-3"), 'P2': ("1", "1", "2", "-3")})])
