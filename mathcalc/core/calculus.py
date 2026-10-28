"""
Математический анализ: пределы, производные (в т.ч. частные, градиент, гессиан, якобиан),
экстремумы функций нескольких переменных, интегралы (неопределённые с пошаговым решением,
определённые, несобственные, кратные), ряды Тейлора, числовые ряды.

Аналитический результат SymPy сопровождается численной проверкой (SciPy / прямой расчёт),
чтобы ответ можно было проверить независимым способом.
"""

import dataclasses
import math
from typing import Any, Dict, List

import numpy as np
import sympy as sp

from .common import box, COL_AMBER, COL_GRAY, COL_GREEN, COL_MAIN, COL_RED
from .data import fmt_float, table_lines
from .expr import parse_bound, parse_expression, symbols, to_numpy
from .functions import pretty, sample
from .result import new_scene2d

F = fmt_float
X = sp.Symbol('x', real=True)


def _num(e) -> float:
    return float(sp.N(e, 20))


def _is_finite_number(v) -> bool:
    return isinstance(v, sp.Expr) and not isinstance(v, sp.AccumBounds) and v.is_number and v.is_finite is True \
        and v.is_real is not False


def _approx(e) -> str:
    """Точное значение и приближение: «√2/2 ≈ 0.7071068»."""
    if e in (sp.oo, -sp.oo, sp.zoo):
        return "+∞" if e == sp.oo else ("−∞" if e == -sp.oo else "∞")
    if isinstance(e, sp.AccumBounds):
        return f"не существует (значения колеблются в [{pretty(e.min)}; {pretty(e.max)}])"
    if not e.is_number:
        return pretty(e)
    if e.is_Integer:
        return str(e)
    try:
        val = complex(sp.N(e, 15))
        if abs(val.imag) > 1e-12:
            return f"{pretty(e)} ≈ {F(val.real, 7)} + {F(val.imag, 7)}i"
        return f"{pretty(e)} ≈ {F(val.real, 7)}" if not e.is_Float else F(val.real, 7)
    except (TypeError, ValueError):
        return pretty(e)


# =============================================================================
# Пределы
# =============================================================================

def _kind(v) -> str:
    if v == 0:
        return "0"
    if v in (sp.oo, -sp.oo, sp.zoo) or (hasattr(v, 'is_infinite') and v.is_infinite):
        return "∞"
    if v == 1:
        return "1"
    return "c"


def limit(f_text: str, point_text: str, direction: str = "двусторонний") -> Dict[str, Any]:
    f = parse_expression(f_text, ['x'])
    x0 = parse_bound(point_text)
    dirs = {"двусторонний": "+-", "справа (x → a+0)": "+", "слева (x → a−0)": "-"}
    d = dirs.get(direction, "+-")
    at = "+∞" if x0 == sp.oo else ("−∞" if x0 == -sp.oo else pretty(x0))
    arrow = {"+-": "", "+": "+0", "-": "−0"}[d] if x0.is_finite else ""
    steps = [f"📌 ПРЕДЕЛ  lim (x → {at}{arrow})  {pretty(f)}"]

    # 1. подстановка
    steps += ["", "📝 1. НЕПОСРЕДСТВЕННАЯ ПОДСТАНОВКА"]
    direct = None
    if x0.is_finite:
        try:
            v = sp.simplify(f.subs(X, x0))
            if _is_finite_number(v) and v.is_real:
                direct = v
                steps.append(f"   f({pretty(x0)}) = {_approx(v)} — функция непрерывна в точке, предел равен значению.")
            else:
                steps.append(f"   Подстановка даёт «{pretty(v)}» — требуется раскрытие неопределённости.")
        except Exception:
            steps.append("   Подстановка невозможна.")
    else:
        steps.append("   Предел на бесконечности — определяем тип выражения.")

    # 2. тип неопределённости и правило Лопиталя
    lhopital_used = False
    if direct is None:
        num_, den = sp.fraction(sp.together(f))
        lim_dir = '+' if d == '+-' else d
        try:
            ln, ld = sp.limit(num_, X, x0, lim_dir), sp.limit(den, X, x0, lim_dir)
            kind = f"{_kind(ln)}/{_kind(ld)}"
        except Exception:
            ln = ld = None
            kind = "?"
        steps += ["", "📝 2. ТИП НЕОПРЕДЕЛЁННОСТИ"]
        if den != 1 and kind in ("0/0", "∞/∞"):
            steps.append(f"   Числитель → {pretty(ln)}, знаменатель → {pretty(ld)}: неопределённость вида «{kind}».")
            steps += ["", "⚙️ 3. ПРАВИЛО ЛОПИТАЛЯ"]
            steps += box(["lim f/g = lim f′/g′, если предел справа существует (неопределённость 0/0 или ∞/∞)"])
            p_, q_ = num_, den
            for it in range(1, 4):
                p_, q_ = sp.simplify(sp.diff(p_, X)), sp.simplify(sp.diff(q_, X))
                steps.append(f"   Шаг {it}:  ({pretty(p_)}) / ({pretty(q_)})")
                try:
                    lp, lq = sp.limit(p_, X, x0, lim_dir), sp.limit(q_, X, x0, lim_dir)
                except Exception:
                    break
                k2 = f"{_kind(lp)}/{_kind(lq)}"
                if k2 not in ("0/0", "∞/∞"):
                    steps.append(f"   Числитель → {pretty(lp)}, знаменатель → {pretty(lq)} — неопределённость раскрыта.")
                    lhopital_used = True
                    break
                steps.append(f"   Снова «{k2}» — применяем правило ещё раз.")
        else:
            if den == 1 or kind not in ("0/0", "∞/∞"):
                steps.append("   Выражение не является дробью вида 0/0 или ∞/∞ "
                             "(возможны «0·∞», «∞ − ∞», «1^∞», колебания). Используется общий алгоритм SymPy "
                             "(разложение в ряд в окрестности точки, алгоритм Грунца).")
            if x0.is_finite:
                try:
                    ser = sp.series(f, X, x0, 3).removeO()
                    steps.append(f"   Разложение в окрестности x = {pretty(x0)}:  f ≈ {pretty(ser)} + …")
                except Exception:
                    pass

    # 3. ответ
    if d == "+-" and x0.is_finite:
        lr, ll = sp.limit(f, X, x0, '+'), sp.limit(f, X, x0, '-')
        if sp.simplify(lr - ll) == 0 if (_is_finite_number(lr) and _is_finite_number(ll)) else lr == ll:
            result = lr
            one_sided = None
        else:
            result = None
            one_sided = (ll, lr)
    else:
        result = sp.limit(f, X, x0, d if d != "+-" else '+')
        one_sided = None

    steps += ["", "📍 ЧИСЛЕННАЯ ПРОВЕРКА"]
    fn = to_numpy(f, ['x'])
    rows = []
    if x0.is_finite:
        x0f = _num(x0)
        for h in (1e-1, 1e-2, 1e-3, 1e-4, 1e-5):
            l_ = fn(np.array([x0f - h]))[0] if d in ("+-", "-") else np.nan
            r_ = fn(np.array([x0f + h]))[0] if d in ("+-", "+") else np.nan
            rows.append((F(h), F(l_, 8), F(r_, 8)))
        steps += box(table_lines(("h", "f(a − h)", "f(a + h)"), rows))
    else:
        sgn = 1 if x0 == sp.oo else -1
        for xv in (10.0, 100.0, 1e3, 1e4, 1e6):
            rows.append((F(sgn * xv), F(fn(np.array([sgn * xv]))[0], 8)))
        steps += box(table_lines(("x", "f(x)"), rows))

    steps += ["", "🎯 ОТВЕТ"]
    if result is not None:
        ans = f"lim = {_approx(result)}"
    else:
        ans = f"Предел не существует: слева {_approx(one_sided[0])}, справа {_approx(one_sided[1])}"
    steps += box([ans], "answer")

    sc = None
    if x0.is_finite:
        x0f = _num(x0)
        w = max(1.0, abs(x0f) * 0.5)
        xs, ys = sample(f, x0f - w, x0f + w, 2001)
        sc = new_scene2d(equal=False, title=f"y = {pretty(f)} около x = {at}")
        sc['curves'].append((xs, ys, "", COL_MAIN))
        if result is not None and _is_finite_number(result):
            sc['points'].append((x0f, _num(result), "предел", COL_RED))
        sc['lines'].append((x0f, 0.0, 0.0, 1.0, "", COL_GRAY))
    else:
        sgn = 1 if x0 == sp.oo else -1
        xs = np.linspace(1, 60, 3000) * sgn
        xs = np.sort(xs)
        ys = fn(xs)
        sc = new_scene2d(equal=False, title=f"y = {pretty(f)} при x → {at}")
        sc['curves'].append((xs, ys, "", COL_MAIN))
        if result is not None and _is_finite_number(result):
            sc['curves'].append((xs, np.full_like(xs, _num(result)), f"y = {pretty(result)}", COL_RED, '--'))
    return {'result': result, 'one_sided': one_sided, 'lhopital': lhopital_used, 'steps': "\n".join(steps), 'plot2d': sc}


# =============================================================================
# Производные
# =============================================================================

def derivative(f_text: str, order: int = 1, point_text: str = "") -> Dict[str, Any]:
    f = parse_expression(f_text, ['x'])
    if order < 1 or order > 10:
        raise ValueError("Порядок производной: от 1 до 10")
    steps = [f"📌 ФУНКЦИЯ  y = {pretty(f)}"]
    derivs = [f]
    steps += ["", "📝 ПРОИЗВОДНЫЕ"]
    for k in range(1, order + 1):
        raw = sp.diff(derivs[-1], X)
        simp_ = sp.simplify(raw)
        derivs.append(simp_)
        mark = "′" * k if k <= 3 else f"⁽{k}⁾"
        line = f"y{mark} = {pretty(simp_)}"
        if sp.count_ops(raw) < 2 * sp.count_ops(simp_) + 20 and sp.srepr(raw) != sp.srepr(simp_):
            steps.append(f"   До упрощения: y{mark} = {pretty(raw)}")
        steps += box([line])
    values = {}
    sc = new_scene2d(equal=False, title=f"y = {pretty(f)}")
    sc['xlabel'], sc['ylabel'] = "x", "y"
    if str(point_text).strip():
        x0 = parse_bound(point_text)
        if not x0.is_finite:
            raise ValueError("Точка должна быть конечной")
        steps += ["", f"⚙️ ЗНАЧЕНИЯ В ТОЧКЕ x₀ = {pretty(x0)}"]
        for k, dk in enumerate(derivs):
            v = sp.simplify(dk.subs(X, x0))
            values[k] = v
            name = "y" + ("′" * k if k <= 3 else f"⁽{k}⁾")
            steps.append(f"   ▸ {name}({pretty(x0)}) = {_approx(v)}")
        y0, k1 = values[0], values.get(1)
        if k1 is not None and _is_finite_number(k1) and _is_finite_number(y0):
            tangent = sp.expand(y0 + k1 * (X - x0))
            steps += ["", "📍 КАСАТЕЛЬНАЯ И НОРМАЛЬ"]
            steps += box(["Касательная: y = f(x₀) + f′(x₀)·(x − x₀)", "Нормаль:     y = f(x₀) − (x − x₀)/f′(x₀)"])
            ans = [f"касательная: y = {pretty(tangent)}"]
            if k1 != 0:
                normal = sp.expand(y0 - (X - x0) / k1)
                ans.append(f"нормаль: y = {pretty(normal)}")
            else:
                ans.append(f"нормаль: x = {pretty(x0)}")
            ans.append(f"угол наклона касательной: arctg({pretty(k1)}) ≈ {F(math.degrees(math.atan(_num(k1))), 5)}°")
            steps += box(ans, "answer")
            x0f = _num(x0)
            sc['curves'].append((np.array([x0f - 3, x0f + 3]), _num(y0) + _num(k1) * np.array([-3.0, 3.0]),
                                 "касательная", COL_RED, '--'))
            sc['points'].append((x0f, _num(y0), "x₀", COL_RED))
            a, b = x0f - 4, x0f + 4
        else:
            a, b = -5.0, 5.0
    else:
        a, b = -5.0, 5.0
    xs, ys = sample(f, a, b)
    sc['curves'].insert(0, (xs, ys, "f(x)", COL_MAIN))
    xs1, ys1 = sample(derivs[1], a, b)
    sc['curves'].insert(1, (xs1, ys1, "f′(x)", COL_GREEN))
    return {'derivatives': derivs, 'values': values, 'steps': "\n".join(steps), 'plot2d': sc}


def _parse_vars(text: str) -> List[str]:
    names = [v for v in str(text).replace(',', ' ').replace(';', ' ').split() if v]
    if not names:
        raise ValueError("Укажите переменные, например: x y z")
    for n in names:
        if not n.isidentifier():
            raise ValueError(f"Недопустимое имя переменной «{n}»")
    return names


def _parse_point(text: str, n: int) -> List[sp.Expr]:
    if not str(text).strip():
        return []
    parts = [p for p in str(text).replace(';', ' ').split() if p]
    if len(parts) != n:
        raise ValueError(f"Точка должна иметь {n} координат(ы) через пробел или «;»")
    return [parse_bound(p) for p in parts]


def partial_derivatives(funcs_text: str, vars_text: str, point_text: str = "") -> Dict[str, Any]:
    names = _parse_vars(vars_text)
    syms = symbols(names)
    funcs = [p.strip() for chunk in str(funcs_text).splitlines() for p in chunk.split(';') if p.strip()]
    if not funcs:
        raise ValueError("Введите функцию")
    exprs = [parse_expression(f, names) for f in funcs]
    pt = _parse_point(point_text, len(names))
    subs = dict(zip(syms, pt)) if pt else {}
    steps: List[str] = []
    values: Dict[str, Any] = {}
    if len(exprs) == 1:
        f = exprs[0]
        steps.append(f"📌 ФУНКЦИЯ  f({', '.join(names)}) = {pretty(f)}")
        steps += ["", "📝 ЧАСТНЫЕ ПРОИЗВОДНЫЕ ПЕРВОГО ПОРЯДКА (градиент)"]
        grad = [sp.simplify(sp.diff(f, s_)) for s_ in syms]
        for n, g in zip(names, grad):
            steps.append(f"   ∂f/∂{n} = {pretty(g)}")
        steps += box([f"grad f = ({'; '.join(pretty(g) for g in grad)})"])
        steps += ["", "⚙️ ВТОРЫЕ ПРОИЗВОДНЫЕ — МАТРИЦА ГЕССЕ"]
        H = sp.Matrix([[sp.simplify(sp.diff(f, a, b)) for b in syms] for a in syms])
        rows = [[pretty(H[i, j]) for j in range(len(syms))] for i in range(len(syms))]
        steps += box(table_lines(tuple("∂²f/∂·∂" + n for n in names), rows))
        lap = sp.simplify(sum(H[i, i] for i in range(len(syms))))
        steps.append(f"   Лапласиан Δf = Σ ∂²f/∂xᵢ² = {pretty(lap)}")
        mixed_ok = all(sp.simplify(H[i, j] - H[j, i]) == 0 for i in range(len(syms)) for j in range(i))
        steps.append("   Смешанные производные равны (теорема Шварца выполняется)." if mixed_ok else
                     "   Смешанные производные различаются — функция не дважды непрерывно дифференцируема.")
        if subs:
            steps += ["", f"📍 В ТОЧКЕ ({'; '.join(pretty(p) for p in pt)})"]
            fv = sp.simplify(f.subs(subs))
            gv = [sp.simplify(g.subs(subs)) for g in grad]
            norm = sp.simplify(sp.sqrt(sum(g ** 2 for g in gv)))
            steps.append(f"   ▸ f = {_approx(fv)}")
            steps.append(f"   ▸ grad f = ({'; '.join(_approx(g) for g in gv)})")
            steps.append(f"   ▸ |grad f| = {_approx(norm)} — наибольшая скорость роста функции")
            Hv = H.subs(subs)
            steps.append(f"   ▸ Гессиан: {pretty(Hv.tolist())}")
            values.update(f=fv, grad=gv, hessian=Hv)
        values.update(grad_expr=grad, hessian_expr=H)
    else:
        steps.append(f"📌 ВЕКТОР-ФУНКЦИЯ ({len(exprs)} компонент) от ({', '.join(names)})")
        for i, e in enumerate(exprs, 1):
            steps.append(f"   f{i} = {pretty(e)}")
        J = sp.Matrix([[sp.simplify(sp.diff(e, s_)) for s_ in syms] for e in exprs])
        steps += ["", "📝 МАТРИЦА ЯКОБИ  J = [∂fᵢ/∂xⱼ]"]
        steps += box(table_lines(tuple(f"∂/∂{n}" for n in names), [[pretty(J[i, j]) for j in range(J.cols)] for i in range(J.rows)]))
        if J.rows == J.cols:
            det = sp.simplify(J.det())
            steps.append(f"   Якобиан det J = {pretty(det)}")
            values['det'] = det
        if subs:
            Jv = J.subs(subs)
            steps += ["", f"📍 В ТОЧКЕ ({'; '.join(pretty(p) for p in pt)})", f"   J = {pretty(Jv.tolist())}"]
            if J.rows == J.cols:
                steps.append(f"   det J = {_approx(sp.simplify(Jv.det()))}")
            values['J_point'] = Jv
        values['jacobian'] = J
    return {'values': values, 'steps': "\n".join(steps), 'plot2d': None}


def extrema_multivar(f_text: str, vars_text: str = "x y") -> Dict[str, Any]:
    """Стационарные точки функции нескольких переменных и их тип по матрице Гессе (критерий Сильвестра)."""
    names = _parse_vars(vars_text)
    syms = symbols(names)
    f = parse_expression(f_text, names)
    grad = [sp.simplify(sp.diff(f, s_)) for s_ in syms]
    H = sp.hessian(f, syms)
    steps = [f"📌 ФУНКЦИЯ  f({', '.join(names)}) = {pretty(f)}", "", "📝 1. НЕОБХОДИМОЕ УСЛОВИЕ: grad f = 0"]
    for n, g in zip(names, grad):
        steps.append(f"   ∂f/∂{n} = {pretty(g)} = 0")
    try:
        sols = sp.solve(grad, syms, dict=True)
    except Exception:
        sols = []
    real = []
    for s_ in sols:
        if len(s_) == len(syms) and all(v.is_real is not False and not v.free_symbols for v in s_.values()):
            real.append(s_)
    how = "символьно"
    if not real:
        # численный поиск из сетки начальных точек
        from scipy.optimize import root
        gfun = sp.lambdify(syms, grad, 'numpy')
        found = []
        rng = np.random.default_rng(0)
        for start in rng.uniform(-5, 5, size=(80, len(syms))):
            sol = root(lambda v: np.array(gfun(*v), dtype=float), start)
            if sol.success and np.all(np.isfinite(sol.x)) and np.max(np.abs(sol.x)) < 1e6:
                if not any(np.allclose(sol.x, p_, atol=1e-6) for p_ in found):
                    found.append(sol.x)
        real = [dict(zip(syms, map(sp.Float, p_))) for p_ in found]
        how = "численно (метод Ньютона из случайных начальных точек)"
    steps.append(f"   Стационарные точки ({how}): " + (str(len(real)) if real else "не найдены"))
    steps += ["", "⚙️ 2. ДОСТАТОЧНОЕ УСЛОВИЕ: МАТРИЦА ГЕССЕ"]
    steps += box([f"H = {pretty(H.tolist())}",
                  "Критерий Сильвестра: все угловые миноры > 0 — минимум; знаки чередуются (−, +, −, …) — максимум;",
                  "собственные значения разных знаков — седловая точка; есть нулевые — нужен дополнительный анализ."])
    results = []
    for s_ in real:
        Hv = H.subs(s_)
        try:
            eig = [complex(sp.N(e)).real for e in Hv.eigenvals(multiple=True)]
        except Exception:
            eig = list(np.linalg.eigvalsh(np.array(Hv.tolist(), dtype=float)))
        minors = [sp.simplify(Hv[:k, :k].det()) for k in range(1, len(syms) + 1)]
        if all(e > 1e-12 for e in eig):
            kind = "локальный минимум"
        elif all(e < -1e-12 for e in eig):
            kind = "локальный максимум"
        elif any(e > 1e-12 for e in eig) and any(e < -1e-12 for e in eig):
            kind = "седловая точка (экстремума нет)"
        else:
            kind = "вырожденный случай (гессиан вырожден) — критерий не даёт ответа"
        fv = sp.simplify(f.subs(s_))
        coords = "; ".join(_approx(s_[sym]) for sym in syms)
        steps.append(f"   ▸ Точка ({coords}):  миноры Δ = {', '.join(_approx(m) for m in minors)}  →  {kind},  f = {_approx(fv)}")
        results.append((s_, kind, fv))
    steps += ["", "🎯 ОТВЕТ"]
    if results:
        steps += box([f"({'; '.join(pretty(s_[sym]) for sym in syms)}): {k}, f = {pretty(v)}" for s_, k, v in results], "answer")
    else:
        steps += box(["Стационарных точек не найдено"], "answer")

    sc2 = sc3 = None
    if len(syms) == 2:
        from .functions import surface
        pts = [(float(s_[syms[0]]), float(s_[syms[1]])) for s_, _, _ in results] or [(0.0, 0.0)]
        xs_, ys_ = [p[0] for p in pts], [p[1] for p in pts]
        span = max(2.0, (max(xs_) - min(xs_)) * 0.8, (max(ys_) - min(ys_)) * 0.8)
        cx, cy = (max(xs_) + min(xs_)) / 2, (max(ys_) + min(ys_)) / 2
        expr_xy = f.subs({syms[0]: sp.Symbol('x', real=True), syms[1]: sp.Symbol('y', real=True)})
        srf = surface(sp.sstr(expr_xy), str(cx - span), str(cx + span), str(cy - span), str(cy + span), 20)
        sc2, sc3 = srf['plot2d'], srf['scene3d']
        sc2['title'] = "Линии уровня и стационарные точки"
        for (s_, kind, fv) in results:
            px, py = float(s_[syms[0]]), float(s_[syms[1]])
            col = COL_GREEN if "минимум" in kind else (COL_RED if "максимум" in kind else COL_AMBER)
            short = "min" if "минимум" in kind else ("max" if "максимум" in kind else ("седло" if "седл" in kind else "?"))
            sc2['points'].append((px, py, short, col))
            sc3.add_point((px, py, float(fv)), "", color=col)
    return {'points': results, 'steps': "\n".join(steps), 'plot2d': sc2, 'scene3d': sc3}


# =============================================================================
# Интегралы
# =============================================================================

RULE_NAMES = {
    'ConstantRule': "интеграл константы: ∫c dx = c·x",
    'ConstantTimesRule': "вынос постоянного множителя: ∫c·f dx = c·∫f dx",
    'PowerRule': "степенная функция: ∫xⁿ dx = xⁿ⁺¹/(n + 1)",
    'NestedPowRule': "степенная функция от степени",
    'AddRule': "интеграл суммы равен сумме интегралов",
    'URule': "замена переменной",
    'PartsRule': "интегрирование по частям: ∫u dv = u·v − ∫v du",
    'CyclicPartsRule': "циклическое интегрирование по частям (интеграл выражается через себя)",
    'ExpRule': "показательная функция: ∫aˣ dx = aˣ/ln a",
    'ReciprocalRule': "∫dx/x = ln|x|",
    'ArctanRule': "табличный интеграл: ∫dx/(a + b·x²) через arctg",
    'ArcsinRule': "табличный интеграл: ∫dx/√(1 − x²) = arcsin x",
    'ArcsinhRule': "табличный интеграл через arsh",
    'SinRule': "∫sin x dx = −cos x",
    'CosRule': "∫cos x dx = sin x",
    'SecTanRule': "∫sec x·tg x dx = sec x",
    'Sec2Rule': "∫dx/cos²x = tg x",
    'Csc2Rule': "∫dx/sin²x = −ctg x",
    'CscCotRule': "∫csc x·ctg x dx = −csc x",
    'TrigRule': "табличный тригонометрический интеграл",
    'RewriteRule': "преобразование подынтегрального выражения",
    'CompleteSquareRule': "выделение полного квадрата",
    'PartialFractionRule': "разложение на простейшие дроби",
    'PiecewiseRule': "кусочно-заданная функция",
    'HeavisideRule': "функция Хевисайда",
    'TrigSubstitutionRule': "тригонометрическая подстановка",
    'DerivativeRule': "интеграл от производной",
    'ErfRule': "интеграл через функцию ошибок erf",
    'DontKnowRule': "элементарными методами не берётся",
    'AlternativeRule': "возможны разные способы",
    'SqrtLinearRule': "корень из линейной функции",
    'SqrtQuadraticRule': "корень из квадратного трёхчлена",
    'ReciprocalSqrtQuadraticRule': "1/√(квадратный трёхчлен)",
    'LogRule': "∫ln x dx = x·ln x − x",
}


def _rule_children(rule) -> List[Any]:
    out = []
    if not dataclasses.is_dataclass(rule):
        return out
    for fld in dataclasses.fields(rule):
        v = getattr(rule, fld.name)
        if dataclasses.is_dataclass(v) and hasattr(v, 'integrand'):
            out.append(v)
        elif isinstance(v, (list, tuple)):
            out.extend(c for c in v if dataclasses.is_dataclass(c) and hasattr(c, 'integrand'))
    return out


PARTS_ROLES = {'v_step': "находим v = ∫dv", 'second_step': "вычисляем ∫v du"}


def _render_rule(rule, depth: int, lines: List[str], budget: List[int], role: str = "", parent_var=X,
                 shown=None):
    if budget[0] <= 0:
        return
    budget[0] -= 1
    name = type(rule).__name__
    desc = RULE_NAMES.get(name, name)
    ind = "   " + "   " * depth
    var = getattr(rule, 'variable', None) or parent_var
    integrand = shown if shown is not None else getattr(rule, 'integrand', None)
    if integrand is not None:
        tail = ""
        try:
            res = rule.eval()
            # внутренние правила SymPy иногда хранят выражение без постоянного множителя —
            # показываем результат шага, только если он проверяется дифференцированием
            if isinstance(var, sp.Symbol) and sp.simplify(sp.diff(res, var) - integrand) == 0:
                tail = f" = {pretty(res)}"
        except Exception:
            pass
        lines.append(f"{ind}▸ {role + ': ' if role else ''}∫ {pretty(integrand)} d{var}{tail}")
    else:
        # шаги внутри циклического интегрирования по частям хранятся без подынтегрального выражения
        lines.append(f"{ind}▸ {role + ': ' if role else ''}очередное интегрирование по частям")
    extra = ""
    if name == 'URule':
        extra = f"   (замена: {getattr(rule, 'u_var', 'u')} = {pretty(getattr(rule, 'u_func', ''))})"
    elif name == 'PartsRule':
        extra = f"   (u = {pretty(rule.u)}, dv = {pretty(rule.dv)} d{var})"
    elif name == 'RewriteRule':
        extra = f"   (переписываем как {pretty(rule.rewritten)})"
    elif name == 'ConstantTimesRule':
        extra = f"   (множитель {pretty(rule.constant)})"
    lines.append(f"{ind}   {desc}{extra}")
    if name == 'PartsRule':
        for fld, label in PARTS_ROLES.items():
            ch = getattr(rule, fld, None)
            if dataclasses.is_dataclass(ch) and hasattr(ch, 'integrand'):
                _render_rule(ch, depth + 1, lines, budget, label, var)
        return
    children = _rule_children(rule)
    if name == 'AlternativeRule' and children:
        children = children[:1]
    for ch in children:
        # у шага после выноса множителя SymPy может хранить исходное выражение — показываем реально интегрируемое
        other = getattr(rule, 'other', None) if name == 'ConstantTimesRule' else None
        _render_rule(ch, depth + 1, lines, budget, "", var, other)
    if name == 'CyclicPartsRule':
        lines.append(f"{ind}   После двух интегрирований по частям исходный интеграл I снова появляется в правой части:")
        lines.append(f"{ind}   I = … + ({pretty(rule.coefficient)})·I  ⟹  I выражается из этого уравнения.")


def indefinite_integral(f_text: str, var: str = "x") -> Dict[str, Any]:
    v = var.strip() or "x"
    f = parse_expression(f_text, [v])
    V = sp.Symbol(v, real=True)
    steps = [f"📌 НЕОПРЕДЕЛЁННЫЙ ИНТЕГРАЛ  ∫ {pretty(f)} d{v}"]
    lines: List[str] = []
    manual_ok = False
    try:
        from sympy.integrals.manualintegrate import integral_steps
        rule = integral_steps(f, V)
        if type(rule).__name__ != 'DontKnowRule':
            _render_rule(rule, 0, lines, [60])
            manual_ok = True
    except Exception:
        pass
    if manual_ok:
        steps += ["", "📝 ХОД РЕШЕНИЯ (правила интегрирования)"]
        steps += [ln.replace('_u', 'u') for ln in lines]  # служебное имя переменной замены SymPy
    F_ = sp.integrate(f, V)
    if F_.has(sp.Integral):
        steps += ["", "🎯 ОТВЕТ"]
        steps += box(["Интеграл не выражается в элементарных функциях (SymPy не нашёл первообразную).",
                      "Для определённого интеграла используйте численное интегрирование."], "answer")
        return {'antiderivative': None, 'steps': "\n".join(steps), 'plot2d': None}
    F_s = sp.simplify(F_)
    if sp.count_ops(F_s) > sp.count_ops(F_):
        F_s = F_
    steps += ["", "⚙️ ПРОВЕРКА ДИФФЕРЕНЦИРОВАНИЕМ"]
    check = sp.simplify(sp.diff(F_s, V) - f)
    steps.append(f"   (F)′ = {pretty(sp.simplify(sp.diff(F_s, V)))}" +
                 ("  — совпадает с подынтегральной функцией ✓" if check == 0 else
                  "  — совпадает с подынтегральной функцией после преобразований" if _numeric_zero(check, V) else
                  "  — проверка не подтвердила совпадение"))
    steps += ["", "🎯 ОТВЕТ"]
    steps += box([f"∫ {pretty(f)} d{v} = {pretty(F_s)} + C"], "answer")
    if F_s.has(sp.log):
        steps.append("   Для действительных значений логарифм понимается как ln|…| (первообразная на каждом "
                     "промежутке, где подынтегральная функция непрерывна).")
    special = {sp.Ei: "Ei — интегральная показательная", sp.Si: "Si — интегральный синус", sp.Ci: "Ci — интегральный косинус",
               sp.erf: "erf — функция ошибок", sp.li: "li — интегральный логарифм", sp.fresnels: "S — интеграл Френеля",
               sp.fresnelc: "C — интеграл Френеля", sp.gamma: "Γ — гамма-функция", sp.uppergamma: "Γ(s, x) — неполная гамма-функция"}
    used = [txt for fn_, txt in special.items() if F_s.has(fn_)]
    if used:
        steps.append("   Первообразная не элементарна и выражается через специальные функции: " + "; ".join(used) + ".")
    sc = None
    if v == 'x':
        xs, ys = sample(f, -5, 5)
        xs2, ys2 = sample(F_s, -5, 5)
        sc = new_scene2d(equal=False, title="Подынтегральная функция и первообразная (C = 0)")
        sc['curves'] += [(xs, ys, "f(x)", COL_MAIN), (xs2, ys2, "F(x)", COL_GREEN)]
    return {'antiderivative': F_s, 'steps': "\n".join(steps), 'plot2d': sc}


def _numeric_zero(e, V) -> bool:
    try:
        fn = to_numpy(e, [str(V)])
        vals = fn(np.linspace(0.3, 2.7, 9))
        vals = vals[np.isfinite(vals)]
        return vals.size > 0 and np.max(np.abs(vals)) < 1e-9
    except Exception:
        return False


def definite_integral(f_text: str, a_text: str, b_text: str) -> Dict[str, Any]:
    from scipy import integrate
    f = parse_expression(f_text, ['x'])
    a, b = parse_bound(a_text), parse_bound(b_text)
    improper = not (a.is_finite and b.is_finite)
    steps = [f"📌 {'НЕСОБСТВЕННЫЙ' if improper else 'ОПРЕДЕЛЁННЫЙ'} ИНТЕГРАЛ  ∫ от {_approx(a)} до {_approx(b)}  {pretty(f)} dx"]
    exact = None
    try:
        Fa = sp.integrate(f, X)
        if not Fa.has(sp.Integral):
            steps += ["", "📝 ПЕРВООБРАЗНАЯ"]
            steps += box([f"F(x) = {pretty(sp.simplify(Fa))}"])
            res = sp.integrate(f, (X, a, b))
            if not res.has(sp.Integral):
                exact = sp.simplify(res)
                steps += ["", "⚙️ ФОРМУЛА НЬЮТОНА — ЛЕЙБНИЦА" + (" (с предельным переходом)" if improper else "")]
                steps += box(["∫ₐᵇ f dx = F(b) − F(a)" if not improper else "∫ₐ^∞ f dx = lim (B → ∞) [F(B) − F(a)]"])
                steps.append(f"   = {_approx(exact)}")
    except Exception:
        pass
    if exact is None:
        steps += ["", "📝 Первообразная в элементарных функциях не найдена — интеграл вычисляется численно."]

    steps += ["", "📍 ЧИСЛЕННАЯ ПРОВЕРКА (адаптивная квадратура Гаусса — Кронрода, scipy.integrate.quad)"]
    fn = to_numpy(f, ['x'])
    af, bf = _num(a) if a.is_finite else (-np.inf if a == -sp.oo else np.inf), _num(b) if b.is_finite else (np.inf if b == sp.oo else -np.inf)
    try:
        import warnings
        with warnings.catch_warnings(record=True) as wlist:
            warnings.simplefilter("always")
            val, err = integrate.quad(lambda t: float(fn(np.array([t]))[0]), af, bf, limit=200)
        steps.append(f"   ▸ I ≈ {F(val, 10)}   (оценка погрешности {F(err, 2)})")
        if wlist:
            steps.append("   Предупреждение квадратуры: возможно, интеграл расходится или подынтегральная функция имеет особенность.")
    except Exception as ex:
        val, err = float('nan'), float('nan')
        steps.append(f"   Численно вычислить не удалось: {ex}")
    if exact is not None and (exact.is_infinite or exact in (sp.oo, -sp.oo, sp.zoo)):
        steps.append("   Интеграл расходится, поэтому численное значение выше смысла не имеет.")
    elif exact is not None and _is_finite_number(exact) and math.isfinite(val):
        diff = abs(_num(exact) - val)
        steps.append(f"   Расхождение с точным значением: {F(diff, 2)}" + (" ✓" if diff <= max(10 * err, 1e-8 * max(1, abs(val))) else ""))

    steps += ["", "🎯 ОТВЕТ"]
    if exact is not None:
        ans = "Интеграл расходится" if (exact.is_infinite or exact in (sp.oo, -sp.oo, sp.zoo)) else f"I = {_approx(exact)}"
    else:
        ans = f"I ≈ {F(val, 10)}"
    steps += box([ans], "answer")

    lo = _num(a) if a.is_finite else (_num(b) - 10 if b.is_finite else -10)
    hi = _num(b) if b.is_finite else (lo + 10)
    if lo > hi:
        lo, hi = hi, lo
    pad = 0.15 * (hi - lo or 1)
    xs, ys = sample(f, lo - pad, hi + pad)
    xa = np.linspace(lo, hi, 600)
    ya = fn(xa)
    sc = new_scene2d(equal=False, title="Площадь под графиком (со знаком)")
    sc['bands'].append((xa, np.minimum(0, ya), np.maximum(0, ya), "∫ f dx", COL_AMBER))
    sc['curves'].append((xs, ys, f"y = {pretty(f)}", COL_MAIN))
    return {'exact': exact, 'numeric': val, 'error': err, 'steps': "\n".join(steps), 'plot2d': sc}


def multiple_integral(f_text: str, limits_text: str) -> Dict[str, Any]:
    """
    Повторный интеграл. limits_text — по строке на переменную, от внутренней к внешней:
      y: 0 .. x
      x: 0 .. 1
    """
    from scipy import integrate
    lims = []
    for ln, line in enumerate(str(limits_text).splitlines(), 1):
        if not line.strip():
            continue
        if ':' not in line or '..' not in line:
            raise ValueError(f"Строка {ln}: формат «переменная: нижний .. верхний», например «y: 0 .. x»")
        var, rng = line.split(':', 1)
        lo, hi = rng.split('..', 1)
        lims.append((var.strip(), lo.strip(), hi.strip()))
    if not 2 <= len(lims) <= 3:
        raise ValueError("Укажите пределы для 2 или 3 переменных (от внутренней к внешней)")
    names = [l_[0] for l_ in lims]
    if len(set(names)) != len(names):
        raise ValueError("Переменные интегрирования должны быть разными")
    f = parse_expression(f_text, names)
    syms = symbols(names)
    bounds = []
    for i, (n, lo, hi) in enumerate(lims):
        outer = names[i + 1:]
        lo_e, hi_e = parse_expression(lo, outer), parse_expression(hi, outer)
        bounds.append((lo_e, hi_e))
    kind = "ДВОЙНОЙ" if len(lims) == 2 else "ТРОЙНОЙ"
    steps = [f"📌 {kind} ИНТЕГРАЛ ∫∫{'∫' if len(lims) == 3 else ''} {pretty(f)} d{' d'.join(names)}"]
    steps += box([f"{n}: от {pretty(lo)} до {pretty(hi)}" for n, (lo, hi) in zip(names, bounds)])
    steps += ["", "📝 ПОВТОРНОЕ ИНТЕГРИРОВАНИЕ (от внутреннего интеграла к внешнему)"]
    cur = f
    exact = None
    try:
        for s_, (lo, hi), n in zip(syms, bounds, names):
            nxt = sp.integrate(cur, (s_, lo, hi))
            if nxt.has(sp.Integral):
                raise ValueError
            nxt = sp.simplify(nxt)
            steps.append(f"   ▸ ∫ по {n} от {pretty(lo)} до {pretty(hi)}:  {pretty(nxt)}")
            cur = nxt
        exact = cur
    except Exception:
        steps.append("   Символьно вычислить не удалось — используется численное интегрирование.")
    steps += ["", "📍 ЧИСЛЕННАЯ ПРОВЕРКА (scipy.integrate.nquad)"]
    fn = sp.lambdify(syms, f, 'numpy')
    rng_funcs = []
    for i, (lo, hi) in enumerate(bounds):
        outer = syms[i + 1:]
        lo_f, hi_f = sp.lambdify(outer, lo, 'numpy'), sp.lambdify(outer, hi, 'numpy')
        rng_funcs.append(lambda *args, lo_f=lo_f, hi_f=hi_f: (float(lo_f(*args)), float(hi_f(*args))))
    try:
        val, err = integrate.nquad(lambda *args: float(fn(*args)), rng_funcs)
        steps.append(f"   ▸ I ≈ {F(val, 10)}   (оценка погрешности {F(err, 2)})")
    except Exception as ex:
        val, err = float('nan'), float('nan')
        steps.append(f"   Численно вычислить не удалось: {ex}")
    steps += ["", "🎯 ОТВЕТ"]
    steps += box([f"I = {_approx(exact)}" if exact is not None else f"I ≈ {F(val, 10)}"], "answer")

    sc = None
    if len(lims) == 2:
        # область интегрирования: внешняя переменная по оси абсцисс
        o_lo, o_hi = _num(bounds[1][0]), _num(bounds[1][1])
        ts = np.linspace(o_lo, o_hi, 400)
        lo_v = np.broadcast_to(sp.lambdify(syms[1], bounds[0][0], 'numpy')(ts), ts.shape).astype(float)
        hi_v = np.broadcast_to(sp.lambdify(syms[1], bounds[0][1], 'numpy')(ts), ts.shape).astype(float)
        sc = new_scene2d(equal=True, title="Область интегрирования")
        sc['xlabel'], sc['ylabel'] = names[1], names[0]
        sc['bands'].append((ts, lo_v, hi_v, "D", COL_AMBER))
        sc['curves'] += [(ts, lo_v, f"{names[0]} = {pretty(bounds[0][0])}", COL_MAIN),
                         (ts, hi_v, f"{names[0]} = {pretty(bounds[0][1])}", COL_GREEN)]
    return {'exact': exact, 'numeric': val, 'steps': "\n".join(steps), 'plot2d': sc}


# =============================================================================
# Ряды
# =============================================================================

def taylor(f_text: str, point_text: str = "0", order: int = 5) -> Dict[str, Any]:
    f = parse_expression(f_text, ['x'])
    x0 = parse_bound(point_text)
    if not x0.is_finite:
        raise ValueError("Точка разложения должна быть конечной")
    if not 1 <= order <= 20:
        raise ValueError("Порядок: от 1 до 20")
    steps = [f"📌 РЯД ТЕЙЛОРА функции {pretty(f)} в точке x₀ = {pretty(x0)} до (x − x₀)^{order}"]
    steps += box(["f(x) = Σ f⁽ᵏ⁾(x₀)/k! · (x − x₀)ᵏ + Rₙ(x)"])
    steps += ["", "📝 КОЭФФИЦИЕНТЫ"]
    rows = []
    poly = sp.Integer(0)
    dk = f
    for k in range(order + 1):
        val = sp.simplify(dk.subs(X, x0))
        if not _is_finite_number(val):
            raise ValueError(f"Производная порядка {k} не определена в точке x₀ — ряд Тейлора не существует (попробуйте другую точку)")
        coef = sp.simplify(val / sp.factorial(k))
        rows.append((str(k), pretty(val), pretty(coef)))
        poly += coef * (X - x0) ** k
        dk = sp.diff(dk, X)
    steps += box(table_lines(("k", "f⁽ᵏ⁾(x₀)", "f⁽ᵏ⁾(x₀)/k!"), rows))
    steps += ["", "🎯 МНОГОЧЛЕН ТЕЙЛОРА"]
    steps += box([f"f(x) ≈ {pretty(poly if x0 == 0 else sp.expand(poly))}",
                  f"Остаточный член: o((x − x₀)^{order}) при x → x₀"], "answer")
    x0f = _num(x0)
    w = 3.0
    xs, ys = sample(f, x0f - w, x0f + w)
    sc = new_scene2d(equal=False, title="Функция и её многочлены Тейлора")
    sc['curves'].append((xs, ys, f"f(x) = {pretty(f)}", COL_MAIN))
    colors = ("#F59E0B", "#10B981", "#EF4444", "#8B5CF6")
    shown = sorted({1, max(1, order // 3), max(1, (2 * order) // 3), order})
    p_k = sp.Integer(0)
    dk = f
    partial = {}
    for k in range(order + 1):
        p_k += sp.simplify(dk.subs(X, x0)) / sp.factorial(k) * (X - x0) ** k
        dk = sp.diff(dk, X)
        partial[k] = p_k
    for i, k in enumerate(shown):
        xs_, ys_ = sample(partial[k], x0f - w, x0f + w)
        sc['curves'].append((xs_, ys_, f"T{k}(x)", colors[i % len(colors)], '--'))
    yf = ys[np.isfinite(ys)]
    if yf.size:
        lo, hi = float(yf.min()), float(yf.max())
        pad = 0.4 * (hi - lo or 1)
        sc['ylim'] = (lo - pad, hi + pad)
    sc['points'].append((x0f, _num(f.subs(X, x0)), "x₀", COL_RED))
    return {'polynomial': poly, 'steps': "\n".join(steps), 'plot2d': sc}


def series_sum(term_text: str, n0_text: str = "1") -> Dict[str, Any]:
    n = sp.Symbol('n', integer=True, positive=True)
    a = parse_expression(term_text, ['n']).subs(sp.Symbol('n', real=True), n)
    n0 = int(_num(parse_bound(n0_text)))
    steps = [f"📌 ЧИСЛОВОЙ РЯД  Σ (n = {n0}…∞)  {pretty(a)}"]
    steps += ["", "📝 1. НЕОБХОДИМОЕ УСЛОВИЕ СХОДИМОСТИ: aₙ → 0"]
    try:
        lim_a = sp.limit(a, n, sp.oo)
        steps.append(f"   lim aₙ = {_approx(lim_a)}" + ("" if lim_a == 0 else "  ≠ 0 — ряд расходится."))
    except Exception:
        lim_a = None
        steps.append("   Предел вычислить не удалось.")
    steps += ["", "⚙️ 2. ПРИЗНАКИ СХОДИМОСТИ"]
    try:
        ratio = sp.limit(sp.Abs(sp.simplify(a.subs(n, n + 1) / a)), n, sp.oo)
        verdict = "< 1 — сходится абсолютно" if ratio.is_number and ratio < 1 else ("> 1 — расходится" if ratio.is_number and ratio > 1 else "= 1 — признак не даёт ответа")
        steps.append(f"   ▸ Признак Даламбера: lim |aₙ₊₁/aₙ| = {_approx(ratio)} {verdict}")
    except Exception:
        steps.append("   ▸ Признак Даламбера: вычислить не удалось")
    try:
        root_ = sp.limit(sp.Abs(a) ** (sp.Integer(1) / n), n, sp.oo)
        verdict = "< 1 — сходится абсолютно" if root_.is_number and root_ < 1 else ("> 1 — расходится" if root_.is_number and root_ > 1 else "= 1 — признак не даёт ответа")
        steps.append(f"   ▸ Радикальный признак Коши: lim ⁿ√|aₙ| = {_approx(root_)} {verdict}")
    except Exception:
        steps.append("   ▸ Радикальный признак Коши: вычислить не удалось")
    S = sp.Sum(a, (n, n0, sp.oo))
    try:
        conv = bool(S.is_convergent())  # SymPy возвращает S.true / S.false
        steps.append(f"   ▸ Итог по совокупности признаков (SymPy): {'сходится' if conv else 'расходится'}")
    except Exception:
        conv = None
        steps.append("   ▸ Определить сходимость автоматически не удалось.")
    if conv:
        try:
            abs_conv = S.is_absolutely_convergent()
            steps.append("   ▸ Сходится абсолютно." if abs_conv else "   ▸ Сходится условно (ряд из модулей расходится).")
        except Exception:
            pass
    steps += ["", "📍 3. ЧАСТИЧНЫЕ СУММЫ"]
    an = sp.lambdify(n, a, 'math')
    partial, s_ = [], 0.0
    N = 2000
    for k in range(n0, n0 + N):
        try:
            s_ += float(an(k))
        except (OverflowError, ZeroDivisionError, ValueError):
            break
        partial.append(s_)
    rows = [(str(n0 + k - 1 + 1), F(partial[k - 1], 10)) for k in (1, 2, 5, 10, 50, 100, 500, 1000, 2000) if k <= len(partial)]
    steps += box(table_lines(("N", "S_N"), rows))
    exact = None
    if conv:
        try:
            val = S.doit()
            if not val.has(sp.Sum):
                exact = sp.simplify(val)
        except Exception:
            pass
    steps += ["", "🎯 ОТВЕТ"]
    if conv is False:
        steps += box(["Ряд расходится"], "answer")
    elif exact is not None:
        steps += box([f"Сумма ряда S = {_approx(exact)}"], "answer")
    elif conv:
        steps += box([f"Ряд сходится; S ≈ {F(partial[-1], 8)} (частичная сумма, N = {len(partial)})"], "answer")
    else:
        steps += box([f"Сходимость не установлена; S_{len(partial)} = {F(partial[-1], 8)}"], "answer")
    sc = new_scene2d(equal=False, title="Частичные суммы S_N")
    sc['xlabel'], sc['ylabel'] = "N", "S_N"
    m = min(len(partial), 200)
    sc['scatter'].append((np.arange(n0, n0 + m), np.array(partial[:m]), "S_N", COL_MAIN))
    if exact is not None and _is_finite_number(exact):
        sc['curves'].append((np.array([n0, n0 + m]), np.array([_num(exact)] * 2), f"S = {pretty(exact)}", COL_GREEN, '--'))
    return {'convergent': conv, 'sum': exact, 'steps': "\n".join(steps), 'plot2d': sc}
