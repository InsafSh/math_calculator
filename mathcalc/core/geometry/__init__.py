"""Раздел «Аналитическая геометрия»."""

from .space import PlaneSolver, LineSolver, RelationsSolver, DistancesAndProjections, PlanePencilSolver
from .planar import SegmentSolver, TriangleSolver, PlaneLineSolver
from .conics import ConicSolver
from .composite import SpaceTaskSolver

__all__ = [
    "PlaneSolver", "LineSolver", "RelationsSolver", "DistancesAndProjections", "PlanePencilSolver",
    "SegmentSolver", "TriangleSolver", "PlaneLineSolver", "ConicSolver", "SpaceTaskSolver",
]
