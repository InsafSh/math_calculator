"""
Обработка результатов эксперимента.

  * прямые многократные измерения — ГОСТ Р 8.736-2011 (выбросы по критерию Граббса,
    доверительные границы случайной погрешности, учёт неисключённой систематической погрешности);
  * косвенные измерения — распространение погрешностей через частные производные (символьно);
  * аппроксимация методом наименьших квадратов — линейная (с выводом формул), полиномиальная,
    экспоненциальная, степенная, логарифмическая, произвольная формула; доверительные интервалы
    параметров и доверительная полоса кривой;
  * табличная функция — интерполяция, численная производная, интеграл.
"""

import math
import re
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np
import sympy as sp

from .common import box, to_pretty_math, COL_MAIN, COL_RED, COL_GREEN, COL_AMBER, COL_GRAY
from .data import fmt_float, parse_series, parse_table, round_measurement, student_t, table_lines
from .expr import parse_expression
from .result import new_scene2d

F = fmt_float


def _result_line(name: str, value: float, err: float, unit: str, P: float) -> Tuple[str, str, str]:
    v, e, _ = round_measurement(value, err)
    u = f" {unit}" if unit else ""
    return f"{name} = ({v} ± {e}){u},   P = {P:g}", v, e


# =============================================================================
# Прямые многократные измерения
# =============================================================================

def grubbs_critical(n: int, alpha: float) -> float:
    """Критическое значение критерия Граббса (одностороннее, для одного крайнего значения)."""
    from scipy import stats
    t = stats.t.ppf(1 - alpha / n, n - 2)
    return (n - 1) / math.sqrt(n) * math.sqrt(t * t / (n - 2 + t * t))


def direct_measurements(text: str, P: float = 0.95, theta: float = 0.0, unit: str = "", name: str = "x",
                        outliers: str = "exclude") -> Dict[str, Any]:
    """
    Обработка ряда прямых равноточных измерений.
    theta — граница неисключённой систематической погрешности (обычно предел допускаемой погрешности прибора).
    outliers: "exclude" — проверить и исключить, "check" — только проверить, "none" — не проверять.
    """
    x_all = parse_series(text)
    if len(x_all) < 2:
        raise ValueError("Нужно не менее двух измерений")
    if theta < 0:
        raise ValueError("Погрешность прибора не может быть отрицательной")
    if not 0 < P < 1:
        raise ValueError("Доверительная вероятность должна быть между 0 и 1")
    u = f" {unit}" if unit else ""
    steps: List[str] = ["📌 ЭТАП 1. ИСХОДНЫЕ ДАННЫЕ"]
    steps.append(f"   ▸ Число измерений n = {len(x_all)},  доверительная вероятность P = {P:g}")
    steps.append(f"   ▸ Граница систематической погрешности (прибора) θ = {F(theta)}{u}")
    steps += box([f"{name}: " + ";  ".join(F(v) for v in x_all)])

    x = x_all.copy()
    excluded: List[float] = []
    steps += ["", "📝 ЭТАП 2. ПРОВЕРКА НА ГРУБЫЕ ПОГРЕШНОСТИ (критерий Граббса)"]
    if outliers == "none":
        steps.append("   Проверка отключена.")
    elif len(x) < 3:
        steps.append("   Для проверки нужно не менее трёх измерений — пропущено.")
    else:
        steps += box([
            "G₁ = (x_max − x̄)/S,   G₂ = (x̄ − x_min)/S",
            "Gкр = (n − 1)/√n · √(t² / (n − 2 + t²)),  t — квантиль Стьюдента уровня 1 − q/n, n − 2 ст. свободы",
            "Если G > Gкр, результат считается грубой погрешностью (промахом).",
        ])
        q = 1 - P
        while len(x) >= 3:
            m, s = x.mean(), x.std(ddof=1)
            if s == 0:
                steps.append("   Все значения одинаковы — промахов нет.")
                break
            g1, g2 = (x.max() - m) / s, (m - x.min()) / s
            gk = grubbs_critical(len(x), q)
            steps.append(f"   n = {len(x)}: x̄ = {F(m)}, S = {F(s)};  G₁ = {F(g1, 4)},  G₂ = {F(g2, 4)},  "
                         f"Gкр(q = {q:g}) = {F(gk, 4)}")
            if max(g1, g2) <= gk:
                steps.append("   G₁, G₂ ≤ Gкр — грубых погрешностей нет.")
                break
            bad = x.max() if g1 >= g2 else x.min()
            if outliers == "check":
                steps.append(f"   Значение {F(bad)} — вероятный промах (G > Gкр). Исключение отключено, оно остаётся в обработке.")
                break
            steps.append(f"   Значение {F(bad)} — промах (G > Gкр), исключается.")
            excluded.append(float(bad))
            idx = int(np.where(x == bad)[0][0])
            x = np.delete(x, idx)
        if len(x) < 2:
            raise ValueError("После исключения промахов осталось меньше двух измерений")

    n = len(x)
    mean = float(x.mean())
    S = float(x.std(ddof=1))
    S_mean = S / math.sqrt(n)
    t = student_t(P, n - 1)
    eps = t * S_mean

    steps += ["", "⚙️ ЭТАП 3. СРЕДНЕЕ, СКО И СЛУЧАЙНАЯ ПОГРЕШНОСТЬ"]
    steps += box([
        "x̄ = Σxᵢ / n",
        "S = √( Σ(xᵢ − x̄)² / (n − 1) )      — СКО отдельного измерения",
        "S_x̄ = S / √n                        — СКО среднего",
        "ε = t(P, n − 1) · S_x̄               — доверительная граница случайной погрешности",
    ])
    steps += [
        f"   ▸ n = {n}" + (f"  (исключено промахов: {len(excluded)})" if excluded else ""),
        f"   ▸ x̄ = {F(mean, 8)}{u}",
        f"   ▸ S = {F(S)}{u},   S_x̄ = {F(S_mean)}{u}",
        f"   ▸ t({P:g}; {n - 1}) = {F(t, 5)}",
        f"   ▸ ε = {F(t, 5)} · {F(S_mean)} = {F(eps)}{u}",
    ]

    steps += ["", "⚙️ ЭТАП 4. ПОЛНАЯ ПОГРЕШНОСТЬ (ГОСТ Р 8.736-2011)"]
    if theta == 0:
        delta = eps
        rule = "θ = 0: Δ = ε"
        steps.append("   Систематическая погрешность не задана: Δ = ε.")
    else:
        ratio = theta / S_mean if S_mean > 0 else math.inf
        steps.append(f"   ▸ θ / S_x̄ = {F(theta)} / {F(S_mean)} = {F(ratio, 4)}")
        if ratio < 0.8:
            delta, rule = eps, "θ/S_x̄ < 0,8: систематической погрешностью пренебрегают, Δ = ε"
        elif ratio > 8:
            delta, rule = theta, "θ/S_x̄ > 8: случайной погрешностью пренебрегают, Δ = θ"
        else:
            S_theta = theta / math.sqrt(3)
            S_sum = math.sqrt(S_theta ** 2 + S_mean ** 2)
            K = (eps + theta) / (S_mean + S_theta)
            delta = K * S_sum
            rule = "0,8 ≤ θ/S_x̄ ≤ 8: Δ = K·S_Σ"
            steps += box([
                "S_θ = θ / √3,   S_Σ = √(S_θ² + S_x̄²),   K = (ε + θ) / (S_x̄ + S_θ),   Δ = K · S_Σ",
            ])
            steps.append(f"   ▸ S_θ = {F(S_theta)},  S_Σ = {F(S_sum)},  K = {F(K, 4)}")
        steps.append(f"   {rule}")
        simple = math.sqrt(eps ** 2 + theta ** 2)
        steps.append(f"   Для сравнения, упрощённая формула учебных практикумов √(ε² + θ²) = {F(simple)}{u}")
    steps.append(f"   ▸ Δ = {F(delta)}{u},   относительная погрешность δ = Δ/|x̄| = "
                 f"{F(100 * delta / abs(mean), 3) if mean else '—'} %")

    line, v_r, e_r = _result_line(name, mean, delta, unit, P)
    steps += ["", "🎯 РЕЗУЛЬТАТ ИЗМЕРЕНИЯ"]
    steps.append("   Погрешность округлена до 1–2 значащих цифр (2 — если первая цифра 1 или 2), результат — до того же разряда.")
    steps += box([line] + ([f"δ = {F(100 * delta / abs(mean), 2)} %"] if mean else []), "answer")

    sc = new_scene2d(equal=False, title=f"Ряд измерений {name}")
    sc['xlabel'], sc['ylabel'] = "номер измерения", f"{name}{(', ' + unit) if unit else ''}"
    idx_all = np.arange(1, len(x_all) + 1)
    keep = np.ones(len(x_all), bool)
    rem = list(excluded)
    for i, v in enumerate(x_all):
        if v in rem:
            keep[i] = False
            rem.remove(v)
    sc['scatter'].append((idx_all[keep], x_all[keep], "измерения", COL_MAIN))
    if excluded:
        sc['scatter'].append((idx_all[~keep], x_all[~keep], "промахи", COL_RED))
    xb = np.array([0.5, len(x_all) + 0.5])
    sc['bands'].append((xb, [mean - delta] * 2, [mean + delta] * 2, f"x̄ ± Δ (P = {P:g})", COL_GREEN))
    sc['curves'].append((xb, [mean, mean], "среднее x̄", COL_GREEN))
    sc['curves'].append((xb, [mean - S] * 2, "x̄ ± S", COL_GRAY, '--'))
    sc['curves'].append((xb, [mean + S] * 2, "", COL_GRAY, '--'))

    return {'n': n, 'mean': mean, 'S': S, 'S_mean': S_mean, 't': t, 'eps': eps, 'delta': delta,
            'excluded': excluded, 'rule': rule, 'result': line, 'value_str': v_r, 'error_str': e_r,
            'steps': "\n".join(steps), 'plot2d': sc}


# =============================================================================
# Косвенные измерения
# =============================================================================

_VAR_RE = re.compile(
    r'^\s*([A-Za-z_]\w*)\s*[=:\s]\s*([-+]?[\d.,]+(?:[eE][-+]?\d+)?)\s*(?:±|\+-|\+/-|\s)\s*([\d.,]+(?:[eE][-+]?\d+)?)\s*(%)?\s*$')


def parse_quantities(text: str) -> Dict[str, Tuple[float, float]]:
    """Строки вида «L = 1.000 ± 0.002», «T 2.006 0.005», «R = 100 ± 1%». Возвращает {имя: (значение, Δ)}."""
    out: Dict[str, Tuple[float, float]] = {}
    for ln, line in enumerate(str(text).splitlines(), 1):
        if not line.strip() or line.strip().startswith('#'):
            continue
        m = _VAR_RE.match(line.replace('−', '-'))
        if not m:
            raise ValueError(f"Строка {ln}: «{line.strip()}». Формат: имя = значение ± погрешность (например, L = 1.000 ± 0.002)")
        name, val, err, pct = m.groups()
        v = float(val.replace(',', '.'))
        e = float(err.replace(',', '.'))
        if pct:
            e = abs(v) * e / 100
        out[name] = (v, e)
    if not out:
        raise ValueError("Не заданы величины: укажите по строке на каждую, например L = 1.000 ± 0.002")
    return out


def indirect_measurement(formula: str, quantities_text: str, unit: str = "", P: float = 0.95) -> Dict[str, Any]:
    """Погрешность косвенного измерения y = f(x₁, …, xₖ) для независимых x с погрешностями Δxᵢ (при одной P)."""
    q = parse_quantities(quantities_text)
    m = re.match(r'^\s*([A-Za-z_]\w*)\s*=(?!=)', formula)
    res_name = m.group(1) if m else "y"
    expr = parse_expression(formula, variables=list(q))
    used = [n for n in q if sp.Symbol(n, real=True) in expr.free_symbols]
    unused = [n for n in q if n not in used]
    if not used:
        raise ValueError("Формула не зависит ни от одной из заданных величин")
    syms = {n: sp.Symbol(n, real=True) for n in q}
    subs = {syms[n]: q[n][0] for n in q}
    value = float(sp.N(expr.subs(subs)))
    if not math.isfinite(value):
        raise ValueError("Значение функции не определено при заданных величинах")

    rows, contrib = [], []
    steps = ["📌 ЭТАП 1. ФОРМУЛА И ИСХОДНЫЕ ДАННЫЕ"]
    steps += box([f"{res_name} = {sp.sstr(expr)}"])
    for n in q:
        v, e = q[n]
        steps.append(f"   ▸ {n} = {F(v)} ± {F(e)}   (δ = {F(100 * e / abs(v), 3) if v else '—'} %)")
    if unused:
        steps.append(f"   Величины {', '.join(unused)} в формулу не входят и не учитываются.")
    steps += ["", "📝 ЭТАП 2. ЧАСТНЫЕ ПРОИЗВОДНЫЕ (символьно) И ВКЛАДЫ В ПОГРЕШНОСТЬ"]
    steps += box([
        f"Δ{res_name} = √( Σ (∂f/∂xᵢ · Δxᵢ)² )   — независимые погрешности при одной доверительной вероятности",
        f"δ{res_name} = Δ{res_name} / |{res_name}|",
    ])
    for n in used:
        d = sp.simplify(sp.diff(expr, syms[n]))
        dv = float(sp.N(d.subs(subs)))
        c = dv * q[n][1]
        contrib.append(c)
        rows.append((n, F(dv, 5), F(q[n][1], 4), F(abs(c), 4)))
        steps.append(f"   ▸ ∂{res_name}/∂{n} = {sp.sstr(d)} = {F(dv, 6)}")
    tot2 = sum(c * c for c in contrib)
    delta = math.sqrt(tot2)
    worst = sum(abs(c) for c in contrib)
    shares = [100 * c * c / tot2 if tot2 else 0 for c in contrib]
    rows = [r + (F(sh, 3) + " %",) for r, sh in zip(rows, shares)]
    steps += box(table_lines(("xᵢ", "∂f/∂xᵢ", "Δxᵢ", "|∂f/∂xᵢ·Δxᵢ|", "доля в Δ²"), rows))
    dominant = used[int(np.argmax(shares))]
    steps.append(f"   Наибольший вклад даёт {dominant} ({F(max(shares), 3)} % дисперсии) — уточнять в первую очередь его.")

    steps += ["", "⚙️ ЭТАП 3. ЗНАЧЕНИЕ И ПОГРЕШНОСТЬ"]
    steps.append(f"   ▸ {res_name} = {F(value, 8)}")
    steps.append(f"   ▸ Δ{res_name} = √({' + '.join(F(c * c, 4) for c in contrib)}) = {F(delta)}")
    steps.append(f"   ▸ Граничная (наихудшая) оценка Σ|∂f/∂xᵢ·Δxᵢ| = {F(worst)}")
    rel = 100 * delta / abs(value) if value else float('nan')
    steps.append(f"   ▸ δ{res_name} = {F(rel, 3)} %")
    line, v_r, e_r = _result_line(res_name, value, delta, unit, P)
    steps += ["", "🎯 РЕЗУЛЬТАТ"]
    steps += box([line, f"δ = {F(rel, 2)} %"], "answer")

    sc = new_scene2d(equal=False, title=f"Вклад величин в погрешность {res_name}, % от Δ²")
    sc['bars'] = (used, shares, COL_AMBER)
    sc['ylabel'] = "%"
    return {'value': value, 'delta': delta, 'relative': rel, 'worst': worst, 'shares': dict(zip(used, shares)),
            'result': line, 'steps': "\n".join(steps), 'plot2d': sc}


# =============================================================================
# Аппроксимация методом наименьших квадратов
# =============================================================================

MODELS = {
    "Линейная  y = a + b·x": ("a + b*x", ["a", "b"]),
    "Пропорциональность  y = b·x": ("b*x", ["b"]),
    "Квадратичная  y = a + b·x + c·x²": ("a + b*x + c*x^2", ["a", "b", "c"]),
    "Кубическая  y = a + b·x + c·x² + d·x³": ("a + b*x + c*x^2 + d*x^3", ["a", "b", "c", "d"]),
    "Экспонента  y = a·exp(b·x)": ("a*exp(b*x)", ["a", "b"]),
    "Экспонента со смещением  y = a·exp(b·x) + c": ("a*exp(b*x) + c", ["a", "b", "c"]),
    "Степенная  y = a·x^b": ("a*x^b", ["a", "b"]),
    "Логарифмическая  y = a + b·ln x": ("a + b*ln(x)", ["a", "b"]),
    "Своя формула": (None, None),
}
LINEAR_IN_PARAMS = {"Линейная  y = a + b·x", "Пропорциональность  y = b·x", "Квадратичная  y = a + b·x + c·x²",
                    "Кубическая  y = a + b·x + c·x² + d·x³", "Логарифмическая  y = a + b·ln x"}
PARAM_NAMES = ["a", "b", "c", "d", "k", "m", "A", "B", "C", "D", "x0", "w", "tau", "phi"]


def _initial_guess(model: str, x: np.ndarray, y: np.ndarray, names: Sequence[str]) -> List[float]:
    if model.startswith("Экспонента") and np.all(y > 0):
        b, la = np.polyfit(x, np.log(y), 1)
        g = {'a': math.exp(la), 'b': b, 'c': 0.0}
        return [g[n] for n in names]
    if model.startswith("Экспонента со смещением"):
        return [float(y.max() - y.min()) or 1.0, -1.0 / (float(np.ptp(x)) or 1.0), float(y.min())]
    if model.startswith("Степенная") and np.all(x > 0) and np.all(y > 0):
        b, la = np.polyfit(np.log(x), np.log(y), 1)
        return [math.exp(la), b]
    return [1.0] * len(names)


def _parse_guess(text: str, names: Sequence[str], strict: bool = True) -> Dict[str, float]:
    """Разбор «a = 1; b = 0.5». strict=False — параметры, которых нет в модели, пропускаются."""
    out = {}
    for part in re.split(r'[;\n]+|,\s+(?=[A-Za-z])', str(text or "")):
        part = part.strip()
        if not part:
            continue
        m = re.match(r'^([A-Za-z_]\w*)\s*=\s*(.+)$', part)
        if not m:
            raise ValueError(f"Начальное приближение «{part}»: формат a = 1; b = 0.5")
        if m.group(1) not in names:
            if not strict:
                continue
            raise ValueError(f"Параметр {m.group(1)} не встречается в формуле")
        out[m.group(1)] = float(m.group(2).replace(',', '.'))
    return out


def least_squares_fit(data_text: str, model: str, custom_formula: str = "", guess_text: str = "",
                      P: float = 0.95) -> Dict[str, Any]:
    """МНК-аппроксимация данных (x, y[, σy]). Возвращает параметры, их доверительные интервалы и качество."""
    from scipy import optimize

    table, headers = parse_table(data_text, min_cols=2)
    x, y = table[:, 0], table[:, 1]
    sigma = table[:, 2] if table.shape[1] >= 3 else None
    if sigma is not None and np.any(sigma <= 0):
        raise ValueError("Погрешности σy (3-й столбец) должны быть положительными")
    n = len(x)
    xn = headers[0] if len(headers) >= 2 else "x"
    yn = headers[1] if len(headers) >= 2 else "y"

    if model not in MODELS:
        raise ValueError(f"Неизвестная модель «{model}»")
    if model == "Своя формула":
        if not custom_formula.strip():
            raise ValueError("Введите формулу модели, например a*exp(-b*x) + c")
        probe = parse_expression(custom_formula, variables=['x'], extra=PARAM_NAMES)
        names = [p for p in PARAM_NAMES if sp.Symbol(p, real=True) in probe.free_symbols]
        if not names:
            raise ValueError("В формуле нет параметров. Используйте имена a, b, c, d, k, m, A, B, C, D, x0, w, tau, phi")
        expr = probe
        formula_txt = custom_formula.strip()
    else:
        formula_txt, names = MODELS[model]
        expr = parse_expression(formula_txt, variables=['x'], extra=names)
    p = len(names)
    if n <= p:
        raise ValueError(f"Точек ({n}) должно быть больше, чем параметров модели ({p})")
    if "ln x" in model and np.any(x <= 0):
        raise ValueError("Логарифмическая модель требует x > 0")
    if model.startswith("Степенная") and np.any(x <= 0):
        raise ValueError("Степенная модель требует x > 0")

    syms = [sp.Symbol('x', real=True)] + [sp.Symbol(nm, real=True) for nm in names]
    f_np = sp.lambdify(syms, expr, 'numpy')
    jac_exprs = [sp.diff(expr, s_) for s_ in syms[1:]]
    jac_np = [sp.lambdify(syms, j, 'numpy') for j in jac_exprs]

    def model_f(xx, *params):
        with np.errstate(all='ignore'):
            return np.broadcast_to(np.asarray(f_np(xx, *params), dtype=float), np.shape(xx)).astype(float)

    def jacobian(xx, params):
        cols = []
        for j in jac_np:
            with np.errstate(all='ignore'):
                cols.append(np.broadcast_to(np.asarray(j(xx, *params), dtype=float), np.shape(xx)))
        return np.column_stack(cols)

    steps: List[str] = ["📌 ЭТАП 1. ДАННЫЕ И МОДЕЛЬ"]
    steps.append(f"   ▸ Точек n = {n},  параметров p = {p},  степеней свободы ν = n − p = {n - p}")
    steps.append(f"   ▸ Модель: y = {formula_txt}")
    steps.append("   ▸ Погрешности σy заданы (3-й столбец) — взвешенный МНК, веса 1/σ²" if sigma is not None
                 else "   ▸ Погрешности y не заданы — обычный МНК (σ оценивается по остаткам)")

    linear_simple = model == "Линейная  y = a + b·x" and sigma is None
    if linear_simple:
        Sx, Sy, Sxx, Sxy = x.sum(), y.sum(), (x * x).sum(), (x * y).sum()
        D = n * Sxx - Sx ** 2
        if abs(D) < 1e-300:
            raise ValueError("Все x одинаковы — прямую построить нельзя")
        b = (n * Sxy - Sx * Sy) / D
        a = (Sy - b * Sx) / n
        popt = np.array([a, b])
        resid = y - (a + b * x)
        s2 = (resid ** 2).sum() / (n - 2)
        pcov = np.array([[s2 * Sxx / D, -s2 * Sx / D], [-s2 * Sx / D, s2 * n / D]])
        steps += ["", "📝 ЭТАП 2. МНК ДЛЯ ПРЯМОЙ (формулы)"]
        steps += box([
            "b = (n·Σxy − Σx·Σy) / (n·Σx² − (Σx)²),     a = (Σy − b·Σx) / n",
            "s² = Σ(yᵢ − a − b·xᵢ)² / (n − 2),   S_b = √(n·s²/D),   S_a = √(s²·Σx²/D),   D = n·Σx² − (Σx)²",
        ])
        steps += [f"   ▸ Σx = {F(Sx)},  Σy = {F(Sy)},  Σx² = {F(Sxx)},  Σxy = {F(Sxy)},  D = {F(D)}",
                  f"   ▸ b = {F(b, 8)},   a = {F(a, 8)},   s² = {F(s2)}"]
        method = "аналитическое решение нормальных уравнений"
    else:
        user_guess = _parse_guess(guess_text, names, strict=model == "Своя формула")
        p0 = _initial_guess(model, x, y, names)
        p0 = [user_guess.get(nm, g) for nm, g in zip(names, p0)]
        if model in LINEAR_IN_PARAMS:
            A = jacobian(x, np.ones(p))
            w = 1 / sigma if sigma is not None else np.ones(n)
            popt, *_ = np.linalg.lstsq(A * w[:, None], y * w, rcond=None)
            method = "линейный МНК (модель линейна по параметрам)"
        else:
            try:
                popt, _ = optimize.curve_fit(model_f, x, y, p0=p0, sigma=sigma, absolute_sigma=sigma is not None,
                                             maxfev=20000)
            except (RuntimeError, ValueError) as ex:
                raise ValueError(f"Итерации не сошлись ({ex}). Задайте начальные приближения параметров ближе к ожидаемым.") from None
            method = "нелинейный МНК (метод Левенберга — Марквардта), начальное приближение " + \
                     ", ".join(f"{nm} = {F(g, 4)}" for nm, g in zip(names, p0))
        resid = y - model_f(x, *popt)
        J = jacobian(x, popt)
        Wv = 1 / sigma ** 2 if sigma is not None else np.ones(n)
        JtWJ = J.T @ (J * Wv[:, None])
        try:
            cov = np.linalg.inv(JtWJ)
        except np.linalg.LinAlgError:
            raise ValueError("Параметры модели неразличимы по этим данным (вырожденная матрица). Упростите модель.") from None
        if sigma is None:
            s2 = (resid ** 2).sum() / (n - p)
            pcov = cov * s2
        else:
            pcov = cov
        steps += ["", "📝 ЭТАП 2. МИНИМИЗАЦИЯ СУММЫ КВАДРАТОВ ОТКЛОНЕНИЙ"]
        steps.append(f"   Метод: {method}.")
        steps.append("   Ковариационная матрица параметров: C = (Jᵀ·W·J)⁻¹" + ("" if sigma is not None else " · s²,  s² = Σe²/(n − p)"))

    se = np.sqrt(np.clip(np.diag(pcov), 0, None))
    t = student_t(P, n - p)
    ci = t * se
    ss_res = float((resid ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float('nan')
    r2_adj = 1 - (1 - r2) * (n - 1) / (n - p) if ss_tot > 0 else float('nan')
    rmse = math.sqrt(ss_res / n)
    chi2 = float(((resid / sigma) ** 2).sum()) if sigma is not None else None

    steps += ["", "⚙️ ЭТАП 3. ПАРАМЕТРЫ И ИХ ДОВЕРИТЕЛЬНЫЕ ИНТЕРВАЛЫ"]
    steps.append(f"   t({P:g}; ν = {n - p}) = {F(t, 5)};  Δ = t · S")
    prow, answer = [], []
    for nm, v, s_, d in zip(names, popt, se, ci):
        vr, dr, _ = round_measurement(float(v), float(d))
        prow.append((nm, F(float(v), 7), F(float(s_), 4), F(float(d), 4), f"{vr} ± {dr}"))
        answer.append(f"{nm} = {vr} ± {dr}")
    steps += box(table_lines(("параметр", "оценка", "S", "Δ (P)", "результат"), prow))
    if p >= 2:
        corr = pcov / np.outer(se, se) if np.all(se > 0) else None
        if corr is not None:
            strong = [(names[i], names[j], corr[i, j]) for i in range(p) for j in range(i + 1, p) if abs(corr[i, j]) > 0.95]
            for a_, b_, c_ in strong:
                steps.append(f"   Внимание: параметры {a_} и {b_} сильно коррелированы (r = {F(c_, 3)}) — их оценки неустойчивы.")

    steps += ["", "📍 ЭТАП 4. КАЧЕСТВО АППРОКСИМАЦИИ"]
    steps.append(f"   ▸ R² = 1 − SS_ост/SS_полн = {F(r2, 6)},   R²_скорр = {F(r2_adj, 6)}")
    steps.append(f"   ▸ СКО остатков RMSE = √(Σe²/n) = {F(rmse)}")
    if model == "Линейная  y = a + b·x":
        r = np.corrcoef(x, y)[0, 1]
        steps.append(f"   ▸ Коэффициент корреляции Пирсона r = {F(r, 6)}")
    if chi2 is not None:
        steps.append(f"   ▸ χ² = Σ(eᵢ/σᵢ)² = {F(chi2, 5)},   χ²/ν = {F(chi2 / (n - p), 4)}  "
                     "(≈ 1 — модель согласуется с данными в пределах погрешностей; ≫ 1 — нет)")
    pred = model_f(x, *popt)
    rows = [(F(xi, 6), F(yi, 6), F(fi, 6), F(ei, 4)) for xi, yi, fi, ei in zip(x, y, pred, resid)]
    steps.append("   Остатки:")
    steps += box(table_lines((xn, yn, "ŷ", "e = y − ŷ"), rows, max_rows=20))

    num_expr = expr.subs({sp.Symbol(nm, real=True): sp.Float(float(v), 5) for nm, v in zip(names, popt)})
    eq = re.sub(r'(\d)([A-Za-z]{2,})', r'\1·\2', to_pretty_math(sp.sstr(sp.N(num_expr, 5))))
    steps += ["", "🎯 РЕЗУЛЬТАТ"]
    steps += box([f"y = {formula_txt}"] + answer + [f"R² = {F(r2, 5)},  P = {P:g}"], "answer")

    # график: данные, кривая, доверительная полоса кривой
    span = float(np.ptp(x))
    xs = np.linspace(float(x.min()) - 0.03 * span, float(x.max()) + 0.03 * span, 400)
    if "ln x" in model or model.startswith("Степенная"):
        xs = xs[xs > 0]
    ys = model_f(xs, *popt)
    Jg = jacobian(xs, popt)
    var = np.einsum('ij,jk,ik->i', Jg, pcov, Jg)
    band = t * np.sqrt(np.clip(var, 0, None))
    sc = new_scene2d(equal=False, title="Аппроксимация МНК")
    sc['xlabel'], sc['ylabel'] = xn, yn
    sc['bands'].append((xs, ys - band, ys + band, f"доверительная полоса P = {P:g}", COL_GREEN))
    sc['curves'].append((xs, ys, f"y = {eq}", COL_GREEN))
    if sigma is not None:
        sc['errorbars'].append((x, y, sigma, None, "данные ± σ", COL_MAIN))
    else:
        sc['scatter'].append((x, y, "данные", COL_MAIN))

    return {'params': dict(zip(names, map(float, popt))), 'se': dict(zip(names, map(float, se))),
            'ci': dict(zip(names, map(float, ci))), 'r2': r2, 'r2_adj': r2_adj, 'rmse': rmse, 'chi2': chi2,
            'equation': eq, 'steps': "\n".join(steps), 'plot2d': sc}


# =============================================================================
# Табличная функция
# =============================================================================

def tabular_function(data_text: str, points_text: str = "", method: str = "Кубический сплайн") -> Dict[str, Any]:
    """Интерполяция в точках, численная производная, интеграл табличной функции y(x)."""
    from scipy import integrate, interpolate

    table, headers = parse_table(data_text, min_cols=2)
    x, y = table[:, 0], table[:, 1]
    xn = headers[0] if len(headers) >= 2 else "x"
    yn = headers[1] if len(headers) >= 2 else "y"
    steps: List[str] = ["📌 ЭТАП 1. ДАННЫЕ"]
    order = np.argsort(x, kind='stable')
    if np.any(order != np.arange(len(x))):
        steps.append("   Точки отсортированы по возрастанию x.")
        x, y = x[order], y[order]
    if np.any(np.diff(x) == 0):
        raise ValueError("Есть повторяющиеся значения x — табличная функция должна быть однозначной")
    n = len(x)
    if n < 2:
        raise ValueError("Нужно хотя бы две точки")
    steps.append(f"   ▸ n = {n},  x ∈ [{F(x[0])}; {F(x[-1])}]" +
                 ("  (шаг постоянный h = " + F(x[1] - x[0]) + ")" if np.allclose(np.diff(x), x[1] - x[0]) else "  (шаг переменный)"))

    if method == "Кубический сплайн" and n >= 3:
        interp = interpolate.CubicSpline(x, y, bc_type='natural')
        mdesc = "естественный кубический сплайн (непрерывны y, y′, y″; y″ = 0 на концах)"
    else:
        interp = interpolate.interp1d(x, y, kind='linear')
        mdesc = "кусочно-линейная интерполяция"
        method = "Линейная"

    steps += ["", "📝 ЭТАП 2. ИНТЕРПОЛЯЦИЯ"]
    steps.append(f"   Метод: {mdesc}.")
    interp_rows, ipts = [], []
    if str(points_text).strip():
        pts = parse_series(points_text)
        for xp in pts:
            if xp < x[0] or xp > x[-1]:
                interp_rows.append((F(xp), "вне диапазона"))
                continue
            yp = float(interp(xp))
            ipts.append((float(xp), yp))
            interp_rows.append((F(xp), F(yp, 7)))
        steps += box(table_lines((xn, f"{yn} (интерп.)"), interp_rows))
    else:
        steps.append("   Точки для интерполяции не заданы.")

    steps += ["", "⚙️ ЭТАП 3. ЧИСЛЕННАЯ ПРОИЗВОДНАЯ"]
    steps += box(["Внутренние точки: y′ᵢ ≈ центральная разность второго порядка (учитывает неравный шаг);",
                  "крайние точки — односторонние разности второго порядка (numpy.gradient)."])
    dy = np.gradient(y, x, edge_order=2 if n >= 3 else 1)
    steps += box(table_lines((xn, yn, f"d{yn}/d{xn}"), [(F(a), F(b), F(c, 5)) for a, b, c in zip(x, y, dy)], max_rows=25))

    steps += ["", "📍 ЭТАП 4. ИНТЕГРАЛ ПО ВСЕМУ ДИАПАЗОНУ"]
    trap = float(integrate.trapezoid(y, x))
    simp_ = float(integrate.simpson(y, x=x)) if n >= 3 else float('nan')
    spl_int = float(interp.integrate(x[0], x[-1])) if method == "Кубический сплайн" else trap
    steps += box(["Трапеции:  I ≈ Σ (yᵢ + yᵢ₊₁)/2 · (xᵢ₊₁ − xᵢ)",
                  "Симпсон:   парабола через каждые три точки (при нечётном числе отрезков — поправка)"])
    steps.append(f"   ▸ Метод трапеций: I = {F(trap, 8)}")
    if n >= 3:
        steps.append(f"   ▸ Метод Симпсона: I = {F(simp_, 8)}")
        if method == "Кубический сплайн":
            steps.append(f"   ▸ Интеграл от сплайна: I = {F(spl_int, 8)}")
        steps.append(f"   Расхождение трапеций и Симпсона {F(abs(trap - simp_), 3)} — ориентир точности по сетке.")
    steps += ["", "🎯 РЕЗУЛЬТАТ"]
    best = simp_ if n >= 3 else trap
    steps += box([f"∫ {yn} d{xn} от {F(x[0])} до {F(x[-1])} ≈ {F(best, 7)}" + ("  (Симпсон)" if n >= 3 else "  (трапеции)")], "answer")

    xs = np.linspace(x[0], x[-1], 500)
    ys = interp(xs)
    sc = new_scene2d(equal=False, title="Табличная функция")
    sc['xlabel'], sc['ylabel'] = xn, yn
    sc['bands'].append((xs, np.minimum(0, ys), np.maximum(0, ys), "площадь (интеграл)", COL_AMBER))
    sc['curves'].append((xs, ys, "сплайн" if method == "Кубический сплайн" else "линейная интерполяция", COL_GREEN))
    sc['scatter'].append((x, y, "данные", COL_MAIN))
    for (xp, yp) in ipts:
        sc['points'].append((xp, yp, "", COL_RED))
    return {'trapezoid': trap, 'simpson': simp_, 'derivative': dy, 'interpolated': ipts,
            'steps': "\n".join(steps), 'plot2d': sc}
