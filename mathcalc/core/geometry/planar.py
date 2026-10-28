"""
Аналитическая геометрия на плоскости: деление отрезка, треугольник, прямая и точка.
"""

from typing import Any, Dict

import numpy as np
import sympy as sp

from ..common import (
    parse_number, fmt_num, simp, sgn, ex, pt_str, pt_full, vec_str, dist, num, box,
    line_eq, slope_form, line_through, parse_point, new_scene2d,
    COL_MAIN, COL_RED, COL_GREEN, COL_AMBER, COL_PINK, COL_GRAY,
)


# ----------------------------------------------------------------------------
# Деление отрезка в отношении, середина, центр масс
# ----------------------------------------------------------------------------

class SegmentSolver:
    """Деление отрезка в отношении λ, симметричная точка, пересечение медиан."""

    @staticmethod
    def solve(pA, pB, pK, m, n) -> Dict[str, Any]:
        A, B, K = parse_point(pA), parse_point(pB), parse_point(pK)
        m, n = parse_number(m), parse_number(n)
        if sgn(m + n) == 0:
            raise ValueError("Сумма m + n равна нулю: точка деления не существует (отрезок делится «в бесконечности»)")
        if sgn(m) == 0 and sgn(n) == 0:
            raise ValueError("Отношение m : n не может быть 0 : 0")

        lam = simp(m / n) if sgn(n) != 0 else None
        # AC : CB = m : n  =>  C = (n·A + m·B) / (m + n)
        C = tuple(simp((n * a + m * b) / (m + n)) for a, b in zip(A, B))
        D = tuple(simp(2 * b - a) for a, b in zip(A, B))
        G = tuple(simp((a + b + k) / 3) for a, b, k in zip(A, B, K))
        Mid = tuple(simp((a + b) / 2) for a, b in zip(A, B))
        MidBK = tuple(simp((b + k) / 2) for b, k in zip(B, K))

        steps = [
            "📌 ЭТАП 1. ТЕОРЕТИЧЕСКИЕ ФОРМУЛЫ",
            "Деление отрезка в отношении λ = m : n (AC : CB = m : n):",
        ]
        steps += box([
            "x_C = (n·x_A + m·x_B) / (m + n),   y_C = (n·y_A + m·y_B) / (m + n)",
            "Середина отрезка: x_M = (x_A + x_B)/2,   y_M = (y_A + y_B)/2",
            "Центр масс (пересечение медиан): x_G = (x_A + x_B + x_K)/3",
        ])
        steps += [
            "",
            "📝 ЭТАП 2. ИСХОДНЫЕ ДАННЫЕ",
            f"   ▸ A{pt_str(A)},  B{pt_str(B)},  K{pt_str(K)}",
            f"   ▸ Отношение AC : CB = {ex(m)} : {ex(n)}",
            "",
            f"⚙️ а) ТОЧКА C, ДЕЛЯЩАЯ ОТРЕЗОК AB В ОТНОШЕНИИ {ex(m)} : {ex(n)}",
            f"   x_C = ({ex(n)}·({ex(A[0])}) + {ex(m)}·({ex(B[0])})) / ({ex(m)} + {ex(n)}) = {ex(C[0])}",
            f"   y_C = ({ex(n)}·({ex(A[1])}) + {ex(m)}·({ex(B[1])})) / ({ex(m)} + {ex(n)}) = {ex(C[1])}",
        ]
        if lam is not None and sgn(lam) < 0:
            steps.append("   (отношение отрицательное — точка C лежит на продолжении отрезка AB, деление внешнее)")
        steps += box([f"C{pt_str(C)}"], "answer")
        steps += [
            "",
            "⚙️ б) ТОЧКА D, ЕСЛИ B — СЕРЕДИНА ОТРЕЗКА AD",
            "   B = (A + D)/2   ⟹   D = 2B − A",
            f"   x_D = 2·({ex(B[0])}) − ({ex(A[0])}) = {ex(D[0])}",
            f"   y_D = 2·({ex(B[1])}) − ({ex(A[1])}) = {ex(D[1])}",
        ]
        steps += box([f"D{pt_str(D)}"], "answer")
        steps += [
            "",
            "⚙️ в) ТОЧКА ПЕРЕСЕЧЕНИЯ МЕДИАН ТРЕУГОЛЬНИКА ABK",
            f"   x_G = ({ex(A[0])} + {ex(B[0])} + {ex(K[0])}) / 3 = {ex(G[0])}",
            f"   y_G = ({ex(A[1])} + {ex(B[1])} + {ex(K[1])}) / 3 = {ex(G[1])}",
            f"   Проверка: G делит медиану K→M (M{pt_str(Mid)} — середина AB) в отношении 2 : 1 от вершины.",
        ]
        steps += box([f"G{pt_str(G)}"], "answer")

        plot = new_scene2d()
        plot['title'] = "Деление отрезка и центр масс"
        for nm, p, col in (("A", A, COL_MAIN), ("B", B, COL_MAIN), ("K", K, COL_MAIN),
                           ("C", C, COL_RED), ("D", D, COL_AMBER), ("G", G, COL_GREEN)):
            plot['points'].append((num(p[0]), num(p[1]), nm, col))
        plot['segments'] += [
            ((num(A[0]), num(A[1])), (num(B[0]), num(B[1])), "", COL_MAIN, '-'),
            ((num(B[0]), num(B[1])), (num(K[0]), num(K[1])), "", COL_MAIN, '-'),
            ((num(K[0]), num(K[1])), (num(A[0]), num(A[1])), "", COL_MAIN, '-'),
            ((num(B[0]), num(B[1])), (num(D[0]), num(D[1])), "AD", COL_AMBER, '--'),
            ((num(K[0]), num(K[1])), (num(Mid[0]), num(Mid[1])), "", COL_GREEN, ':'),
            ((num(A[0]), num(A[1])), (num(MidBK[0]), num(MidBK[1])), "", COL_GREEN, ':'),
        ]
        return {'C': C, 'D': D, 'G': G, 'steps': "\n".join(steps), 'plot2d': plot}


# ----------------------------------------------------------------------------
# Треугольник на плоскости
# ----------------------------------------------------------------------------

class TriangleSolver:
    """Треугольник ABC на плоскости: стороны, медиана, высота, угол, биссектриса."""

    NAMES = ["A", "B", "C"]

    @staticmethod
    def solve(pA, pB, pC, med_v: str = "A", alt_v: str = "B", ang_v: str = "A") -> Dict[str, Any]:
        P = [parse_point(pA), parse_point(pB), parse_point(pC)]
        N = TriangleSolver.NAMES
        area2 = simp((P[1][0] - P[0][0]) * (P[2][1] - P[0][1]) - (P[2][0] - P[0][0]) * (P[1][1] - P[0][1]))
        if sgn(area2) == 0:
            raise ValueError("Точки A, B, C лежат на одной прямой — треугольник вырожден")
        area = simp(sp.Abs(area2) / 2)

        steps = [
            "📌 ЭТАП 1. ТЕОРЕТИЧЕСКИЕ ФОРМУЛЫ",
        ]
        steps += box([
            "Прямая через две точки:  (x − x₁)/(x₂ − x₁) = (y − y₁)/(y₂ − y₁)",
            "Длина стороны:  |PQ| = √((x₂ − x₁)² + (y₂ − y₁)²)",
            "Угол при вершине:  cos∠ = (u⃗·v⃗) / (|u⃗|·|v⃗|)",
            "Расстояние от точки до прямой:  d = |A·x₀ + B·y₀ + C| / √(A² + B²)",
            "Биссектриса делит противоположную сторону в отношении |VP| : |VQ|",
        ])
        steps += ["", f"📝 ЭТАП 2. ВЕРШИНЫ:  A{pt_str(P[0])},  B{pt_str(P[1])},  C{pt_str(P[2])}",
                  f"   ▸ Площадь S = ½·|(B−A)×(C−A)| = {fmt_num(area)}", ""]

        plot = new_scene2d()
        plot['title'] = "Треугольник ABC"
        for i in range(3):
            plot['points'].append((num(P[i][0]), num(P[i][1]), N[i], COL_MAIN))
            j = (i + 1) % 3
            plot['segments'].append(((num(P[i][0]), num(P[i][1])), (num(P[j][0]), num(P[j][1])), "", COL_MAIN, '-'))

        # --- а) стороны ---
        steps.append("⚙️ а) УРАВНЕНИЯ И ДЛИНЫ СТОРОН")
        sides_info = {}
        perimeter = 0
        for (i, j) in ((0, 1), (0, 2), (1, 2)):
            A_, B_, C_ = line_through(P[i], P[j])
            eq, coef = line_eq(A_, B_, C_)
            ln = dist(P[i], P[j])
            perimeter += ln
            nm = N[i] + N[j]
            sides_info[nm] = {'eq': eq, 'coef': coef, 'len': ln}
            steps.append(f"   ▸ {nm}:  вектор {nm}⃗ = {vec_str([b - a for a, b in zip(P[i], P[j])])}")
            steps.append(f"        общее:  {eq}")
            steps.append(f"        с угл. коэффициентом:  {slope_form(*coef)}")
            steps.append(f"        длина:  |{nm}| = {fmt_num(ln)}")
        steps += box([f"{k}:  {v['eq']},   |{k}| = {ex(v['len'])}" for k, v in sides_info.items()], "answer")
        steps.append(f"   Периметр P = {fmt_num(simp(perimeter))}")

        def opp(vi):
            others = [k for k in range(3) if k != vi]
            return others[0], others[1]

        # --- б) медиана ---
        mv = N.index(med_v)
        p1, p2 = opp(mv)
        Mm = tuple(simp((a + b) / 2) for a, b in zip(P[p1], P[p2]))
        mA, mB, mC = line_through(P[mv], Mm)
        m_eq, m_coef = line_eq(mA, mB, mC)
        m_len = dist(P[mv], Mm)
        steps += [
            "",
            f"⚙️ б) МЕДИАНА {N[mv]}M (M — середина стороны {N[p1]}{N[p2]})",
            f"   M = (({ex(P[p1][0])} + {ex(P[p2][0])})/2; ({ex(P[p1][1])} + {ex(P[p2][1])})/2) = M{pt_str(Mm)}",
            f"   Прямая через {N[mv]}{pt_str(P[mv])} и M{pt_str(Mm)}:",
            f"   |{N[mv]}M| = √(({ex(Mm[0])} − ({ex(P[mv][0])}))² + ({ex(Mm[1])} − ({ex(P[mv][1])}))²) = {fmt_num(m_len)}",
        ]
        steps += box([f"{N[mv]}M:  {m_eq},   |{N[mv]}M| = {fmt_num(m_len)}"], "answer")
        plot['points'].append((num(Mm[0]), num(Mm[1]), "M", COL_GREEN))
        plot['segments'].append(((num(P[mv][0]), num(P[mv][1])), (num(Mm[0]), num(Mm[1])), f"медиана {N[mv]}M", COL_GREEN, '-'))

        # --- в) высота ---
        hv = N.index(alt_v)
        q1, q2 = opp(hv)
        sA, sB, sC = line_through(P[q1], P[q2])
        nrm2 = simp(sA ** 2 + sB ** 2)
        val = simp(sA * P[hv][0] + sB * P[hv][1] + sC)
        tproj = simp(-val / nrm2)
        Hf = (simp(P[hv][0] + tproj * sA), simp(P[hv][1] + tproj * sB))
        # высота: направляющий вектор = нормаль стороны (sA, sB)
        hA, hB = sB, -sA
        hC = -(hA * P[hv][0] + hB * P[hv][1])
        h_eq, _ = line_eq(hA, hB, hC)
        h_len = simp(sp.Abs(val) / sp.sqrt(nrm2))
        side_eq = sides_info.get(N[q1] + N[q2], {}).get('eq')
        steps += [
            "",
            f"⚙️ в) ВЫСОТА {N[hv]}H (на сторону {N[q1]}{N[q2]})",
            f"   Сторона {N[q1]}{N[q2]}:  {side_eq};  её нормаль n⃗ = ({ex(sA)}; {ex(sB)}) — направляющий вектор высоты.",
            f"   Высота через {N[hv]}{pt_str(P[hv])} параллельно n⃗: ({ex(sB)})·(x − {ex(P[hv][0])}) − ({ex(sA)})·(y − {ex(P[hv][1])}) = 0",
            f"   Длина |{N[hv]}H| = |{ex(sA)}·({ex(P[hv][0])}) + {ex(sB)}·({ex(P[hv][1])}) + {ex(sC)}| / √({ex(sA)}² + {ex(sB)}²) = {fmt_num(h_len)}",
            f"   Основание высоты H{pt_full(Hf)}",
        ]
        steps += box([f"{N[hv]}H:  {h_eq},   |{N[hv]}H| = {fmt_num(h_len)}"], "answer")
        plot['points'].append((num(Hf[0]), num(Hf[1]), "H", COL_RED))
        plot['segments'].append(((num(P[hv][0]), num(P[hv][1])), (num(Hf[0]), num(Hf[1])), f"высота {N[hv]}H", COL_RED, '-'))
        plot['lines'].append((num(P[q1][0]), num(P[q1][1]), num(P[q2][0] - P[q1][0]), num(P[q2][1] - P[q1][1]), "", COL_GRAY))

        # --- г) угол ---
        av = N.index(ang_v)
        r1, r2 = opp(av)
        u = tuple(b - a for a, b in zip(P[av], P[r1]))
        v = tuple(b - a for a, b in zip(P[av], P[r2]))
        lu, lv = simp(sp.sqrt(u[0] ** 2 + u[1] ** 2)), simp(sp.sqrt(v[0] ** 2 + v[1] ** 2))
        dot = simp(u[0] * v[0] + u[1] * v[1])
        cosv = simp(dot / (lu * lv))
        ang = num(sp.acos(cosv)) * 180 / np.pi
        kind = "острый" if sgn(dot) > 0 else ("тупой" if sgn(dot) < 0 else "прямой")
        steps += [
            "",
            f"⚙️ г) ВНУТРЕННИЙ УГОЛ {N[av]}",
            f"   u⃗ = {N[av]}{N[r1]}⃗ = {vec_str(u)},   v⃗ = {N[av]}{N[r2]}⃗ = {vec_str(v)}",
            f"   u⃗·v⃗ = {ex(dot)},   |u⃗| = {ex(lu)},   |v⃗| = {ex(lv)}",
            f"   cos {N[av]} = {ex(dot)} / ({ex(lu)}·{ex(lv)}) = {fmt_num(cosv)}",
        ]
        steps += box([f"cos {N[av]} = {ex(cosv)},   ∠{N[av]} ≈ {ang:.2f}°  ({kind})"], "answer")

        # --- д) биссектриса ---
        L = tuple(simp((lv * a + lu * b) / (lu + lv)) for a, b in zip(P[r1], P[r2]))
        bA, bB, bC = line_through(P[av], L)
        b_eq, _ = line_eq(bA, bB, bC)
        b_len = dist(P[av], L)
        steps += [
            "",
            f"⚙️ д) БИССЕКТРИСА УГЛА {N[av]}",
            f"   Биссектриса делит сторону {N[r1]}{N[r2]} в отношении {N[r1]}L : L{N[r2]} = |{N[av]}{N[r1]}| : |{N[av]}{N[r2]}| = {ex(lu)} : {ex(lv)}",
            f"   L = (|{N[av]}{N[r2]}|·{N[r1]} + |{N[av]}{N[r1]}|·{N[r2]}) / (|{N[av]}{N[r1]}| + |{N[av]}{N[r2]}|) = L{pt_full(L)}",
            f"   Биссектриса — прямая {N[av]}L.",
        ]
        steps += box([f"биссектриса {N[av]}L:  {b_eq},   |{N[av]}L| = {fmt_num(b_len)}"], "answer")
        plot['points'].append((num(L[0]), num(L[1]), "L", COL_AMBER))
        plot['segments'].append(((num(P[av][0]), num(P[av][1])), (num(L[0]), num(L[1])), f"биссектриса {N[av]}L", COL_AMBER, '-'))

        return {'area': area, 'steps': "\n".join(steps), 'plot2d': plot,
                'median_eq': m_eq, 'altitude_eq': h_eq, 'bisector_eq': b_eq, 'angle_deg': ang, 'cos_angle': cosv}


# ----------------------------------------------------------------------------
# Прямая и точка на плоскости
# ----------------------------------------------------------------------------

class PlaneLineSolver:
    """Прямая l: Ax + By + C = 0 и точка M: параллельная, перпендикуляр, проекция, расстояние, симметрия."""

    @staticmethod
    def solve(A, B, C, pM) -> Dict[str, Any]:
        A, B, C = parse_number(A), parse_number(B), parse_number(C)
        M = parse_point(pM)
        if sgn(A) == 0 and sgn(B) == 0:
            raise ValueError("Коэффициенты A и B не могут одновременно равняться нулю")

        nrm2 = simp(A ** 2 + B ** 2)
        val = simp(A * M[0] + B * M[1] + C)
        # а) параллельная
        Cp = simp(-(A * M[0] + B * M[1]))
        par_eq, _ = line_eq(A, B, Cp)
        # б) перпендикуляр: направляющий вектор = n = (A, B)  =>  B(x − xM) − A(y − yM) = 0
        perp_eq, _ = line_eq(B, -A, simp(-(B * M[0] - A * M[1])))
        # в) проекция
        t = simp(-val / nrm2)
        H = (simp(M[0] + t * A), simp(M[1] + t * B))
        d = simp(sp.Abs(val) / sp.sqrt(nrm2))
        # г) симметрия
        Ms = (simp(2 * H[0] - M[0]), simp(2 * H[1] - M[1]))
        l_eq, _ = line_eq(A, B, C)

        steps = ["📌 ЭТАП 1. ТЕОРЕТИЧЕСКИЕ ФОРМУЛЫ"]
        steps += box([
            "Параллельная прямая:  тот же вектор нормали n⃗ = (A; B)",
            "Перпендикуляр:  направляющий вектор прямой = n⃗, т.е. B·(x − x₀) − A·(y − y₀) = 0",
            "Расстояние:  d = |A·x₀ + B·y₀ + C| / √(A² + B²)",
            "Проекция:  H = M − (A·x₀ + B·y₀ + C)/(A² + B²) · n⃗,    M' = 2H − M",
        ])
        steps += [
            "",
            "📝 ЭТАП 2. ИСХОДНЫЕ ДАННЫЕ",
            f"   ▸ l: {l_eq},   n⃗ = ({ex(A)}; {ex(B)}),   M{pt_str(M)}",
            f"   ▸ A·x₀ + B·y₀ + C = {ex(A)}·({ex(M[0])}) + {ex(B)}·({ex(M[1])}) + {ex(C)} = {ex(val)}",
            "",
            "⚙️ а) ПРЯМАЯ ЧЕРЕЗ M ПАРАЛЛЕЛЬНО l",
            f"   Вектор нормали сохраняется: {ex(A)}·(x − {ex(M[0])}) + {ex(B)}·(y − {ex(M[1])}) = 0",
        ]
        steps += box([par_eq], "answer")
        steps += [
            "",
            "⚙️ б) ПРЯМАЯ ЧЕРЕЗ M ПЕРПЕНДИКУЛЯРНО l",
            f"   Направляющий вектор s⃗ = n⃗ = ({ex(A)}; {ex(B)}):   ({ex(B)})·(x − {ex(M[0])}) − ({ex(A)})·(y − {ex(M[1])}) = 0",
        ]
        steps += box([perp_eq], "answer")
        steps += [
            "",
            "⚙️ в) ПРОЕКЦИЯ H ТОЧКИ M НА l И РАССТОЯНИЕ",
            f"   t = −({ex(val)}) / ({ex(A)}² + {ex(B)}²) = {ex(t)}",
            f"   H = M + t·n⃗ = ({ex(M[0])} + ({ex(t)})·({ex(A)}); {ex(M[1])} + ({ex(t)})·({ex(B)}))",
            f"   d = |{ex(val)}| / √{ex(nrm2)} = {fmt_num(d)}",
        ]
        steps += box([f"H{pt_full(H)},   d = {fmt_num(d)}"], "answer")
        if sgn(val) == 0:
            steps.append("   Точка M лежит на прямой l (d = 0), поэтому H = M и M' = M.")
        steps += [
            "",
            "⚙️ г) ТОЧКА M', СИММЕТРИЧНАЯ M ОТНОСИТЕЛЬНО l",
            "   H — середина отрезка MM'   ⟹   M' = 2H − M",
            f"   M' = (2·({ex(H[0])}) − ({ex(M[0])}); 2·({ex(H[1])}) − ({ex(M[1])}))",
        ]
        steps += box([f"M'{pt_full(Ms)}"], "answer")

        plot = new_scene2d()
        plot['title'] = "Прямая l, точка M и её проекция"
        plot['lines'].append((num(H[0]), num(H[1]), num(-B), num(A), f"l: {l_eq}", COL_MAIN))
        plot['lines'].append((num(M[0]), num(M[1]), num(-B), num(A), "∥ l", COL_GREEN))
        plot['lines'].append((num(M[0]), num(M[1]), num(A), num(B), "⊥ l", COL_AMBER))
        for nm, p, col in (("M", M, COL_RED), ("H", H, COL_GREEN), ("M'", Ms, COL_PINK)):
            plot['points'].append((num(p[0]), num(p[1]), nm, col))
        plot['segments'].append(((num(M[0]), num(M[1])), (num(Ms[0]), num(Ms[1])), "", COL_RED, '--'))
        return {'parallel': par_eq, 'perpendicular': perp_eq, 'H': H, 'distance': d, 'symmetric': Ms,
                'steps': "\n".join(steps), 'plot2d': plot}
