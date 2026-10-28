"""
Единый формат результата задачи.

Решатель любого раздела возвращает Result: текст пошагового решения, краткий итог,
численные значения и (необязательно) сцены для 2D- и 3D-визуализации.
Сцены — простые описания объектов без привязки к GUI; их рисует пакет mathcalc.plotting.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

Point2 = Tuple[float, float]
Point3 = Tuple[float, float, float]


def new_scene2d(equal: bool = True, title: str = "") -> Dict[str, Any]:
    """
    Пустая 2D-сцена. Формат элементов:
      points:    (x, y, подпись, цвет)                       — отмеченные точки с подписью
      segments:  ((x1, y1), (x2, y2), подпись, цвет, стиль)  — отрезки
      lines:     (x0, y0, dx, dy, подпись, цвет[, стиль])    — бесконечные прямые
      curves:    (xs, ys, подпись, цвет[, стиль])            — кривые (NaN разрывает линию)
      scatter:   (xs, ys, подпись, цвет)                     — облако точек без подписей
      errorbars: (xs, ys, yerr, xerr, подпись, цвет)         — точки с погрешностями (xerr/yerr могут быть None)
      bands:     (xs, y_низ, y_верх, подпись, цвет)          — закрашенная полоса (доверительный интервал, площадь)
      contours:  (X, Y, Z, уровни, подпись, цвет)            — линии уровня Z(X, Y) = уровни
      bars:      (подписи, значения, цвет)                   — столбчатая диаграмма (вместо координатного чертежа)
    Параметры вида: title, equal (одинаковый масштаб осей), xlabel, ylabel, xlim, ylim.
    """
    return {'points': [], 'segments': [], 'lines': [], 'curves': [], 'scatter': [], 'errorbars': [],
            'bands': [], 'contours': [], 'bars': None, 'title': title, 'equal': equal, 'xlabel': '', 'ylabel': '',
            'xlim': None, 'ylim': None}


@dataclass
class Scene3D:
    """Описание 3D-сцены: плоскости, прямые, точки, векторы, отрезки."""
    planes: List[Dict[str, Any]] = field(default_factory=list)
    lines: List[Dict[str, Any]] = field(default_factory=list)
    points: List[Dict[str, Any]] = field(default_factory=list)
    vectors: List[Dict[str, Any]] = field(default_factory=list)
    segments: List[Dict[str, Any]] = field(default_factory=list)
    surfaces: List[Dict[str, Any]] = field(default_factory=list)
    curves: List[Dict[str, Any]] = field(default_factory=list)
    labels: Tuple[str, str, str] = ("X", "Y", "Z")

    def add_plane(self, A, B, C, D, label: str = "Плоскость", color: Optional[str] = None):
        self.planes.append({'A': float(A), 'B': float(B), 'C': float(C), 'D': float(D), 'label': label, 'color': color})
        return self

    def add_line(self, point, direction, label: str = "Прямая", color: Optional[str] = None):
        self.lines.append({'p': tuple(float(c) for c in point), 's': tuple(float(c) for c in direction),
                           'label': label, 'color': color})
        return self

    def add_point(self, point, label: str = "Точка", color: str = "#F59E0B"):
        self.points.append({'p': tuple(float(c) for c in point), 'label': label, 'color': color})
        return self

    def add_vector(self, origin, vec, label: str = "Вектор", color: str = "#10B981"):
        self.vectors.append({'p': tuple(float(c) for c in origin), 'v': tuple(float(c) for c in vec),
                             'label': label, 'color': color})
        return self

    def add_segment(self, p1, p2, label: str = "", color: str = "#94A3B8"):
        self.segments.append({'p1': tuple(float(c) for c in p1), 'p2': tuple(float(c) for c in p2),
                              'label': label, 'color': color})
        return self

    def add_surface(self, X, Y, Z, label: str = "", cmap: str = "viridis"):
        """Поверхность по сеткам X, Y, Z (NaN — пропуски вне области определения)."""
        self.surfaces.append({'X': X, 'Y': Y, 'Z': Z, 'label': label, 'cmap': cmap})
        return self

    def add_curve(self, xs, ys, zs, label: str = "", color: str = "#EF4444"):
        """Пространственная кривая по массивам координат."""
        self.curves.append({'x': xs, 'y': ys, 'z': zs, 'label': label, 'color': color})
        return self

    def is_empty(self) -> bool:
        return not (self.planes or self.lines or self.points or self.vectors or self.segments
                    or self.surfaces or self.curves)


@dataclass
class Result:
    """Результат решения задачи."""
    steps: str
    summary: str = ""
    values: Dict[str, Any] = field(default_factory=dict)
    scene2d: Optional[Dict[str, Any]] = None
    scene3d: Optional[Scene3D] = None
