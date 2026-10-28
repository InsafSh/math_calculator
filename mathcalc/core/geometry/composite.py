"""
Комплексная задача в пространстве: плоскость по трём точкам, прямая через две точки,
перпендикуляр к плоскости, параллельная плоскость, прямая из общих уравнений.
"""

from typing import Any, Dict, List

from ..common import simp, sgn, ex, vec_str, box, parse_point
from .space import PlaneSolver, LineSolver, RelationsSolver, DistancesAndProjections


# ----------------------------------------------------------------------------
# Комплексная задача в пространстве
# ----------------------------------------------------------------------------

class SpaceTaskSolver:
    """Плоскость ABC, прямая AD, перпендикуляр DH, параллельная плоскость, прямая l (общий вид)."""

    @staticmethod
    def solve(pA, pB, pC, pD, pl1, pl2) -> Dict[str, Any]:
        A, B, C, D = [parse_point(p, 3) for p in (pA, pB, pC, pD)]

        def banner(txt):
            return ["", f"📐 {txt}", ""]

        steps: List[str] = []

        # а) плоскость ABC
        plane = PlaneSolver.by_three_points(A, B, C)
        a_, b_, c_, d_ = plane['A'], plane['B'], plane['C'], plane['D']
        steps += banner("а) ОБЩЕЕ УРАВНЕНИЕ ПЛОСКОСТИ ABC И УРАВНЕНИЕ В ОТРЕЗКАХ")
        steps.append(plane['steps'])
        steps += ["", "⚙️ Уравнение в отрезках:  x/a + y/b + z/c = 1"]
        if all(sgn(v) != 0 for v in (a_, b_, c_, d_)):
            ia, ib, ic = simp(-d_ / a_), simp(-d_ / b_), simp(-d_ / c_)
            seg_eq = f"x/({ex(ia)}) + y/({ex(ib)}) + z/({ex(ic)}) = 1"
            steps += [f"   Переносим D вправо и делим на −D:  a = −D/A = {ex(ia)},  b = −D/B = {ex(ib)},  c = −D/C = {ex(ic)}"]
            steps += box([seg_eq], "answer")
        else:
            seg_eq = None
            steps.append("   Уравнение в отрезках не существует: плоскость проходит через начало координат или параллельна одной из осей (какой-то из коэффициентов A, B, C, D равен нулю).")

        # б) прямая AD и угол с плоскостью ABC
        lineAD = LineSolver.by_two_points(A, D)
        steps += banner("б) ПРЯМАЯ AD И УГОЛ МЕЖДУ ПРЯМОЙ AD И ПЛОСКОСТЬЮ ABC")
        steps.append(lineAD['steps'])
        steps += ["", "⚙️ Угол между прямой AD и плоскостью ABC:"]
        rel_AD = RelationsSolver.line_and_plane(A, lineAD['s'], (a_, b_, c_, d_))
        steps.append(rel_AD['steps'])

        # в) перпендикуляр DH, H, расстояние
        nrm = (a_, b_, c_)
        perp = LineSolver.by_point_and_vector(D[0], D[1], D[2], a_, b_, c_)
        proj = DistancesAndProjections.point_to_plane(D, (a_, b_, c_, d_))
        steps += banner("в) ПЕРПЕНДИКУЛЯР DH К ПЛОСКОСТИ ABC, ОСНОВАНИЕ H, РАССТОЯНИЕ")
        steps += ["⚙️ Направляющий вектор перпендикуляра = вектор нормали плоскости n⃗ = " + vec_str(nrm)]
        steps.append(perp['steps'])
        steps.append("")
        steps.append(proj['steps'])

        # г) параллельная плоскость
        par = PlaneSolver.by_point_parallel_to_plane(D, a_, b_, c_, d_)
        steps += banner("г) ПЛОСКОСТЬ ЧЕРЕЗ D, ПАРАЛЛЕЛЬНАЯ ПЛОСКОСТИ ABC")
        steps.append(par['steps'])

        # д) прямая l
        gen = LineSolver.from_general_to_canonical(pl1, pl2)
        steps += banner("д) КАНОНИЧЕСКИЙ ВИД ПРЯМОЙ l И ЕЁ ПОЛОЖЕНИЕ ОТНОСИТЕЛЬНО ПЛОСКОСТИ ABC")
        steps.append(gen['steps'])
        steps += ["", "⚙️ Взаимное расположение прямой l и плоскости ABC:"]
        rel_l = RelationsSolver.line_and_plane(gen['M0'], gen['s'], (a_, b_, c_, d_))
        steps.append(rel_l['steps'])

        return {
            'plane': (a_, b_, c_, d_), 'points': {'A': A, 'B': B, 'C': C, 'D': D},
            'H': proj['projection'], 'distance': proj['distance'],
            'parallel_plane': (par['A'], par['B'], par['C'], par['D']),
            'line_AD': (A, lineAD['s']), 'line_l': (gen['M0'], gen['s']),
            'intercept_eq': seg_eq,
            'steps': "\n".join(steps)
        }
