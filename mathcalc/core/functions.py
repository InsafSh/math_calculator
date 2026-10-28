"""
Функции и графики: графики y = f(x), исследование функции, параметрические и полярные кривые,
неявные кривые F(x, y) = 0, поверхности z = f(x, y) с линиями уровня.

Символьные вычисления (SymPy) используются там, где дают точный ответ; иначе — надёжные численные
методы на заданном отрезке (поиск смены знака + метод Брента).
"""

import math
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np
import sympy as sp

from .common import box, COL_AMBER, COL_GRAY, COL_GREEN, COL_MAIN, COL_RED
from .data import fmt_float, table_lines
from .expr import parse_bound, parse_expression, to_numpy
from .result import Scene3D, new_scene2d

F = fmt_float
PALETTE = ("#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899", "#14B8A6")
X = sp.Symbol('x', real=True)


def pretty(e) -> str:
    """Короткая читаемая запись выражения SymPy."""
    from .common import to_pretty_math
    return to_pretty_math(sp.sstr(e)).replace('log(', 'ln(')


def _range(a_text: str, b_text: str) -> Tuple[float, float]:
    a, b = float(parse_bound(a_text)), float(parse_bound(b_text))
    if not (math.isfinite(a) and math.isfinite(b)):
        raise ValueError("Границы отрезка должны быть конечными")
    if b <= a:
        raise ValueError("Правая граница должна быть больше левой")
    return a, b


def _split_functions(text: str) -> List[str]:
    parts = [p.strip() for chunk in str(text).splitlines() for p in chunk.split(';')]
    parts = [p for p in parts if p]
    if not parts:
        raise ValueError("Введите хотя бы одну функцию")
    return parts


def break_discontinuities(xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    """Разрыв линии графика в точках разрыва функции (иначе рисуется ложная вертикальная черта)."""
    ys = ys.astype(float).copy()
    finite = np.isfinite(ys)
    if finite.sum() < 3:
        return ys
    dy = np.abs(np.diff(ys))
    med = np.nanmedian(dy[np.isfinite(dy)]) if np.any(np.isfinite(dy)) else 0
    yr = np.nanpercentile(ys[finite], 95) - np.nanpercentile(ys[finite], 5)
    thr = max(50 * med, 0.5 * yr) if yr > 0 else np.inf
    jumps = np.where(dy > thr)[0]
    for j in jumps:
        # скачок со сменой знака или к очень большим значениям — разрыв второго рода/скачок
        ys[j + 1 if abs(ys[j + 1]) > abs(ys[j]) else j] = np.nan
    return ys


def sample(expr: sp.Expr, a: float, b: float, n: int = 2000) -> Tuple[np.ndarray, np.ndarray]:
    xs = np.linspace(a, b, n)
    ys = to_numpy(expr, ['x'])(xs)
    return xs, break_discontinuities(xs, ys)


def numeric_roots(f, a: float, b: float, n: int = 4000) -> List[float]:
    """Корни непрерывной функции на [a, b]: смена знака + метод Брента, плюс касания (минимум |f| ≈ 0)."""
    from scipy.optimize import brentq
    xs = np.linspace(a, b, n)
    with np.errstate(all='ignore'):
        ys = f(xs)
    roots: List[float] = []
    scale = np.nanmax(np.abs(ys[np.isfinite(ys)])) if np.any(np.isfinite(ys)) else 1.0
    for i in range(n - 1):
        y0, y1 = ys[i], ys[i + 1]
        if not (np.isfinite(y0) and np.isfinite(y1)):
            continue
        if y0 == 0:
            roots.append(float(xs[i]))
        elif y0 * y1 < 0:
            # смена знака через бесконечный разрыв (tg x) — не корень
            if abs(y0) + abs(y1) > 0.2 * scale and scale > 0 and n > 100:
                mid = f(np.array([(xs[i] + xs[i + 1]) / 2]))[0]
                if not np.isfinite(mid) or abs(mid) > max(abs(y0), abs(y1)):
                    continue
            try:
                roots.append(float(brentq(lambda t: float(f(np.array([t]))[0]), xs[i], xs[i + 1], xtol=1e-13)))
            except (ValueError, RuntimeError):
                pass
    for i in range(1, n - 1):  # касание оси без смены знака
        y = ys[i - 1:i + 2]
        if np.all(np.isfinite(y)) and abs(y[1]) <= abs(y[0]) and abs(y[1]) <= abs(y[2]) and \
                abs(y[1]) < 1e-9 * max(1.0, scale) and y[0] * y[2] > 0:
            roots.append(float(xs[i]))
    if np.isfinite(ys[-1]) and ys[-1] == 0:
        roots.append(float(xs[-1]))
    roots.sort()
    out: List[float] = []
    for r in roots:
        if not out or abs(r - out[-1]) > 1e-7 * max(1.0, abs(r)):
            out.append(r)
    return out


def solve_on_interval(expr: sp.Expr, a: float, b: float) -> Tuple[List[Any], str]:
    """
    Решения expr = 0 на [a, b]: сначала символьно (точные значения), иначе численно.
    Возвращает (список значений — sympy или float, описание способа).
    """
    try:
        sol = sp.solveset(sp.simplify(expr), X, domain=sp.Interval(a, b))
        if isinstance(sol, sp.FiniteSet) and all(s.is_real for s in sol):
            vals = sorted(sol, key=lambda s: float(s))
            if len(vals) <= 25:
                return list(vals), "символьно"
    except Exception:
        pass
    f = to_numpy(expr, ['x'])
    return numeric_roots(f, a, b), "численно"


def _finite_number(v) -> bool:
    """Конечное действительное число (не ±∞, не интервал накопления вида AccumBounds(−1, 1))."""
    return isinstance(v, sp.Expr) and not isinstance(v, sp.AccumBounds) and v.is_number and         v.is_real is True and v.is_finite is True


def _val(v) -> float:
    return float(v) if not isinstance(v, float) else v


def _vstr(v) -> str:
    """Точное значение (если есть) и приближение."""
    if isinstance(v, float):
        return F(v, 7)
    if v.is_Integer:
        return str(v)
    return f"{pretty(v)} ≈ {F(float(v), 7)}"


# =============================================================================
# Графики функций
# =============================================================================

def plot_functions(funcs_text: str, a_text: str, b_text: str) -> Dict[str, Any]:
    a, b = _range(a_text, b_text)
    funcs = _split_functions(funcs_text)
    exprs = [parse_expression(f, ['x']) for f in funcs]
    sc = new_scene2d(equal=False, title="Графики функций")
    sc['xlabel'], sc['ylabel'] = "x", "y"
    steps = ["📌 ФУНКЦИИ"]
    grid = np.linspace(a, b, 11)
    rows = []
    for i, e in enumerate(exprs):
        col = PALETTE[i % len(PALETTE)]
        xs, ys = sample(e, a, b)
        sc['curves'].append((xs, ys, f"y = {pretty(e)}", col))
        steps.append(f"   ▸ y{i + 1} = {pretty(e)}")
        nan_share = float(np.mean(~np.isfinite(ys)))
        if nan_share > 0.001:
            steps.append(f"     не определена на части отрезка ({F(100 * nan_share, 3)} % точек)")
        yv = to_numpy(e, ['x'])(grid)
        rows.append([F(v, 5) for v in yv])
    steps += ["", "📝 ТАБЛИЦА ЗНАЧЕНИЙ"]
    headers = ("x",) + tuple(f"y{i + 1}" for i in range(len(exprs)))
    table = [(F(xv, 4),) + tuple(r[j] for r in rows) for j, xv in enumerate(grid)]
    steps += box(table_lines(headers, table))
    if len(exprs) >= 2:
        steps += ["", "⚙️ ТОЧКИ ПЕРЕСЕЧЕНИЯ ГРАФИКОВ"]
        found = False
        for i in range(len(exprs)):
            for j in range(i + 1, len(exprs)):
                roots, how = solve_on_interval(exprs[i] - exprs[j], a, b)
                for r in roots:
                    yv = float(to_numpy(exprs[i], ['x'])(np.array([_val(r)]))[0])
                    if not math.isfinite(yv):
                        continue
                    if abs(yv) < 1e-12:  # шум округления вместо точного нуля
                        yv = 0.0
                    found = True
                    steps.append(f"   ▸ y{i + 1} = y{j + 1}:  x = {_vstr(r)},  y = {F(yv, 7)}  ({how})")
                    sc['points'].append((_val(r), yv, "", COL_RED))
        if not found:
            steps.append("   На отрезке пересечений нет.")
    return {'exprs': exprs, 'steps': "\n".join(steps), 'plot2d': sc}


# =============================================================================
# Исследование функции
# =============================================================================

def _sign_intervals(fn, points: Sequence[float], a: float, b: float, pos: str, neg: str) -> List[str]:
    """Знак функции на интервалах между точками разбиения."""
    cuts = sorted({a, b, *[p for p in points if a < p < b]})
    out = []
    for l, r in zip(cuts[:-1], cuts[1:]):
        mids = np.linspace(l, r, 7)[1:-1]
        vals = fn(mids)
        vals = vals[np.isfinite(vals)]
        if vals.size == 0:
            continue
        s = np.sign(np.median(vals))
        out.append(f"({F(l, 5)}; {F(r, 5)}): {pos if s > 0 else neg if s < 0 else 'постоянна'}")
    return out


def investigate_function(f_text: str, a_text: str, b_text: str) -> Dict[str, Any]:
    a, b = _range(a_text, b_text)
    f = parse_expression(f_text, ['x'])
    fn = to_numpy(f, ['x'])
    steps: List[str] = [f"📌 ФУНКЦИЯ  y = {pretty(f)},  исследование на [{F(a)}; {F(b)}]"]
    info: Dict[str, Any] = {}

    # 1. Область определения
    steps += ["", "📝 1. ОБЛАСТЬ ОПРЕДЕЛЕНИЯ"]
    domain = None
    try:
        domain = sp.calculus.util.continuous_domain(f, X, sp.S.Reals)
        steps.append(f"   D(f) = {pretty(domain)}  (множество, где функция определена и непрерывна)")
    except Exception:
        steps.append("   Символьно найти не удалось; на графике видны промежутки, где функция определена.")
    info['domain'] = domain

    # 2. Чётность и периодичность
    steps += ["", "📝 2. ЧЁТНОСТЬ, ПЕРИОДИЧНОСТЬ"]
    try:
        fm = sp.simplify(f.subs(X, -X))
        if sp.simplify(fm - f) == 0:
            steps.append("   f(−x) = f(x) — функция чётная (график симметричен относительно Oy).")
        elif sp.simplify(fm + f) == 0:
            steps.append("   f(−x) = −f(x) — функция нечётная (график симметричен относительно начала координат).")
        else:
            steps.append("   Функция общего вида (ни чётная, ни нечётная).")
    except Exception:
        steps.append("   Определить не удалось.")
    try:
        per = sp.periodicity(f, X)
        if per is not None and per != 0:
            steps.append(f"   Периодическая, наименьший период T = {pretty(per)}.")
    except Exception:
        pass

    # 3. Нули и пересечение с осями
    steps += ["", "📝 3. ПЕРЕСЕЧЕНИЕ С ОСЯМИ"]
    zeros, how = solve_on_interval(f, a, b)
    zeros = [z for z in zeros if math.isfinite(_val(z))]
    info['zeros'] = zeros
    steps.append("   Нули функции на отрезке (" + how + "): " + (", ".join(f"x = {_vstr(z)}" for z in zeros) if zeros else "нет"))
    try:
        y0 = f.subs(X, 0)
        if a <= 0 <= b and y0.is_real and y0.is_finite:
            steps.append(f"   Пересечение с Oy: y(0) = {_vstr(sp.nsimplify(y0) if y0.is_Float else y0)}")
    except Exception:
        pass

    # 4. Асимптоты
    steps += ["", "📝 4. АСИМПТОТЫ"]
    vert = []
    try:
        sing = sp.singularities(f, X, sp.Interval(a, b))
        if isinstance(sing, sp.FiniteSet):
            for s_ in sorted(sing, key=lambda v: float(v)):
                lim_l = sp.limit(f, X, s_, '-')
                lim_r = sp.limit(f, X, s_, '+')
                if lim_l.is_infinite or lim_r.is_infinite:
                    vert.append(s_)
                    steps.append(f"   Вертикальная: x = {_vstr(s_)}   (lim слева = {pretty(lim_l)}, справа = {pretty(lim_r)})")
                else:
                    steps.append(f"   В точке x = {_vstr(s_)} разрыв без бесконечного предела (слева {pretty(lim_l)}, справа {pretty(lim_r)})")
    except Exception:
        pass
    if not vert:
        steps.append("   Вертикальных асимптот на отрезке нет (или их не удалось найти символьно).")
    obliques = []
    for side, inf in (("+∞", sp.oo), ("−∞", -sp.oo)):
        try:
            k = sp.limit(f / X, X, inf)
            if _finite_number(k):
                bb = sp.limit(f - k * X, X, inf)
                if _finite_number(bb):
                    kind = "горизонтальная" if k == 0 else "наклонная"
                    obliques.append((k, bb))
                    steps.append(f"   При x → {side}: {kind} y = {pretty(sp.expand(k * X + bb))}   "
                                 f"(k = lim f/x = {pretty(k)}, b = lim (f − kx) = {pretty(bb)})")
                    continue
            steps.append(f"   При x → {side}: наклонной и горизонтальной асимптот нет.")
        except Exception:
            steps.append(f"   При x → {side}: вычислить пределы не удалось.")
    info['vertical'] = vert

    # 5. Производная, монотонность, экстремумы
    d1 = sp.simplify(sp.diff(f, X))
    steps += ["", "⚙️ 5. ПЕРВАЯ ПРОИЗВОДНАЯ: МОНОТОННОСТЬ И ЭКСТРЕМУМЫ"]
    steps += box([f"f′(x) = {pretty(d1)}"])
    tol = 1e-6 * max(1.0, b - a)

    def admissible(c) -> bool:
        """Точка внутри области определения и не на вертикальной асимптоте (численный поиск мог «найти» полюс)."""
        cv = _val(c)
        if not math.isfinite(cv) or any(abs(cv - _val(v)) < tol for v in vert):
            return False
        if domain is not None and not isinstance(c, float):
            try:
                if domain.contains(c) is sp.false:
                    return False
            except Exception:
                pass
        return math.isfinite(float(fn(np.array([cv]))[0]))

    crit, how1 = solve_on_interval(d1, a, b)
    crit = [c for c in crit if admissible(c)]
    d1n = to_numpy(d1, ['x'])
    steps.append("   Критические точки f′ = 0 (" + how1 + "): " + (", ".join(_vstr(c) for c in crit) if crit else "нет"))
    breaks = [_val(c) for c in crit] + [_val(v) for v in vert]
    for line in _sign_intervals(d1n, breaks, a, b, "f′ > 0 — возрастает ↗", "f′ < 0 — убывает ↘"):
        steps.append(f"   ▸ {line}")
    extrema = []
    h = 1e-4 * max(1.0, b - a)
    for c in crit:
        cv = _val(c)
        left, right = d1n(np.array([cv - h]))[0], d1n(np.array([cv + h]))[0]
        yv = float(fn(np.array([cv]))[0])
        if not math.isfinite(yv):
            continue
        if left > 0 > right:
            extrema.append((c, yv, "максимум"))
        elif left < 0 < right:
            extrema.append((c, yv, "минимум"))
    for c, yv, kind in extrema:
        exact = ""
        if not isinstance(c, float):
            try:
                ev = sp.simplify(f.subs(X, c))
                exact = f" = {pretty(ev)}" if not ev.is_Float else ""
            except Exception:
                pass
        steps.append(f"   ▸ Локальный {kind}: x = {_vstr(c)},  y{exact} ≈ {F(yv, 7)}")
    if not extrema:
        steps.append("   Локальных экстремумов на отрезке нет.")
    info['extrema'] = extrema

    # 6. Вторая производная, выпуклость, перегибы
    d2 = sp.simplify(sp.diff(d1, X))
    steps += ["", "⚙️ 6. ВТОРАЯ ПРОИЗВОДНАЯ: ВЫПУКЛОСТЬ И ПЕРЕГИБЫ"]
    steps += box([f"f″(x) = {pretty(d2)}"])
    infl_c, how2 = solve_on_interval(d2, a, b)
    infl_c = [c for c in infl_c if admissible(c)]
    d2n = to_numpy(d2, ['x'])
    inflections = []
    for c in infl_c:
        cv = _val(c)
        l_, r_ = d2n(np.array([cv - h]))[0], d2n(np.array([cv + h]))[0]
        yv = float(fn(np.array([cv]))[0])
        if math.isfinite(yv) and l_ * r_ < 0:
            inflections.append((c, yv))
    for line in _sign_intervals(d2n, [_val(c) for c in infl_c] + [_val(v) for v in vert], a, b,
                                "f″ > 0 — выпукла вниз ∪", "f″ < 0 — выпукла вверх ∩"):
        steps.append(f"   ▸ {line}")
    steps.append("   Точки перегиба (" + how2 + "): " +
                 (", ".join(f"({_vstr(c)}; {F(yv, 6)})" for c, yv in inflections) if inflections else "нет"))
    info['inflections'] = inflections

    # 7. Наибольшее и наименьшее значения на отрезке
    xs, ys = sample(f, a, b, 4000)
    if not vert and np.all(np.isfinite(ys)):
        cand = [(a, float(fn(np.array([a]))[0])), (b, float(fn(np.array([b]))[0]))] + [(_val(c), yv) for c, yv, _ in extrema]
        mx = max(cand, key=lambda t: t[1])
        mn = min(cand, key=lambda t: t[1])
        steps += ["", "📍 7. НАИБОЛЬШЕЕ И НАИМЕНЬШЕЕ ЗНАЧЕНИЯ НА ОТРЕЗКЕ"]
        steps.append("   Сравниваются значения на концах отрезка и в точках экстремума.")
        steps += box([f"max f = {F(mx[1], 7)} при x = {F(mx[0], 7)}", f"min f = {F(mn[1], 7)} при x = {F(mn[0], 7)}"], "answer")
        info['max'], info['min'] = mx, mn

    sc = new_scene2d(equal=False, title=f"y = {pretty(f)}")
    sc['xlabel'], sc['ylabel'] = "x", "y"
    sc['curves'].append((xs, ys, "y = f(x)", COL_MAIN))
    asym = [(_val(v), 0.0, 0.0, 1.0) for v in vert] + [(0.0, float(bb), 1.0, float(k)) for k, bb in obliques]
    for i, (px, py, dx, dy) in enumerate(asym):
        sc['lines'].append((px, py, dx, dy, "асимптоты" if i == 0 else "", COL_GRAY, '--'))
    for z in zeros:
        sc['points'].append((_val(z), 0.0, "", COL_GREEN))
    for c, yv, kind in extrema:
        sc['points'].append((_val(c), yv, "max" if kind == "максимум" else "min", COL_RED))
    for c, yv in inflections:
        sc['points'].append((_val(c), yv, "перегиб", COL_AMBER))
    return {'f': f, 'd1': d1, 'd2': d2, 'info': info, 'steps': "\n".join(steps), 'plot2d': sc}


# =============================================================================
# Параметрические и полярные кривые
# =============================================================================

def parametric_curve(x_text: str, y_text: str, t0_text: str, t1_text: str) -> Dict[str, Any]:
    t0, t1 = _range(t0_text, t1_text)
    xe, ye = parse_expression(x_text, ['t']), parse_expression(y_text, ['t'])
    ts = np.linspace(t0, t1, 3000)
    xs, ys = to_numpy(xe, ['t'])(ts), to_numpy(ye, ['t'])(ts)
    T = sp.Symbol('t', real=True)
    dx, dy = sp.simplify(sp.diff(xe, T)), sp.simplify(sp.diff(ye, T))
    speed = np.sqrt(to_numpy(dx, ['t'])(ts) ** 2 + to_numpy(dy, ['t'])(ts) ** 2)
    from scipy.integrate import trapezoid
    length = float(trapezoid(np.nan_to_num(speed), ts))
    area = 0.5 * float(trapezoid(np.nan_to_num(xs * to_numpy(dy, ['t'])(ts) - ys * to_numpy(dx, ['t'])(ts)), ts))
    steps = ["📌 ПАРАМЕТРИЧЕСКАЯ КРИВАЯ"]
    steps += box([f"x(t) = {pretty(xe)}", f"y(t) = {pretty(ye)}", f"t ∈ [{F(t0)}; {F(t1)}]"])
    steps += ["", "📝 ПРОИЗВОДНЫЕ"]
    steps.append(f"   x′(t) = {pretty(dx)},   y′(t) = {pretty(dy)}")
    try:
        steps.append(f"   dy/dx = y′/x′ = {pretty(sp.simplify(dy / dx))}")
    except Exception:
        pass
    steps += ["", "⚙️ ДЛИНА ДУГИ И ПЛОЩАДЬ (численно)"]
    steps += box(["L = ∫ √(x′² + y′²) dt",
                  "S = ½ ∫ (x·y′ − y·x′) dt   — ориентированная площадь (для замкнутой кривой — площадь фигуры)"])
    steps.append(f"   ▸ L ≈ {F(length, 7)}")
    steps.append(f"   ▸ S ≈ {F(area, 7)}")
    sc = new_scene2d(equal=True, title="Параметрическая кривая")
    sc['curves'].append((xs, ys, "", COL_MAIN))
    sc['points'].append((float(xs[0]), float(ys[0]), f"t = {F(t0, 4)}", COL_GREEN))
    sc['points'].append((float(xs[-1]), float(ys[-1]), f"t = {F(t1, 4)}", COL_RED))
    return {'length': length, 'area': area, 'steps': "\n".join(steps), 'plot2d': sc}


def polar_curve(r_text: str, p0_text: str, p1_text: str) -> Dict[str, Any]:
    p0, p1 = _range(p0_text, p1_text)
    re_ = parse_expression(r_text.replace('φ', 'phi').replace('θ', 'phi'), ['phi'])
    ps = np.linspace(p0, p1, 4000)
    rs = to_numpy(re_, ['phi'])(ps)
    xs, ys = rs * np.cos(ps), rs * np.sin(ps)
    PHI = sp.Symbol('phi', real=True)
    dr = sp.simplify(sp.diff(re_, PHI))
    from scipy.integrate import trapezoid
    drn = to_numpy(dr, ['phi'])(ps)
    length = float(trapezoid(np.nan_to_num(np.sqrt(rs ** 2 + drn ** 2)), ps))
    area = 0.5 * float(trapezoid(np.nan_to_num(rs ** 2), ps))
    steps = ["📌 КРИВАЯ В ПОЛЯРНЫХ КООРДИНАТАХ"]
    steps += box([f"r(φ) = {pretty(re_).replace('phi', 'φ')},  φ ∈ [{F(p0)}; {F(p1)}]",
                  "x = r·cos φ,  y = r·sin φ"])
    steps += ["", "⚙️ ДЛИНА И ПЛОЩАДЬ СЕКТОРА (численно)"]
    steps += box(["L = ∫ √(r² + r′²) dφ", "S = ½ ∫ r² dφ"])
    steps.append(f"   r′(φ) = {pretty(dr).replace('phi', 'φ')}")
    steps.append(f"   ▸ L ≈ {F(length, 7)}")
    steps.append(f"   ▸ S ≈ {F(area, 7)}  (при самопересечениях участки считаются многократно)")
    if np.any(rs < 0):
        steps.append("   r(φ) < 0 на части промежутка — точки откладываются в противоположном направлении.")
    sc = new_scene2d(equal=True, title="Полярная кривая")
    sc['curves'].append((xs, ys, "", COL_MAIN))
    return {'length': length, 'area': area, 'steps': "\n".join(steps), 'plot2d': sc}


# =============================================================================
# Неявные кривые и поверхности
# =============================================================================

def implicit_curve(eq_text: str, x0: str, x1: str, y0: str, y1: str) -> Dict[str, Any]:
    a, b = _range(x0, x1)
    c, d = _range(y0, y1)
    txt = str(eq_text)
    if '=' in txt:
        lhs, rhs = txt.split('=', 1)
        expr = parse_expression(lhs, ['x', 'y']) - parse_expression(rhs, ['x', 'y'])
    else:
        expr = parse_expression(txt, ['x', 'y'])
    n = 600
    Xg, Yg = np.meshgrid(np.linspace(a, b, n), np.linspace(c, d, n))
    Z = to_numpy(expr, ['x', 'y'])(Xg, Yg)
    if not np.any(np.isfinite(Z)):
        raise ValueError("Функция не определена в заданной области")
    zf = Z[np.isfinite(Z)]
    if zf.min() > 0 or zf.max() < 0:
        raise ValueError("В заданной области F(x, y) не меняет знак — кривая F = 0 сюда не попадает. Расширьте область.")
    Y_ = sp.Symbol('y', real=True)
    Fx, Fy = sp.simplify(sp.diff(expr, X)), sp.simplify(sp.diff(expr, Y_))
    steps = ["📌 НЕЯВНАЯ КРИВАЯ  F(x, y) = 0"]
    steps += box([f"F(x, y) = {pretty(expr)}", f"x ∈ [{F(a)}; {F(b)}],  y ∈ [{F(c)}; {F(d)}]"])
    steps += ["", "📝 ПРОИЗВОДНАЯ НЕЯВНОЙ ФУНКЦИИ"]
    steps += box(["dy/dx = −F′ₓ / F′ᵧ"])
    steps.append(f"   F′ₓ = {pretty(Fx)},   F′ᵧ = {pretty(Fy)}")
    steps.append(f"   dy/dx = {pretty(sp.simplify(-Fx / Fy))}")
    steps.append("   Особые точки (F = F′ₓ = F′ᵧ = 0) — точки самопересечения, возврата или изолированные.")
    try:
        sing = sp.solve([expr, Fx, Fy], [X, Y_], dict=True)
        real = [s for s in sing if all(v.is_real for v in s.values())]
        steps.append("   Найдены: " + (", ".join(f"({pretty(s[X])}; {pretty(s[Y_])})" for s in real) if real else "нет"))
    except Exception:
        steps.append("   Символьно найти не удалось.")
    sc = new_scene2d(equal=True, title="F(x, y) = 0")
    sc['contours'].append((Xg, Yg, Z, [0.0], "F(x, y) = 0", COL_MAIN))
    sc['xlim'], sc['ylim'] = (a, b), (c, d)
    return {'expr': expr, 'steps': "\n".join(steps), 'plot2d': sc}


def surface(f_text: str, x0: str, x1: str, y0: str, y1: str, levels: int = 15) -> Dict[str, Any]:
    a, b = _range(x0, x1)
    c, d = _range(y0, y1)
    expr = parse_expression(f_text, ['x', 'y'])
    Y_ = sp.Symbol('y', real=True)
    n = 70
    Xg, Yg = np.meshgrid(np.linspace(a, b, n), np.linspace(c, d, n))
    Z = to_numpy(expr, ['x', 'y'])(Xg, Yg)
    if not np.any(np.isfinite(Z)):
        raise ValueError("Функция не определена в заданной области")
    fx, fy = sp.simplify(sp.diff(expr, X)), sp.simplify(sp.diff(expr, Y_))
    steps = ["📌 ФУНКЦИЯ ДВУХ ПЕРЕМЕННЫХ"]
    steps += box([f"z = {pretty(expr)}", f"x ∈ [{F(a)}; {F(b)}],  y ∈ [{F(c)}; {F(d)}]"])
    steps += ["", "📝 ЧАСТНЫЕ ПРОИЗВОДНЫЕ И ГРАДИЕНТ"]
    steps.append(f"   ∂z/∂x = {pretty(fx)}")
    steps.append(f"   ∂z/∂y = {pretty(fy)}")
    steps.append(f"   grad z = ({pretty(fx)}; {pretty(fy)})  — направлен перпендикулярно линиям уровня")
    zf = Z[np.isfinite(Z)]
    i_max, i_min = np.nanargmax(Z), np.nanargmin(Z)
    steps += ["", "⚙️ ЗНАЧЕНИЯ В ОБЛАСТИ (по сетке)"]
    steps.append(f"   ▸ max z ≈ {F(float(zf.max()), 6)} в ({F(Xg.flat[i_max], 4)}; {F(Yg.flat[i_max], 4)})")
    steps.append(f"   ▸ min z ≈ {F(float(zf.min()), 6)} в ({F(Xg.flat[i_min], 4)}; {F(Yg.flat[i_min], 4)})")
    steps.append("   Точные стационарные точки и их тип — в задаче «Экстремумы функции нескольких переменных».")
    sc3 = Scene3D(labels=("x", "y", "z")).add_surface(Xg, Yg, Z, f"z = {pretty(expr)}")
    Xc, Yc = np.meshgrid(np.linspace(a, b, 300), np.linspace(c, d, 300))
    Zc = to_numpy(expr, ['x', 'y'])(Xc, Yc)
    sc2 = new_scene2d(equal=(abs((b - a) - (d - c)) < 0.5 * max(b - a, d - c)), title="Линии уровня z = const")
    sc2['xlabel'], sc2['ylabel'] = "x", "y"
    zfin = Zc[np.isfinite(Zc)]
    lo, hi = np.percentile(zfin, [2, 98])
    sc2['contours'].append((Xc, Yc, Zc, np.linspace(lo, hi, levels), "", None))
    sc2['xlim'], sc2['ylim'] = (a, b), (c, d)
    return {'expr': expr, 'steps': "\n".join(steps), 'plot2d': sc2, 'scene3d': sc3}
