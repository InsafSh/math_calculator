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


def new_scene2d() -> Dict[str, Any]:
    """
    Пустая 2D-сцена. Формат элементов:
      points:   (x, y, подпись, цвет)
      segments: ((x1, y1), (x2, y2), подпись, цвет, стиль линии)
      lines:    (x0, y0, dx, dy, подпись, цвет)  — бесконечная прямая через точку по направлению
      curves:   (массив x, массив y, подпись, цвет)
      title:    заголовок графика
    """
    return {'points': [], 'segments': [], 'lines': [], 'curves': [], 'title': ''}


@dataclass
class Scene3D:
    """Описание 3D-сцены: плоскости, прямые, точки, векторы, отрезки."""
    planes: List[Dict[str, Any]] = field(default_factory=list)
    lines: List[Dict[str, Any]] = field(default_factory=list)
    points: List[Dict[str, Any]] = field(default_factory=list)
    vectors: List[Dict[str, Any]] = field(default_factory=list)
    segments: List[Dict[str, Any]] = field(default_factory=list)

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

    def is_empty(self) -> bool:
        return not (self.planes or self.lines or self.points or self.vectors or self.segments)


@dataclass
class Result:
    """Результат решения задачи."""
    steps: str
    summary: str = ""
    values: Dict[str, Any] = field(default_factory=dict)
    scene2d: Optional[Dict[str, Any]] = None
    scene3d: Optional[Scene3D] = None
