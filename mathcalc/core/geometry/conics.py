"""
Кривые второго порядка: классификация, поворот и перенос осей, канонический вид, характеристики.
"""

from typing import Any, Dict

import numpy as np
import sympy as sp

from ..common import (
    parse_number, fmt_num, simp, sgn, ex, signed, shifted, num, box, new_scene2d,
    COL_MAIN, COL_RED, COL_AMBER, COL_PINK, COL_GRAY,
)


# ----------------------------------------------------------------------------
# Кривые второго порядка
# ----------------------------------------------------------------------------

def poly_str(a, b, c, d, e, f, vx="x", vy="y") -> str:
    terms = [(a, f"{vx}²"), (b, f"{vx}{vy}"), (c, f"{vy}²"), (d, vx), (e, vy), (f, "")]
    out = ""
    for coef, mon in terms:
        coef = simp(coef)
        if sgn(coef) == 0:
            continue
        sign = "-" if sgn(coef) < 0 else "+"
        ac = simp(abs(coef)) if coef.is_number and sgn(coef) < 0 else coef
        cs = ex(ac)
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
        if sgn(a) == 0 and sgn(b) == 0 and sgn(c) == 0:
            raise ValueError("Коэффициенты при x², xy, y² нулевые — это не кривая второго порядка")

        delta = simp(a * c - b ** 2 / 4)
        steps = ["📌 ЭТАП 1. ТЕОРЕТИЧЕСКАЯ СПРАВКА"]
        steps += box([
            "Общий вид:  A·x² + B·xy + C·y² + D·x + E·y + F = 0",
            "Инвариант δ = A·C − B²/4:  δ > 0 — эллипс,  δ < 0 — гипербола,  δ = 0 — парабола",
            "Если B ≠ 0 — поворот осей: x = x'·cosθ − y'·sinθ,  y = x'·sinθ + y'·cosθ,  tg 2θ = B/(A − C)",
            "Затем — выделение полных квадратов (параллельный перенос начала координат).",
        ])
        steps += [
            "",
            "📝 ЭТАП 2. ИСХОДНОЕ УРАВНЕНИЕ И ТИП",
            f"   {poly_str(a, b, c, d, e, f)}",
            f"   δ = {ex(a)}·({ex(c)}) − ({ex(b)})²/4 = {ex(delta)}",
        ]
        dsgn = sgn(delta)
        steps.append("   δ " + (">" if dsgn > 0 else "<" if dsgn < 0 else "=") + " 0  ⟹  тип по инварианту: " +
                     ("эллиптический" if dsgn > 0 else "гиперболический" if dsgn < 0 else "параболический"))

        # ---- поворот осей ----
        cosT, sinT = sp.Integer(1), sp.Integer(0)
        a2, c2, d2, e2 = a, c, d, e
        theta_deg = 0.0
        if sgn(b) != 0:
            R = simp(sp.sqrt((a - c) ** 2 + b ** 2))
            cos2 = simp((a - c) / R)
            cosT = simp(sp.sqrt(simp((1 + cos2) / 2)))
            sinT = simp(sgn(b) * sp.sqrt(simp((1 - cos2) / 2)))
            a2 = simp(a * cosT ** 2 + b * cosT * sinT + c * sinT ** 2)
            c2 = simp(a * sinT ** 2 - b * cosT * sinT + c * cosT ** 2)
            d2 = simp(d * cosT + e * sinT)
            e2 = simp(-d * sinT + e * cosT)
            theta_deg = float(np.degrees(np.arctan2(num(sinT), num(cosT))))
            steps += [
                "",
                "⚙️ ЭТАП 3. ПОВОРОТ ОСЕЙ (устранение члена с xy)",
                f"   tg 2θ = B/(A − C) = {ex(b)}/({ex(a - c)})" if sgn(a - c) != 0 else "   A = C  ⟹  cos 2θ = 0,  θ = ±45° (знак — по знаку B)",
                f"   cos 2θ = (A − C)/√((A − C)² + B²) = {ex(cos2)}",
                f"   cos θ = √((1 + cos 2θ)/2) = {ex(cosT)},   sin θ = {'+' if sgn(b) > 0 else '−'}√((1 − cos 2θ)/2) = {ex(sinT)}",
                f"   Угол поворота θ ≈ {theta_deg:.2f}°",
                "   Подстановка в уравнение даёт коэффициенты:",
                f"     A' = A·cos²θ + B·sinθ·cosθ + C·sin²θ = {ex(a2)}",
                f"     C' = A·sin²θ − B·sinθ·cosθ + C·cos²θ = {ex(c2)}",
                f"     D' = D·cosθ + E·sinθ = {ex(d2)},    E' = −D·sinθ + E·cosθ = {ex(e2)}",
            ]
            steps += box([poly_str(a2, 0, c2, d2, e2, f, "x'", "y'")])
            steps.append(f"   Новые базисные векторы: e⃗₁ = ({ex(cosT)}; {ex(sinT)}),  e⃗₂ = ({ex(-sinT)}; {ex(cosT)})")
        else:
            steps += ["", "⚙️ ЭТАП 3. ПОВОРОТ ОСЕЙ", "   Член с xy отсутствует (B = 0) — поворот не нужен, оси канонического вида параллельны исходным."]

        U, V = ("x'", "y'") if sgn(b) != 0 else ("x", "y")

        def to_world(u, v):
            return (simp(u * cosT - v * sinT), simp(u * sinT + v * cosT))

        def dir_world(du, dv):
            return (num(du * cosT - dv * sinT), num(du * sinT + dv * cosT))

        plot = new_scene2d()
        info: Dict[str, Any] = {}
        steps += ["", "⚙️ ЭТАП 4. ВЫДЕЛЕНИЕ ПОЛНЫХ КВАДРАТОВ"]
        ca, cc = sgn(a2), sgn(c2)

        def add_pt(p_uv, name, color):
            w = to_world(*p_uv)
            plot['points'].append((num(w[0]), num(w[1]), name, color))
            return w

        def add_line_uv(p_uv, du, dv, label, color):
            w = to_world(*p_uv)
            dx, dy = dir_world(du, dv)
            plot['lines'].append((num(w[0]), num(w[1]), dx, dy, label, color))

        def frame_note(p_uv):
            if sgn(b) == 0:
                return ""
            w = to_world(*p_uv)
            return f"  — в исходной системе: ({ex(w[0])}; {ex(w[1])})"

        result_type = ""
        canon = ""

        if ca != 0 and cc != 0:
            u0 = simp(-d2 / (2 * a2))
            v0 = simp(-e2 / (2 * c2))
            K = simp(d2 ** 2 / (4 * a2) + e2 ** 2 / (4 * c2) - f)
            steps += [
                f"   {ex(a2)}·({U}² {signed(d2 / a2)}·{U}) {signed(c2)}·({V}² {signed(e2 / c2)}·{V}) {signed(f)} = 0",
                f"   {ex(a2)}·{shifted(U, u0)}² {signed(c2)}·{shifted(V, v0)}² = {ex(K)}",
                f"   Параллельный перенос: X = {U} {signed(-u0)},  Y = {V} {signed(-v0)}",
                f"   Центр O'({ex(u0)}; {ex(v0)}) в системе ({U}, {V}){frame_note((u0, v0))}",
            ]
            if ca * cc > 0:
                if sgn(K) == 0:
                    result_type = "Вырожденный случай: единственная точка"
                    canon = f"{ex(a2)}·X² {signed(c2)}·Y² = 0"
                    add_pt((u0, v0), "O'", COL_RED)
                elif sgn(K) * ca < 0:
                    result_type = "Мнимый эллипс (пустое множество — действительных точек нет)"
                    canon = f"{ex(a2)}·X² {signed(c2)}·Y² = {ex(K)}  (знаки левой и правой частей разные — решений нет)"
                else:
                    A2, B2 = simp(K / a2), simp(K / c2)
                    aa, bb = simp(sp.sqrt(A2)), simp(sp.sqrt(B2))
                    canon = f"X²/{ex(A2)} + Y²/{ex(B2)} = 1"
                    steps += ["   Делим на правую часть:", f"   {canon}"]
                    if sgn(A2 - B2) == 0:
                        result_type = f"Окружность радиуса R = {ex(aa)}"
                        info.update(center=(u0, v0), R=aa)
                        steps.append(f"   a = b ⟹ окружность, центр O'({ex(u0)}; {ex(v0)}), R = {ex(aa)}")
                        add_pt((u0, v0), "O'", COL_RED)
                    else:
                        result_type = "Эллипс"
                        along_u = sgn(A2 - B2) > 0
                        big, small = (aa, bb) if along_u else (bb, aa)
                        cf = simp(sp.sqrt(simp(big ** 2 - small ** 2)))
                        eps = simp(cf / big)
                        f1 = (u0 - cf, v0) if along_u else (u0, v0 - cf)
                        f2 = (u0 + cf, v0) if along_u else (u0, v0 + cf)
                        info.update(center=(u0, v0), a=big, b=small, c=cf, e=eps)
                        steps += [
                            f"   Полуоси: a = {ex(big)} (большая), b = {ex(small)} (малая); большая полуось направлена вдоль оси {'X' if along_u else 'Y'}",
                            f"   c = √(a² − b²) = {fmt_num(cf)},   ε = c/a = {fmt_num(eps)}",
                            f"   Фокусы: F₁({ex(f1[0])}; {ex(f1[1])}),  F₂({ex(f2[0])}; {ex(f2[1])}) в системе ({U}, {V}){frame_note(f2)}",
                        ]
                        if sgn(eps) != 0:
                            dd = simp(big / eps)
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
                    xs_u = num(u0) + num(aa) * np.cos(ts)
                    xs_v = num(v0) + num(bb) * np.sin(ts)
                    cx_ = xs_u * num(cosT) - xs_v * num(sinT)
                    cy_ = xs_u * num(sinT) + xs_v * num(cosT)
                    plot['curves'].append((cx_, cy_, "", COL_MAIN))
            else:
                if sgn(K) == 0:
                    result_type = "Вырожденный случай: пара пересекающихся прямых"
                    kk = simp(sp.sqrt(simp(-a2 / c2)))
                    canon = f"Y = ±{ex(kk)}·X"
                    steps.append(f"   Правая часть равна 0: {canon}")
                    add_line_uv((u0, v0), 1, kk, "", COL_MAIN)
                    add_line_uv((u0, v0), 1, -kk, "", COL_MAIN)
                    add_pt((u0, v0), "O'", COL_RED)
                else:
                    result_type = "Гипербола"
                    real_u = sgn(K) * ca > 0
                    if real_u:
                        aa, bb = simp(sp.sqrt(simp(K / a2))), simp(sp.sqrt(simp(-K / c2)))
                        canon = f"X²/{ex(aa ** 2)} − Y²/{ex(bb ** 2)} = 1"
                    else:
                        aa, bb = simp(sp.sqrt(simp(K / c2))), simp(sp.sqrt(simp(-K / a2)))
                        canon = f"Y²/{ex(aa ** 2)} − X²/{ex(bb ** 2)} = 1"
                    cf = simp(sp.sqrt(simp(aa ** 2 + bb ** 2)))
                    eps = simp(cf / aa)
                    f1 = (u0 - cf, v0) if real_u else (u0, v0 - cf)
                    f2 = (u0 + cf, v0) if real_u else (u0, v0 + cf)
                    info.update(center=(u0, v0), a=aa, b=bb, c=cf, e=eps)
                    steps += [
                        "   Делим на правую часть:", f"   {canon}",
                        f"   Действительная полуось a = {ex(aa)} (вдоль оси {'X' if real_u else 'Y'}), мнимая b = {ex(bb)}",
                        f"   c = √(a² + b²) = {fmt_num(cf)},   ε = c/a = {fmt_num(eps)}",
                        f"   Фокусы: F₁({ex(f1[0])}; {ex(f1[1])}),  F₂({ex(f2[0])}; {ex(f2[1])}) в системе ({U}, {V}){frame_note(f2)}",
                    ]
                    if real_u:
                        sl = simp(bb / aa)
                        steps.append(f"   Асимптоты: Y = ±{ex(sl)}·X   (то есть {V} {signed(-v0)} = ±{ex(sl)}·{shifted(U, u0)})")
                        dirs = [(1, sl), (1, -sl)]
                    else:
                        sl = simp(aa / bb)
                        steps.append(f"   Асимптоты: Y = ±{ex(sl)}·X   (то есть {V} {signed(-v0)} = ±{ex(sl)}·{shifted(U, u0)})")
                        dirs = [(1, sl), (1, -sl)]
                    dd = simp(aa / eps)
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
                            pu = num(u0) + sg * num(aa) * np.cosh(ss)
                            pv = num(v0) + num(bb) * np.sinh(ss)
                        else:
                            pv = num(v0) + sg * num(aa) * np.cosh(ss)
                            pu = num(u0) + num(bb) * np.sinh(ss)
                        plot['curves'].append((pu * num(cosT) - pv * num(sinT), pu * num(sinT) + pv * num(cosT), "", COL_MAIN))
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
            q0 = simp(-lin_q / (2 * qq))
            steps.append(f"   Уравнение содержит только {nq}²: {ex(qq)}·{nq}² {signed(lin_q)}·{nq} {signed(lin_o)}·{no} {signed(f)} = 0")
            if sgn(lin_o) == 0:
                disc = simp(lin_q ** 2 - 4 * qq * f)
                steps.append(f"   Коэффициент при {no} равен 0: квадратное уравнение относительно {nq}, D = {ex(disc)}")
                if sgn(disc) > 0:
                    r1 = simp((-lin_q - sp.sqrt(disc)) / (2 * qq))
                    r2 = simp((-lin_q + sp.sqrt(disc)) / (2 * qq))
                    result_type = "Вырожденный случай: пара параллельных прямых"
                    canon = f"{nq} = {ex(r1)},  {nq} = {ex(r2)}"
                    for r in (r1, r2):
                        if not swap:
                            add_line_uv((r, 0), 0, 1, "", COL_MAIN)
                        else:
                            add_line_uv((0, r), 1, 0, "", COL_MAIN)
                elif sgn(disc) == 0:
                    result_type = "Вырожденный случай: двойная прямая (две совпавшие прямые)"
                    canon = f"{nq} = {ex(q0)}"
                    if not swap:
                        add_line_uv((q0, 0), 0, 1, "", COL_MAIN)
                    else:
                        add_line_uv((0, q0), 1, 0, "", COL_MAIN)
                else:
                    result_type = "Мнимые параллельные прямые (действительных точек нет)"
                    canon = f"{nq} = {ex(q0)} ± i·√{ex(-disc / (4 * qq ** 2))}"
            else:
                o0 = simp((lin_q ** 2 / (4 * qq) - f) / lin_o)
                pt_ = simp(-lin_o / (2 * qq))  # (nq - q0)^2 = 2·pt·(no - o0)
                p_abs = simp(abs(pt_))
                steps += [
                    f"   {ex(qq)}·{shifted(nq, q0)}² = {ex(-lin_o)}·{shifted(no, o0)}",
                    f"   Параллельный перенос: вершина O'({nq} = {ex(q0)}, {no} = {ex(o0)})",
                ]
                nqX, noY = ("X", "Y") if not swap else ("Y", "X")
                # каноническое: (nq')² = 2p (no') ; запись в виде y² = 2px
                canon = f"{nqX}² = {ex(2 * pt_)}·{noY}"
                result_type = "Парабола"
                steps += [
                    f"   Каноническое уравнение:  {canon}   (вида {'x² = 2py' if not swap else 'y² = 2px'})",
                    f"   Параметр параболы p = {ex(p_abs)}  (расстояние от фокуса до директрисы)",
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
                    f"   Вершина: ({ex(vertex[0])}; {ex(vertex[1])}),   фокус F({ex(focus[0])}; {ex(focus[1])}) в системе ({U}, {V}){frame_note(focus)}",
                    f"   Директриса: {no} = {ex(dir_c[1])} (в системе ({U}, {V}))",
                    f"   Ось симметрии параллельна оси {'Oy' if not swap else 'Ox'} (в системе {U}{V}), ветви направлены {'вверх' if (not swap and sgn(pt_) > 0) else 'вниз' if not swap else 'вправо' if sgn(pt_) > 0 else 'влево'}",
                    "   Эксцентриситет ε = 1",
                ]
                info.update(vertex=vertex, p=p_abs, focus=focus)
                add_pt(vertex, "вершина", COL_RED)
                add_pt(focus, "F", COL_AMBER)
                if not swap:
                    add_line_uv((0, dir_c[1]), 1, 0, "директриса", COL_PINK)
                else:
                    add_line_uv((dir_c[1], 0), 0, 1, "директриса", COL_PINK)
                span = 4 * max(1.0, num(p_abs))
                ss = np.linspace(-span, span, 300)
                if not swap:
                    pu = num(q0) + ss
                    pv = num(o0) + ss ** 2 / (2 * num(pt_))
                else:
                    pv = num(q0) + ss
                    pu = num(o0) + ss ** 2 / (2 * num(pt_))
                plot['curves'].append((pu * num(cosT) - pv * num(sinT), pu * num(sinT) + pv * num(cosT), "", COL_MAIN))

        steps += ["", "🎯 ИТОГ"]
        ans = [f"Тип кривой: {result_type}", f"Канонический вид: {canon}"]
        if sgn(b) != 0:
            ans.append(f"Угол поворота θ ≈ {theta_deg:.2f}°,  cosθ = {ex(cosT)},  sinθ = {ex(sinT)}")
        if 'center' in info:
            w = to_world(*info['center'])
            ans.append(f"Центр: ({ex(w[0])}; {ex(w[1])}) в исходной системе")
        for k, nm in (('a', 'a'), ('b', 'b'), ('c', 'c'), ('e', 'ε')):
            if k in info:
                ans.append(f"{nm} = {fmt_num(info[k])}")
        if 'vertex' in info:
            w = to_world(*info['vertex'])
            wf = to_world(*info['focus'])
            ans.append(f"Вершина: ({ex(w[0])}; {ex(w[1])}),  фокус: ({ex(wf[0])}; {ex(wf[1])}) в исходной системе,  p = {ex(info['p'])}")
        steps += box(ans, "answer")

        plot['title'] = result_type
        plot['equal'] = True
        return {'type': result_type, 'canonical': canon, 'theta_deg': theta_deg, 'info': info,
                'steps': "\n".join(steps), 'plot2d': plot}
