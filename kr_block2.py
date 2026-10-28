"""
KR Block 2 - Контрольная работа, блок II: «Аналитическая геометрия на плоскости и в пространстве».
Универсальные решатели типовых задач 6-10 из KR_varianty_s_otvetami.pdf с пошаговым решением на русском.

  6.  Деление отрезка в заданном отношении, середина, центр масс треугольника.
  7.  Треугольник на плоскости: стороны, медиана, высота, угол, биссектриса.
  8.  Прямая и точка на плоскости: параллельная, перпендикуляр, проекция, расстояние, симметрия.
  9.  Кривые 2-го порядка: приведение к каноническому виду (перенос и поворот осей).
  10. Комплексная задача в пространстве: плоскость ABC, прямая AD, перпендикуляр DH,
      параллельная плоскость, прямая в общем виде.

Каждый решатель возвращает словарь: 'steps' (текст решения), 'plot2d' / данные для 3D и числовые результаты.
"""

import sympy as sp
import numpy as np
from typing import Dict, Any, List, Tuple

from geometry_core import (
    parse_number, fmt_num, to_pretty_math, simplify_plane_eq,
    PlaneSolver, LineSolver, RelationsSolver, DistancesAndProjections
)

COL_MAIN = "#3B82F6"
COL_RED = "#EF4444"
COL_GREEN = "#10B981"
COL_AMBER = "#F59E0B"
COL_PINK = "#EC4899"
COL_GRAY = "#94A3B8"


# ----------------------------------------------------------------------------
# Вспомогательные функции форматирования и вычислений
# ----------------------------------------------------------------------------

def _simp(v):
    """Упрощение выражения (корни, дроби)."""
    return sp.simplify(sp.radsimp(sp.sympify(v)))


def _sgn(v) -> int:
    """Знак числа (с числовой проверкой нуля)."""
    f = float(sp.N(v, 30))
    if abs(f) < 1e-12:
        return 0
    return 1 if f > 0 else -1


def _s(v) -> str:
    """Точное значение без десятичного приближения."""
    return to_pretty_math(_simp(v))


def _add(v) -> str:
    """Слагаемое со знаком: '+ 4' или '- 4'."""
    v = _simp(v)
    return f"- {_s(-v)}" if _sgn(v) < 0 else f"+ {_s(v)}"


def _shift(var: str, v0) -> str:
    """Выражение (var − v0) без двойных знаков."""
    v0 = _simp(v0)
    if _sgn(v0) == 0:
        return var
    return f"({var} + {_s(-v0)})" if _sgn(v0) < 0 else f"({var} − {_s(v0)})"


def _pt(p) -> str:
    return "(" + "; ".join(_s(c) for c in p) + ")"


def _pt_full(p) -> str:
    return "(" + "; ".join(fmt_num(_simp(c)) for c in p) + ")"


def _vec(p) -> str:
    return "(" + "; ".join(_s(c) for c in p) + ")"


def _dist(p, q):
    return _simp(sp.sqrt(sum((a - b) ** 2 for a, b in zip(p, q))))


def _num(v) -> float:
    return float(sp.N(v, 20))


def _box(lines: List[str], kind: str = "formula") -> List[str]:
    """Рамка вокруг строк. kind = formula (жёлтая) | answer (зелёная)."""
    w = max(len(l) for l in lines) + 2
    if kind == "answer":
        tl, tr, bl, br, h, v = "╔", "╗", "╚", "╝", "═", "║"
    else:
        tl, tr, bl, br, h, v = "┌", "┐", "└", "┘", "─", "│"
    out = [f"   {tl}{h * w}{tr}"]
    for l in lines:
        out.append(f"   {v} {l.ljust(w - 1)}{v}")
    out.append(f"   {bl}{h * w}{br}")
    return out


def _line_eq(A, B, C) -> Tuple[str, Tuple]:
    """Общее уравнение прямой Ax + By + C = 0 в приведённом виде. Возвращает (строка, (A, B, C))."""
    A, B, C = _simp(A), _simp(B), _simp(C)
    As, Bs, _, Cs, eq = simplify_plane_eq(A, B, sp.Integer(0), C)
    return to_pretty_math(eq), (As, Bs, Cs)


def _slope_form(A, B, C) -> str:
    """Уравнение с угловым коэффициентом y = kx + b (или x = const)."""
    if _sgn(B) == 0:
        return f"x = {_s(-C / A)}  (вертикальная прямая, углового коэффициента нет)"
    k = _simp(-A / B)
    b = _simp(-C / B)
    if _sgn(b) == 0:
        return f"y = {_s(k)}·x"
    sign = "+" if _sgn(b) > 0 else "-"
    return f"y = {_s(k)}·x {sign} {_s(abs(b))}"


def _line_through(p, q) -> Tuple[sp.Expr, sp.Expr, sp.Expr]:
    """Коэффициенты (A, B, C) прямой через две точки плоскости."""
    A = q[1] - p[1]
    B = p[0] - q[0]
    C = -(A * p[0] + B * p[1])
    return _simp(A), _simp(B), _simp(C)


def _parse_pt(p, dim: int = 2):
    pt = [parse_number(c) for c in p]
    if len(pt) != dim:
        raise ValueError(f"Ожидалась точка с {dim} координатами")
    return tuple(pt)


def _new_plot() -> Dict[str, list]:
    return {'points': [], 'segments': [], 'lines': [], 'curves': [], 'title': ''}


# ----------------------------------------------------------------------------
# Задача 6. Деление отрезка в отношении, середина, центр масс
# ----------------------------------------------------------------------------

class SegmentSolver:
    """Деление отрезка в отношении λ, симметричная точка, пересечение медиан."""

    @staticmethod
    def solve(pA, pB, pK, m, n) -> Dict[str, Any]:
        A, B, K = _parse_pt(pA), _parse_pt(pB), _parse_pt(pK)
        m, n = parse_number(m), parse_number(n)
        if _sgn(m + n) == 0:
            raise ValueError("Сумма m + n равна нулю: точка деления не существует (отрезок делится «в бесконечности»)")
        if _sgn(m) == 0 and _sgn(n) == 0:
            raise ValueError("Отношение m : n не может быть 0 : 0")

        lam = _simp(m / n) if _sgn(n) != 0 else None
        # AC : CB = m : n  =>  C = (n·A + m·B) / (m + n)
        C = tuple(_simp((n * a + m * b) / (m + n)) for a, b in zip(A, B))
        D = tuple(_simp(2 * b - a) for a, b in zip(A, B))
        G = tuple(_simp((a + b + k) / 3) for a, b, k in zip(A, B, K))
        Mid = tuple(_simp((a + b) / 2) for a, b in zip(A, B))
        MidBK = tuple(_simp((b + k) / 2) for b, k in zip(B, K))

        steps = [
            "📌 ЭТАП 1. ТЕОРЕТИЧЕСКИЕ ФОРМУЛЫ",
            "Деление отрезка в отношении λ = m : n (AC : CB = m : n):",
        ]
        steps += _box([
            "x_C = (n·x_A + m·x_B) / (m + n),   y_C = (n·y_A + m·y_B) / (m + n)",
            "Середина отрезка: x_M = (x_A + x_B)/2,   y_M = (y_A + y_B)/2",
            "Центр масс (пересечение медиан): x_G = (x_A + x_B + x_K)/3",
        ])
        steps += [
            "",
            "📝 ЭТАП 2. ИСХОДНЫЕ ДАННЫЕ",
            f"   ▸ A{_pt(A)},  B{_pt(B)},  K{_pt(K)}",
            f"   ▸ Отношение AC : CB = {_s(m)} : {_s(n)}",
            "",
            f"⚙️ а) ТОЧКА C, ДЕЛЯЩАЯ ОТРЕЗОК AB В ОТНОШЕНИИ {_s(m)} : {_s(n)}",
            f"   x_C = ({_s(n)}·({_s(A[0])}) + {_s(m)}·({_s(B[0])})) / ({_s(m)} + {_s(n)}) = {_s(C[0])}",
            f"   y_C = ({_s(n)}·({_s(A[1])}) + {_s(m)}·({_s(B[1])})) / ({_s(m)} + {_s(n)}) = {_s(C[1])}",
        ]
        if lam is not None and _sgn(lam) < 0:
            steps.append("   (отношение отрицательное — точка C лежит на продолжении отрезка AB, деление внешнее)")
        steps += _box([f"C{_pt(C)}"], "answer")
        steps += [
            "",
            "⚙️ б) ТОЧКА D, ЕСЛИ B — СЕРЕДИНА ОТРЕЗКА AD",
            "   B = (A + D)/2   ⟹   D = 2B − A",
            f"   x_D = 2·({_s(B[0])}) − ({_s(A[0])}) = {_s(D[0])}",
            f"   y_D = 2·({_s(B[1])}) − ({_s(A[1])}) = {_s(D[1])}",
        ]
        steps += _box([f"D{_pt(D)}"], "answer")
        steps += [
            "",
            "⚙️ в) ТОЧКА ПЕРЕСЕЧЕНИЯ МЕДИАН ТРЕУГОЛЬНИКА ABK",
            f"   x_G = ({_s(A[0])} + {_s(B[0])} + {_s(K[0])}) / 3 = {_s(G[0])}",
            f"   y_G = ({_s(A[1])} + {_s(B[1])} + {_s(K[1])}) / 3 = {_s(G[1])}",
            f"   Проверка: G делит медиану K→M (M{_pt(Mid)} — середина AB) в отношении 2 : 1 от вершины.",
        ]
        steps += _box([f"G{_pt(G)}"], "answer")

        plot = _new_plot()
        plot['title'] = "Деление отрезка и центр масс"
        for nm, p, col in (("A", A, COL_MAIN), ("B", B, COL_MAIN), ("K", K, COL_MAIN),
                           ("C", C, COL_RED), ("D", D, COL_AMBER), ("G", G, COL_GREEN)):
            plot['points'].append((_num(p[0]), _num(p[1]), nm, col))
        plot['segments'] += [
            ((_num(A[0]), _num(A[1])), (_num(B[0]), _num(B[1])), "", COL_MAIN, '-'),
            ((_num(B[0]), _num(B[1])), (_num(K[0]), _num(K[1])), "", COL_MAIN, '-'),
            ((_num(K[0]), _num(K[1])), (_num(A[0]), _num(A[1])), "", COL_MAIN, '-'),
            ((_num(B[0]), _num(B[1])), (_num(D[0]), _num(D[1])), "AD", COL_AMBER, '--'),
            ((_num(K[0]), _num(K[1])), (_num(Mid[0]), _num(Mid[1])), "", COL_GREEN, ':'),
            ((_num(A[0]), _num(A[1])), (_num(MidBK[0]), _num(MidBK[1])), "", COL_GREEN, ':'),
        ]
        return {'C': C, 'D': D, 'G': G, 'steps': "\n".join(steps), 'plot2d': plot}


# ----------------------------------------------------------------------------
# Задача 7. Треугольник на плоскости
# ----------------------------------------------------------------------------

class TriangleSolver:
    """Треугольник ABC на плоскости: стороны, медиана, высота, угол, биссектриса."""

    NAMES = ["A", "B", "C"]

    @staticmethod
    def solve(pA, pB, pC, med_v: str = "A", alt_v: str = "B", ang_v: str = "A") -> Dict[str, Any]:
        P = [_parse_pt(pA), _parse_pt(pB), _parse_pt(pC)]
        N = TriangleSolver.NAMES
        area2 = _simp((P[1][0] - P[0][0]) * (P[2][1] - P[0][1]) - (P[2][0] - P[0][0]) * (P[1][1] - P[0][1]))
        if _sgn(area2) == 0:
            raise ValueError("Точки A, B, C лежат на одной прямой — треугольник вырожден")
        area = _simp(sp.Abs(area2) / 2)

        steps = [
            "📌 ЭТАП 1. ТЕОРЕТИЧЕСКИЕ ФОРМУЛЫ",
        ]
        steps += _box([
            "Прямая через две точки:  (x − x₁)/(x₂ − x₁) = (y − y₁)/(y₂ − y₁)",
            "Длина стороны:  |PQ| = √((x₂ − x₁)² + (y₂ − y₁)²)",
            "Угол при вершине:  cos∠ = (u⃗·v⃗) / (|u⃗|·|v⃗|)",
            "Расстояние от точки до прямой:  d = |A·x₀ + B·y₀ + C| / √(A² + B²)",
            "Биссектриса делит противоположную сторону в отношении |VP| : |VQ|",
        ])
        steps += ["", f"📝 ЭТАП 2. ВЕРШИНЫ:  A{_pt(P[0])},  B{_pt(P[1])},  C{_pt(P[2])}",
                  f"   ▸ Площадь S = ½·|(B−A)×(C−A)| = {fmt_num(area)}", ""]

        plot = _new_plot()
        plot['title'] = "Треугольник ABC"
        for i in range(3):
            plot['points'].append((_num(P[i][0]), _num(P[i][1]), N[i], COL_MAIN))
            j = (i + 1) % 3
            plot['segments'].append(((_num(P[i][0]), _num(P[i][1])), (_num(P[j][0]), _num(P[j][1])), "", COL_MAIN, '-'))

        # --- а) стороны ---
        steps.append("⚙️ а) УРАВНЕНИЯ И ДЛИНЫ СТОРОН")
        sides_info = {}
        perimeter = 0
        for (i, j) in ((0, 1), (0, 2), (1, 2)):
            A_, B_, C_ = _line_through(P[i], P[j])
            eq, coef = _line_eq(A_, B_, C_)
            ln = _dist(P[i], P[j])
            perimeter += ln
            nm = N[i] + N[j]
            sides_info[nm] = {'eq': eq, 'coef': coef, 'len': ln}
            steps.append(f"   ▸ {nm}:  вектор {nm}⃗ = {_vec([b - a for a, b in zip(P[i], P[j])])}")
            steps.append(f"        общее:  {eq}")
            steps.append(f"        с угл. коэффициентом:  {_slope_form(*coef)}")
            steps.append(f"        длина:  |{nm}| = {fmt_num(ln)}")
        steps += _box([f"{k}:  {v['eq']},   |{k}| = {_s(v['len'])}" for k, v in sides_info.items()], "answer")
        steps.append(f"   Периметр P = {fmt_num(_simp(perimeter))}")

        def opp(vi):
            others = [k for k in range(3) if k != vi]
            return others[0], others[1]

        # --- б) медиана ---
        mv = N.index(med_v)
        p1, p2 = opp(mv)
        Mm = tuple(_simp((a + b) / 2) for a, b in zip(P[p1], P[p2]))
        mA, mB, mC = _line_through(P[mv], Mm)
        m_eq, m_coef = _line_eq(mA, mB, mC)
        m_len = _dist(P[mv], Mm)
        steps += [
            "",
            f"⚙️ б) МЕДИАНА {N[mv]}M (M — середина стороны {N[p1]}{N[p2]})",
            f"   M = (({_s(P[p1][0])} + {_s(P[p2][0])})/2; ({_s(P[p1][1])} + {_s(P[p2][1])})/2) = M{_pt(Mm)}",
            f"   Прямая через {N[mv]}{_pt(P[mv])} и M{_pt(Mm)}:",
            f"   |{N[mv]}M| = √(({_s(Mm[0])} − ({_s(P[mv][0])}))² + ({_s(Mm[1])} − ({_s(P[mv][1])}))²) = {fmt_num(m_len)}",
        ]
        steps += _box([f"{N[mv]}M:  {m_eq},   |{N[mv]}M| = {fmt_num(m_len)}"], "answer")
        plot['points'].append((_num(Mm[0]), _num(Mm[1]), "M", COL_GREEN))
        plot['segments'].append(((_num(P[mv][0]), _num(P[mv][1])), (_num(Mm[0]), _num(Mm[1])), f"медиана {N[mv]}M", COL_GREEN, '-'))

        # --- в) высота ---
        hv = N.index(alt_v)
        q1, q2 = opp(hv)
        sA, sB, sC = _line_through(P[q1], P[q2])
        nrm2 = _simp(sA ** 2 + sB ** 2)
        val = _simp(sA * P[hv][0] + sB * P[hv][1] + sC)
        tproj = _simp(-val / nrm2)
        Hf = (_simp(P[hv][0] + tproj * sA), _simp(P[hv][1] + tproj * sB))
        # высота: направляющий вектор = нормаль стороны (sA, sB)
        hA, hB = sB, -sA
        hC = -(hA * P[hv][0] + hB * P[hv][1])
        h_eq, _ = _line_eq(hA, hB, hC)
        h_len = _simp(sp.Abs(val) / sp.sqrt(nrm2))
        side_eq = sides_info.get(N[q1] + N[q2], {}).get('eq')
        steps += [
            "",
            f"⚙️ в) ВЫСОТА {N[hv]}H (на сторону {N[q1]}{N[q2]})",
            f"   Сторона {N[q1]}{N[q2]}:  {side_eq};  её нормаль n⃗ = ({_s(sA)}; {_s(sB)}) — направляющий вектор высоты.",
            f"   Высота через {N[hv]}{_pt(P[hv])} параллельно n⃗: ({_s(sB)})·(x − {_s(P[hv][0])}) − ({_s(sA)})·(y − {_s(P[hv][1])}) = 0",
            f"   Длина |{N[hv]}H| = |{_s(sA)}·({_s(P[hv][0])}) + {_s(sB)}·({_s(P[hv][1])}) + {_s(sC)}| / √({_s(sA)}² + {_s(sB)}²) = {fmt_num(h_len)}",
            f"   Основание высоты H{_pt_full(Hf)}",
        ]
        steps += _box([f"{N[hv]}H:  {h_eq},   |{N[hv]}H| = {fmt_num(h_len)}"], "answer")
        plot['points'].append((_num(Hf[0]), _num(Hf[1]), "H", COL_RED))
        plot['segments'].append(((_num(P[hv][0]), _num(P[hv][1])), (_num(Hf[0]), _num(Hf[1])), f"высота {N[hv]}H", COL_RED, '-'))
        plot['lines'].append((_num(P[q1][0]), _num(P[q1][1]), _num(P[q2][0] - P[q1][0]), _num(P[q2][1] - P[q1][1]), "", COL_GRAY))

        # --- г) угол ---
        av = N.index(ang_v)
        r1, r2 = opp(av)
        u = tuple(b - a for a, b in zip(P[av], P[r1]))
        v = tuple(b - a for a, b in zip(P[av], P[r2]))
        lu, lv = _simp(sp.sqrt(u[0] ** 2 + u[1] ** 2)), _simp(sp.sqrt(v[0] ** 2 + v[1] ** 2))
        dot = _simp(u[0] * v[0] + u[1] * v[1])
        cosv = _simp(dot / (lu * lv))
        ang = _num(sp.acos(cosv)) * 180 / np.pi
        kind = "острый" if _sgn(dot) > 0 else ("тупой" if _sgn(dot) < 0 else "прямой")
        steps += [
            "",
            f"⚙️ г) ВНУТРЕННИЙ УГОЛ {N[av]}",
            f"   u⃗ = {N[av]}{N[r1]}⃗ = {_vec(u)},   v⃗ = {N[av]}{N[r2]}⃗ = {_vec(v)}",
            f"   u⃗·v⃗ = {_s(dot)},   |u⃗| = {_s(lu)},   |v⃗| = {_s(lv)}",
            f"   cos {N[av]} = {_s(dot)} / ({_s(lu)}·{_s(lv)}) = {fmt_num(cosv)}",
        ]
        steps += _box([f"cos {N[av]} = {_s(cosv)},   ∠{N[av]} ≈ {ang:.2f}°  ({kind})"], "answer")

        # --- д) биссектриса ---
        L = tuple(_simp((lv * a + lu * b) / (lu + lv)) for a, b in zip(P[r1], P[r2]))
        bA, bB, bC = _line_through(P[av], L)
        b_eq, _ = _line_eq(bA, bB, bC)
        b_len = _dist(P[av], L)
        steps += [
            "",
            f"⚙️ д) БИССЕКТРИСА УГЛА {N[av]}",
            f"   Биссектриса делит сторону {N[r1]}{N[r2]} в отношении {N[r1]}L : L{N[r2]} = |{N[av]}{N[r1]}| : |{N[av]}{N[r2]}| = {_s(lu)} : {_s(lv)}",
            f"   L = (|{N[av]}{N[r2]}|·{N[r1]} + |{N[av]}{N[r1]}|·{N[r2]}) / (|{N[av]}{N[r1]}| + |{N[av]}{N[r2]}|) = L{_pt_full(L)}",
            f"   Биссектриса — прямая {N[av]}L.",
        ]
        steps += _box([f"биссектриса {N[av]}L:  {b_eq},   |{N[av]}L| = {fmt_num(b_len)}"], "answer")
        plot['points'].append((_num(L[0]), _num(L[1]), "L", COL_AMBER))
        plot['segments'].append(((_num(P[av][0]), _num(P[av][1])), (_num(L[0]), _num(L[1])), f"биссектриса {N[av]}L", COL_AMBER, '-'))

        return {'area': area, 'steps': "\n".join(steps), 'plot2d': plot,
                'median_eq': m_eq, 'altitude_eq': h_eq, 'bisector_eq': b_eq, 'angle_deg': ang, 'cos_angle': cosv}


# ----------------------------------------------------------------------------
# Задача 8. Прямая и точка на плоскости
# ----------------------------------------------------------------------------

class PlaneLineSolver:
    """Прямая l: Ax + By + C = 0 и точка M: параллельная, перпендикуляр, проекция, расстояние, симметрия."""

    @staticmethod
    def solve(A, B, C, pM) -> Dict[str, Any]:
        A, B, C = parse_number(A), parse_number(B), parse_number(C)
        M = _parse_pt(pM)
        if _sgn(A) == 0 and _sgn(B) == 0:
            raise ValueError("Коэффициенты A и B не могут одновременно равняться нулю")

        nrm2 = _simp(A ** 2 + B ** 2)
        val = _simp(A * M[0] + B * M[1] + C)
        # а) параллельная
        Cp = _simp(-(A * M[0] + B * M[1]))
        par_eq, _ = _line_eq(A, B, Cp)
        # б) перпендикуляр: направляющий вектор = n = (A, B)
        Bp, Ap = A, -B
        Cperp = _simp(-(Ap * M[0] + Bp * M[1]))
        # Ap*x + Bp*y + Cperp = 0  ->  B(x−xM) − A(y−yM)... записываем -B x + A y; нормируем
        perp_eq, _ = _line_eq(B, -A, _simp(-(B * M[0] - A * M[1])))
        # в) проекция
        t = _simp(-val / nrm2)
        H = (_simp(M[0] + t * A), _simp(M[1] + t * B))
        d = _simp(sp.Abs(val) / sp.sqrt(nrm2))
        # г) симметрия
        Ms = (_simp(2 * H[0] - M[0]), _simp(2 * H[1] - M[1]))
        l_eq, _ = _line_eq(A, B, C)

        steps = ["📌 ЭТАП 1. ТЕОРЕТИЧЕСКИЕ ФОРМУЛЫ"]
        steps += _box([
            "Параллельная прямая:  тот же вектор нормали n⃗ = (A; B)",
            "Перпендикуляр:  направляющий вектор прямой = n⃗, т.е. B·(x − x₀) − A·(y − y₀) = 0",
            "Расстояние:  d = |A·x₀ + B·y₀ + C| / √(A² + B²)",
            "Проекция:  H = M − (A·x₀ + B·y₀ + C)/(A² + B²) · n⃗,    M' = 2H − M",
        ])
        steps += [
            "",
            "📝 ЭТАП 2. ИСХОДНЫЕ ДАННЫЕ",
            f"   ▸ l: {l_eq},   n⃗ = ({_s(A)}; {_s(B)}),   M{_pt(M)}",
            f"   ▸ A·x₀ + B·y₀ + C = {_s(A)}·({_s(M[0])}) + {_s(B)}·({_s(M[1])}) + {_s(C)} = {_s(val)}",
            "",
            "⚙️ а) ПРЯМАЯ ЧЕРЕЗ M ПАРАЛЛЕЛЬНО l",
            f"   Вектор нормали сохраняется: {_s(A)}·(x − {_s(M[0])}) + {_s(B)}·(y − {_s(M[1])}) = 0",
        ]
        steps += _box([par_eq], "answer")
        steps += [
            "",
            "⚙️ б) ПРЯМАЯ ЧЕРЕЗ M ПЕРПЕНДИКУЛЯРНО l",
            f"   Направляющий вектор s⃗ = n⃗ = ({_s(A)}; {_s(B)}):   ({_s(B)})·(x − {_s(M[0])}) − ({_s(A)})·(y − {_s(M[1])}) = 0",
        ]
        steps += _box([perp_eq], "answer")
        steps += [
            "",
            "⚙️ в) ПРОЕКЦИЯ H ТОЧКИ M НА l И РАССТОЯНИЕ",
            f"   t = −({_s(val)}) / ({_s(A)}² + {_s(B)}²) = {_s(t)}",
            f"   H = M + t·n⃗ = ({_s(M[0])} + ({_s(t)})·({_s(A)}); {_s(M[1])} + ({_s(t)})·({_s(B)}))",
            f"   d = |{_s(val)}| / √{_s(nrm2)} = {fmt_num(d)}",
        ]
        steps += _box([f"H{_pt_full(H)},   d = {fmt_num(d)}"], "answer")
        if _sgn(val) == 0:
            steps.append("   Точка M лежит на прямой l (d = 0), поэтому H = M и M' = M.")
        steps += [
            "",
            "⚙️ г) ТОЧКА M', СИММЕТРИЧНАЯ M ОТНОСИТЕЛЬНО l",
            "   H — середина отрезка MM'   ⟹   M' = 2H − M",
            f"   M' = (2·({_s(H[0])}) − ({_s(M[0])}); 2·({_s(H[1])}) − ({_s(M[1])}))",
        ]
        steps += _box([f"M'{_pt_full(Ms)}"], "answer")

        plot = _new_plot()
        plot['title'] = "Прямая l, точка M и её проекция"
        plot['lines'].append((_num(H[0]), _num(H[1]), _num(-B), _num(A), f"l: {l_eq}", COL_MAIN))
        plot['lines'].append((_num(M[0]), _num(M[1]), _num(-B), _num(A), "∥ l", COL_GREEN))
        plot['lines'].append((_num(M[0]), _num(M[1]), _num(A), _num(B), "⊥ l", COL_AMBER))
        for nm, p, col in (("M", M, COL_RED), ("H", H, COL_GREEN), ("M'", Ms, COL_PINK)):
            plot['points'].append((_num(p[0]), _num(p[1]), nm, col))
        plot['segments'].append(((_num(M[0]), _num(M[1])), (_num(Ms[0]), _num(Ms[1])), "", COL_RED, '--'))
        return {'parallel': par_eq, 'perpendicular': perp_eq, 'H': H, 'distance': d, 'symmetric': Ms,
                'steps': "\n".join(steps), 'plot2d': plot}


# ----------------------------------------------------------------------------
# Задача 9. Кривые второго порядка
# ----------------------------------------------------------------------------

def _poly_str(a, b, c, d, e, f, vx="x", vy="y") -> str:
    terms = [(a, f"{vx}²"), (b, f"{vx}{vy}"), (c, f"{vy}²"), (d, vx), (e, vy), (f, "")]
    out = ""
    for coef, mon in terms:
        coef = _simp(coef)
        if _sgn(coef) == 0:
            continue
        sign = "-" if _sgn(coef) < 0 else "+"
        ac = _simp(abs(coef)) if coef.is_number and _sgn(coef) < 0 else coef
        cs = _s(ac)
        if mon and cs == "1":
            body = mon
        elif mon:
            body = f"{cs}{mon}" if coef.is_Rational or coef.is_Integer else f"({cs}){mon}"
        else:
            body = cs
        if not out:
            out = ("-" if sign == "-" else "") + body
        else:
            out += f" {sign} {body}"
    return (out or "0") + " = 0"


class ConicSolver:
    """Приведение уравнения кривой второго порядка к каноническому виду."""

    @staticmethod
    def solve(a, b, c, d, e, f) -> Dict[str, Any]:
        a, b, c, d, e, f = [parse_number(v) for v in (a, b, c, d, e, f)]
        if _sgn(a) == 0 and _sgn(b) == 0 and _sgn(c) == 0:
            raise ValueError("Коэффициенты при x², xy, y² нулевые — это не кривая второго порядка")

        delta = _simp(a * c - b ** 2 / 4)
        steps = ["📌 ЭТАП 1. ТЕОРЕТИЧЕСКАЯ СПРАВКА"]
        steps += _box([
            "Общий вид:  A·x² + B·xy + C·y² + D·x + E·y + F = 0",
            "Инвариант δ = A·C − B²/4:  δ > 0 — эллипс,  δ < 0 — гипербола,  δ = 0 — парабола",
            "Если B ≠ 0 — поворот осей: x = x'·cosθ − y'·sinθ,  y = x'·sinθ + y'·cosθ,  tg 2θ = B/(A − C)",
            "Затем — выделение полных квадратов (параллельный перенос начала координат).",
        ])
        steps += [
            "",
            "📝 ЭТАП 2. ИСХОДНОЕ УРАВНЕНИЕ И ТИП",
            f"   {_poly_str(a, b, c, d, e, f)}",
            f"   δ = {_s(a)}·({_s(c)}) − ({_s(b)})²/4 = {_s(delta)}",
        ]
        dsgn = _sgn(delta)
        steps.append("   δ " + (">" if dsgn > 0 else "<" if dsgn < 0 else "=") + " 0  ⟹  тип по инварианту: " +
                     ("эллиптический" if dsgn > 0 else "гиперболический" if dsgn < 0 else "параболический"))

        # ---- поворот осей ----
        cosT, sinT = sp.Integer(1), sp.Integer(0)
        a2, c2, d2, e2 = a, c, d, e
        theta_deg = 0.0
        if _sgn(b) != 0:
            R = _simp(sp.sqrt((a - c) ** 2 + b ** 2))
            cos2 = _simp((a - c) / R)
            cosT = _simp(sp.sqrt(_simp((1 + cos2) / 2)))
            sinT = _simp(_sgn(b) * sp.sqrt(_simp((1 - cos2) / 2)))
            a2 = _simp(a * cosT ** 2 + b * cosT * sinT + c * sinT ** 2)
            c2 = _simp(a * sinT ** 2 - b * cosT * sinT + c * cosT ** 2)
            d2 = _simp(d * cosT + e * sinT)
            e2 = _simp(-d * sinT + e * cosT)
            theta_deg = float(np.degrees(np.arctan2(_num(sinT), _num(cosT))))
            steps += [
                "",
                "⚙️ ЭТАП 3. ПОВОРОТ ОСЕЙ (устранение члена с xy)",
                f"   tg 2θ = B/(A − C) = {_s(b)}/({_s(a - c)})" if _sgn(a - c) != 0 else f"   A = C  ⟹  cos 2θ = 0,  θ = 45° (знак по знаку B)",
                f"   cos 2θ = (A − C)/√((A − C)² + B²) = {_s(cos2)}",
                f"   cos θ = √((1 + cos 2θ)/2) = {_s(cosT)},   sin θ = {'+' if _sgn(b) > 0 else '−'}√((1 − cos 2θ)/2) = {_s(sinT)}",
                f"   Угол поворота θ ≈ {theta_deg:.2f}°",
                "   Подстановка в уравнение даёт коэффициенты:",
                f"     A' = A·cos²θ + B·sinθ·cosθ + C·sin²θ = {_s(a2)}",
                f"     C' = A·sin²θ − B·sinθ·cosθ + C·cos²θ = {_s(c2)}",
                f"     D' = D·cosθ + E·sinθ = {_s(d2)},    E' = −D·sinθ + E·cosθ = {_s(e2)}",
            ]
            steps += _box([_poly_str(a2, 0, c2, d2, e2, f, "x'", "y'")])
            steps.append(f"   Новые базисные векторы: e⃗₁ = ({_s(cosT)}; {_s(sinT)}),  e⃗₂ = ({_s(-sinT)}; {_s(cosT)})")
        else:
            steps += ["", "⚙️ ЭТАП 3. ПОВОРОТ ОСЕЙ", "   Член с xy отсутствует (B = 0) — поворот не нужен, оси канонического вида параллельны исходным."]

        U, V = ("x'", "y'") if _sgn(b) != 0 else ("x", "y")

        def to_world(u, v):
            return (_simp(u * cosT - v * sinT), _simp(u * sinT + v * cosT))

        def dir_world(du, dv):
            return (_num(du * cosT - dv * sinT), _num(du * sinT + dv * cosT))

        plot = _new_plot()
        info: Dict[str, Any] = {}
        steps += ["", "⚙️ ЭТАП 4. ВЫДЕЛЕНИЕ ПОЛНЫХ КВАДРАТОВ"]
        ca, cc = _sgn(a2), _sgn(c2)

        def add_pt(p_uv, name, color):
            w = to_world(*p_uv)
            plot['points'].append((_num(w[0]), _num(w[1]), name, color))
            return w

        def add_line_uv(p_uv, du, dv, label, color):
            w = to_world(*p_uv)
            dx, dy = dir_world(du, dv)
            plot['lines'].append((_num(w[0]), _num(w[1]), dx, dy, label, color))

        def frame_note(p_uv):
            if _sgn(b) == 0:
                return ""
            w = to_world(*p_uv)
            return f"  — в исходной системе: ({_s(w[0])}; {_s(w[1])})"

        result_type = ""
        canon = ""

        if ca != 0 and cc != 0:
            u0 = _simp(-d2 / (2 * a2))
            v0 = _simp(-e2 / (2 * c2))
            K = _simp(d2 ** 2 / (4 * a2) + e2 ** 2 / (4 * c2) - f)
            steps += [
                f"   {_s(a2)}·({U}² {_add(d2 / a2)}·{U}) {_add(c2)}·({V}² {_add(e2 / c2)}·{V}) {_add(f)} = 0",
                f"   {_s(a2)}·{_shift(U, u0)}² {_add(c2)}·{_shift(V, v0)}² = {_s(K)}",
                f"   Параллельный перенос: X = {U} {_add(-u0)},  Y = {V} {_add(-v0)}",
                f"   Центр O'({_s(u0)}; {_s(v0)}) в системе ({U}, {V}){frame_note((u0, v0))}",
            ]
            if ca * cc > 0:
                if _sgn(K) == 0:
                    result_type = "Вырожденный случай: единственная точка"
                    canon = f"{_s(a2)}·X² {_add(c2)}·Y² = 0"
                    add_pt((u0, v0), "O'", COL_RED)
                elif _sgn(K) * ca < 0:
                    result_type = "Мнимый эллипс (пустое множество — действительных точек нет)"
                    canon = f"{_s(a2)}·X² {_add(c2)}·Y² = {_s(K)}  (знаки левой и правой частей разные — решений нет)"
                else:
                    A2, B2 = _simp(K / a2), _simp(K / c2)
                    aa, bb = _simp(sp.sqrt(A2)), _simp(sp.sqrt(B2))
                    canon = f"X²/{_s(A2)} + Y²/{_s(B2)} = 1"
                    steps += ["   Делим на правую часть:", f"   {canon}"]
                    if _sgn(A2 - B2) == 0:
                        result_type = f"Окружность радиуса R = {_s(aa)}"
                        info.update(center=(u0, v0), R=aa)
                        steps.append(f"   a = b ⟹ окружность, центр O'({_s(u0)}; {_s(v0)}), R = {_s(aa)}")
                        add_pt((u0, v0), "O'", COL_RED)
                    else:
                        result_type = "Эллипс"
                        along_u = _sgn(A2 - B2) > 0
                        big, small = (aa, bb) if along_u else (bb, aa)
                        cf = _simp(sp.sqrt(_simp(big ** 2 - small ** 2)))
                        eps = _simp(cf / big)
                        f1 = (u0 - cf, v0) if along_u else (u0, v0 - cf)
                        f2 = (u0 + cf, v0) if along_u else (u0, v0 + cf)
                        info.update(center=(u0, v0), a=big, b=small, c=cf, e=eps)
                        steps += [
                            f"   Полуоси: a = {_s(big)} (большая), b = {_s(small)} (малая); большая полуось направлена вдоль оси {'X' if along_u else 'Y'}",
                            f"   c = √(a² − b²) = {fmt_num(cf)},   ε = c/a = {fmt_num(eps)}",
                            f"   Фокусы: F₁({_s(f1[0])}; {_s(f1[1])}),  F₂({_s(f2[0])}; {_s(f2[1])}) в системе ({U}, {V}){frame_note(f2)}",
                        ]
                        if _sgn(eps) != 0:
                            dd = _simp(big / eps)
                            steps.append(f"   Директрисы: расстояние от центра a/ε = {fmt_num(dd)} вдоль большой оси")
                            for sg in (-1, 1):
                                if along_u:
                                    add_line_uv((u0 + sg * dd, v0), 0, 1, "", COL_GRAY)
                                else:
                                    add_line_uv((u0, v0 + sg * dd), 1, 0, "", COL_GRAY)
                        add_pt((u0, v0), "O'", COL_RED)
                        add_pt(f1, "F₁", COL_AMBER)
                        add_pt(f2, "F₂", COL_AMBER)
                    ts = np.linspace(0, 2 * np.pi, 300)
                    xs_u = _num(u0) + _num(aa) * np.cos(ts)
                    xs_v = _num(v0) + _num(bb) * np.sin(ts)
                    cx_ = xs_u * _num(cosT) - xs_v * _num(sinT)
                    cy_ = xs_u * _num(sinT) + xs_v * _num(cosT)
                    plot['curves'].append((cx_, cy_, "", COL_MAIN))
            else:
                if _sgn(K) == 0:
                    result_type = "Вырожденный случай: пара пересекающихся прямых"
                    kk = _simp(sp.sqrt(_simp(-a2 / c2)))
                    canon = f"Y = ±{_s(kk)}·X"
                    steps.append(f"   Правая часть равна 0: {canon}")
                    add_line_uv((u0, v0), 1, kk, "", COL_MAIN)
                    add_line_uv((u0, v0), 1, -kk, "", COL_MAIN)
                    add_pt((u0, v0), "O'", COL_RED)
                else:
                    result_type = "Гипербола"
                    real_u = _sgn(K) * ca > 0
                    if real_u:
                        aa, bb = _simp(sp.sqrt(_simp(K / a2))), _simp(sp.sqrt(_simp(-K / c2)))
                        canon = f"X²/{_s(aa ** 2)} − Y²/{_s(bb ** 2)} = 1"
                    else:
                        aa, bb = _simp(sp.sqrt(_simp(K / c2))), _simp(sp.sqrt(_simp(-K / a2)))
                        canon = f"Y²/{_s(aa ** 2)} − X²/{_s(bb ** 2)} = 1"
                    cf = _simp(sp.sqrt(_simp(aa ** 2 + bb ** 2)))
                    eps = _simp(cf / aa)
                    f1 = (u0 - cf, v0) if real_u else (u0, v0 - cf)
                    f2 = (u0 + cf, v0) if real_u else (u0, v0 + cf)
                    info.update(center=(u0, v0), a=aa, b=bb, c=cf, e=eps)
                    steps += [
                        "   Делим на правую часть:", f"   {canon}",
                        f"   Действительная полуось a = {_s(aa)} (вдоль оси {'X' if real_u else 'Y'}), мнимая b = {_s(bb)}",
                        f"   c = √(a² + b²) = {fmt_num(cf)},   ε = c/a = {fmt_num(eps)}",
                        f"   Фокусы: F₁({_s(f1[0])}; {_s(f1[1])}),  F₂({_s(f2[0])}; {_s(f2[1])}) в системе ({U}, {V}){frame_note(f2)}",
                    ]
                    if real_u:
                        sl = _simp(bb / aa)
                        steps.append(f"   Асимптоты: Y = ±{_s(sl)}·X   (то есть {V} {_add(-v0)} = ±{_s(sl)}·{_shift(U, u0)})")
                        dirs = [(1, sl), (1, -sl)]
                    else:
                        sl = _simp(aa / bb)
                        steps.append(f"   Асимптоты: Y = ±{_s(sl)}·X   (то есть {V} {_add(-v0)} = ±{_s(sl)}·{_shift(U, u0)})")
                        dirs = [(1, sl), (1, -sl)]
                    dd = _simp(aa / eps)
                    steps.append(f"   Директрисы: расстояние от центра a/ε = {fmt_num(dd)} вдоль действительной оси")
                    for i_dr, dr in enumerate(dirs):
                        add_line_uv((u0, v0), dr[0], dr[1], "асимптоты" if i_dr == 0 else "", COL_GRAY)
                    for sg in (-1, 1):
                        if real_u:
                            add_line_uv((u0 + sg * dd, v0), 0, 1, "", COL_PINK)
                        else:
                            add_line_uv((u0, v0 + sg * dd), 1, 0, "", COL_PINK)
                    add_pt((u0, v0), "O'", COL_RED)
                    add_pt(f1, "F₁", COL_AMBER)
                    add_pt(f2, "F₂", COL_AMBER)
                    ss = np.linspace(-2.6, 2.6, 300)
                    for sg in (-1, 1):
                        if real_u:
                            pu = _num(u0) + sg * _num(aa) * np.cosh(ss)
                            pv = _num(v0) + _num(bb) * np.sinh(ss)
                        else:
                            pv = _num(v0) + sg * _num(aa) * np.cosh(ss)
                            pu = _num(u0) + _num(bb) * np.sinh(ss)
                        plot['curves'].append((pu * _num(cosT) - pv * _num(sinT), pu * _num(sinT) + pv * _num(cosT), "", COL_MAIN))
        elif ca == 0 and cc == 0:
            raise ValueError("После поворота оба коэффициента при квадратах нулевые — уравнение линейное, кривой 2-го порядка нет")
        else:
            # Парабола (a2 или c2 равен нулю)
            swap = (ca == 0)  # (v - v0)^2 = 2p (u - u0)
            if not swap:
                qq, lin_q, lin_o = a2, d2, e2  # q·u² + lin_q·u + lin_o·v + f = 0
                nq, no = U, V
            else:
                qq, lin_q, lin_o = c2, e2, d2
                nq, no = V, U
            q0 = _simp(-lin_q / (2 * qq))
            steps.append(f"   Уравнение содержит только {nq}²: {_s(qq)}·{nq}² {_add(lin_q)}·{nq} {_add(lin_o)}·{no} {_add(f)} = 0")
            if _sgn(lin_o) == 0:
                disc = _simp(lin_q ** 2 - 4 * qq * f)
                steps.append(f"   Коэффициент при {no} равен 0: квадратное уравнение относительно {nq}, D = {_s(disc)}")
                if _sgn(disc) > 0:
                    r1 = _simp((-lin_q - sp.sqrt(disc)) / (2 * qq))
                    r2 = _simp((-lin_q + sp.sqrt(disc)) / (2 * qq))
                    result_type = "Вырожденный случай: пара параллельных прямых"
                    canon = f"{nq} = {_s(r1)},  {nq} = {_s(r2)}"
                    for r in (r1, r2):
                        if not swap:
                            add_line_uv((r, 0), 0, 1, "", COL_MAIN)
                        else:
                            add_line_uv((0, r), 1, 0, "", COL_MAIN)
                elif _sgn(disc) == 0:
                    result_type = "Вырожденный случай: двойная прямая (две совпавшие прямые)"
                    canon = f"{nq} = {_s(q0)}"
                    if not swap:
                        add_line_uv((q0, 0), 0, 1, "", COL_MAIN)
                    else:
                        add_line_uv((0, q0), 1, 0, "", COL_MAIN)
                else:
                    result_type = "Мнимые параллельные прямые (действительных точек нет)"
                    canon = f"{nq} = {_s(q0)} ± i·√{_s(-disc / (4 * qq ** 2))}"
            else:
                o0 = _simp((lin_q ** 2 / (4 * qq) - f) / lin_o)
                pt_ = _simp(-lin_o / (2 * qq))  # (nq - q0)^2 = 2·pt·(no - o0)
                p_abs = _simp(abs(pt_))
                steps += [
                    f"   {_s(qq)}·{_shift(nq, q0)}² = {_s(-lin_o)}·{_shift(no, o0)}",
                    f"   Параллельный перенос: вершина O'({nq} = {_s(q0)}, {no} = {_s(o0)})",
                ]
                nqX, noY = ("X", "Y") if not swap else ("Y", "X")
                # каноническое: (nq')² = 2p (no') ; запись в виде y² = 2px
                canon = f"{nqX}² = {_s(2 * pt_)}·{noY}"
                result_type = "Парабола"
                steps += [
                    f"   Каноническое уравнение:  {canon}   (вида {'x² = 2py' if not swap else 'y² = 2px'})",
                    f"   Параметр параболы p = {_s(p_abs)}  (расстояние от фокуса до директрисы)",
                ]
                if not swap:
                    vertex = (q0, o0)
                    focus = (q0, o0 + pt_ / 2)
                    dir_c = ("y", o0 - pt_ / 2)
                else:
                    vertex = (o0, q0)
                    focus = (o0 + pt_ / 2, q0)
                    dir_c = ("x", o0 - pt_ / 2)
                steps += [
                    f"   Вершина: ({_s(vertex[0])}; {_s(vertex[1])}),   фокус F({_s(focus[0])}; {_s(focus[1])}) в системе ({U}, {V}){frame_note(focus)}",
                    f"   Директриса: {no} = {_s(dir_c[1])} (в системе ({U}, {V}))",
                    f"   Ось симметрии параллельна оси {'Oy' if not swap else 'Ox'} (в системе {U}{V}), ветви направлены {'вверх' if (not swap and _sgn(pt_) > 0) else 'вниз' if not swap else 'вправо' if _sgn(pt_) > 0 else 'влево'}",
                    "   Эксцентриситет ε = 1",
                ]
                info.update(vertex=vertex, p=p_abs, focus=focus)
                add_pt(vertex, "вершина", COL_RED)
                add_pt(focus, "F", COL_AMBER)
                if not swap:
                    add_line_uv((0, dir_c[1]), 1, 0, "директриса", COL_PINK)
                else:
                    add_line_uv((dir_c[1], 0), 0, 1, "директриса", COL_PINK)
                span = 4 * max(1.0, _num(p_abs))
                ss = np.linspace(-span, span, 300)
                if not swap:
                    pu = _num(q0) + ss
                    pv = _num(o0) + ss ** 2 / (2 * _num(pt_))
                else:
                    pv = _num(q0) + ss
                    pu = _num(o0) + ss ** 2 / (2 * _num(pt_))
                plot['curves'].append((pu * _num(cosT) - pv * _num(sinT), pu * _num(sinT) + pv * _num(cosT), "", COL_MAIN))

        steps += ["", "🎯 ИТОГ"]
        ans = [f"Тип кривой: {result_type}", f"Канонический вид: {canon}"]
        if _sgn(b) != 0:
            ans.append(f"Угол поворота θ ≈ {theta_deg:.2f}°,  cosθ = {_s(cosT)},  sinθ = {_s(sinT)}")
        if 'center' in info:
            w = to_world(*info['center'])
            ans.append(f"Центр: ({_s(w[0])}; {_s(w[1])}) в исходной системе")
        for k, nm in (('a', 'a'), ('b', 'b'), ('c', 'c'), ('e', 'ε')):
            if k in info:
                ans.append(f"{nm} = {fmt_num(info[k])}")
        if 'vertex' in info:
            w = to_world(*info['vertex'])
            wf = to_world(*info['focus'])
            ans.append(f"Вершина: ({_s(w[0])}; {_s(w[1])}),  фокус: ({_s(wf[0])}; {_s(wf[1])}) в исходной системе,  p = {_s(info['p'])}")
        steps += _box(ans, "answer")

        plot['title'] = result_type
        plot['equal'] = True
        return {'type': result_type, 'canonical': canon, 'theta_deg': theta_deg, 'info': info,
                'steps': "\n".join(steps), 'plot2d': plot}


# ----------------------------------------------------------------------------
# Задача 10. Комплексная задача в пространстве
# ----------------------------------------------------------------------------

class SpaceTaskSolver:
    """Плоскость ABC, прямая AD, перпендикуляр DH, параллельная плоскость, прямая l (общий вид)."""

    @staticmethod
    def solve(pA, pB, pC, pD, pl1, pl2) -> Dict[str, Any]:
        A, B, C, D = [_parse_pt(p, 3) for p in (pA, pB, pC, pD)]

        def banner(txt):
            return ["", f"📐 {txt}", ""]

        steps: List[str] = []

        # а) плоскость ABC
        plane = PlaneSolver.by_three_points(A, B, C)
        a_, b_, c_, d_ = plane['A'], plane['B'], plane['C'], plane['D']
        steps += banner("а) ОБЩЕЕ УРАВНЕНИЕ ПЛОСКОСТИ ABC И УРАВНЕНИЕ В ОТРЕЗКАХ")
        steps.append(plane['steps'])
        steps += ["", "⚙️ Уравнение в отрезках:  x/a + y/b + z/c = 1"]
        if all(_sgn(v) != 0 for v in (a_, b_, c_, d_)):
            ia, ib, ic = _simp(-d_ / a_), _simp(-d_ / b_), _simp(-d_ / c_)
            seg_eq = f"x/({_s(ia)}) + y/({_s(ib)}) + z/({_s(ic)}) = 1"
            steps += [f"   Переносим D вправо и делим на −D:  a = −D/A = {_s(ia)},  b = −D/B = {_s(ib)},  c = −D/C = {_s(ic)}"]
            steps += _box([seg_eq], "answer")
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
        steps += ["⚙️ Направляющий вектор перпендикуляра = вектор нормали плоскости n⃗ = " + _vec(nrm)]
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
