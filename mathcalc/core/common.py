"""
Общие функции ядра: разбор ввода, точное форматирование чисел и формул (√, ², индексы),
приведение уравнений, оформление шагов решения (рамки формул и ответов).
Используются всеми разделами.
"""

import re
from typing import Any, List, Tuple

import sympy as sp

from .result import new_scene2d  # noqa: F401  (реэкспорт для решателей)


def to_pretty_math(text: Any) -> str:
    """
    Преобразует математические выражения в красивый читаемый Unicode вид:
    - sqrt(...) -> √... (настоящий знак корня)
    - **2 -> ²
    - x0 -> x₀
    - * -> ·
    - ==> -> ⟹
    """
    s = str(text)

    # 1. Замена корней sqrt(...) на √...
    s = re.sub(r'sqrt\((\d+)\)', r'√\1', s)
    s = re.sub(r'sqrt\(([a-zA-Z0-9_]+)\)', r'√\1', s)

    while 'sqrt(' in s:
        idx = s.find('sqrt(')
        depth = 0
        end_idx = -1
        for i in range(idx + 4, len(s)):
            if s[i] == '(':
                depth += 1
            elif s[i] == ')':
                depth -= 1
                if depth == 0:
                    end_idx = i
                    break
        if end_idx != -1:
            inner = s[idx + 5 : end_idx]
            s = s[:idx] + '√(' + inner + ')' + s[end_idx + 1:]
        else:
            s = s.replace('sqrt(', '√(')
            break

    # 2. Степени **2, **3, etc. -> ², ³, ⁴
    pow_map = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹', '-': '⁻'}
    s = re.sub(r'\*\*(-?\d+)', lambda m: ''.join(pow_map.get(c, c) for c in m.group(1)), s)
    s = re.sub(r'\^(\d+)', lambda m: ''.join(pow_map.get(c, c) for c in m.group(1)), s)

    # 3. Индексы x0, y0, z0, x1, y1, z1, M0, M1, n1, s1
    sub_map = {'0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉'}
    s = re.sub(r'\b([xyzMnsPtuvwABCDEF])_?(\d+)\b',
               lambda m: m.group(1) + ''.join(sub_map.get(c, c) for c in m.group(2)), s)

    # 4. Умножение * -> ·
    s = s.replace('*', '·')
    s = re.sub(r'\s*·\s*', '·', s)
    s = re.sub(r'(\d+)·([a-zA-Zxyz])', r'\1\2', s)

    # 5. Стрелки
    s = s.replace('==>', '  ⟹  ').replace('-->', ' ➔ ').replace('->', ' ➔ ')

    # 6. Тригонометрия и греческие буквы
    s = s.replace('phi', 'φ').replace('theta', 'θ').replace('alpha', 'α')
    s = s.replace('beta', 'β').replace('gamma', 'γ').replace('Delta', 'Δ').replace('mu', 'μ')
    s = s.replace('acos', 'arccos').replace('asin', 'arcsin')

    return s


def parse_number(val_str: Any) -> sp.Expr:
    """Безопасный парсинг числа или математического выражения (например 1/2, -3.5, sqrt(3))."""
    if isinstance(val_str, (int, float, sp.Expr)):
        return sp.sympify(val_str)
    raw = str(val_str).strip()
    s = raw.replace(',', '.').replace('^', '**').replace('−', '-')
    # Поддерживаем ввод реального корня: √3, √2.5, √(x+1)
    s = re.sub(r'√\s*(\d+(?:\.\d+)?)', r'sqrt(\1)', s).replace('√', 'sqrt')
    if not s:
        raise ValueError("Пустое поле — введите число")
    allowed_locals = {
        'sqrt': sp.sqrt,
        'pi': sp.pi,
        'E': sp.E,
        'sin': sp.sin,
        'cos': sp.cos,
        'tan': sp.tan,
        'asin': sp.asin,
        'acos': sp.acos,
        'atan': sp.atan
    }
    try:
        expr = sp.sympify(s, locals=allowed_locals, rational=True)
    except (sp.SympifyError, SyntaxError, TypeError, ValueError):
        raise ValueError(f"Не удалось разобрать «{raw}». Примеры ввода: 2, -1/3, 2.5, sqrt(3), √2, pi/4") from None
    if not isinstance(expr, sp.Expr) or expr.free_symbols or not expr.is_number:
        raise ValueError(f"«{raw}» — не число. Допустимы числа, дроби, sqrt(...), pi, sin/cos/tan")
    if expr.is_real is False:
        raise ValueError(f"«{raw}» — не действительное число")
    return expr


def fmt_num(val: Any, decimals: int = 4) -> str:
    """Форматирование числа: красивый точный вид с корнями (√) + десятичное приближение."""
    try:
        expr = sp.sympify(val)
        exact_str = to_pretty_math(expr)
        if expr.is_Integer:
            return exact_str
        elif expr.is_Rational:
            f_val = float(expr)
            return f"{exact_str}  (≈ {f_val:.{decimals}f})"
        elif expr.is_number:
            f_val = float(expr.evalf())
            return f"{exact_str}  (≈ {f_val:.{decimals}f})"
        return exact_str
    except Exception:
        return to_pretty_math(str(val))


def fmt_point(pt: Tuple[Any, Any, Any]) -> str:
    """Красивый вывод точки M(x, y, z)"""
    return f"({fmt_num(pt[0])};  {fmt_num(pt[1])};  {fmt_num(pt[2])})"


def fmt_vector(v: Tuple[Any, Any, Any]) -> str:
    """Красивый вывод вектора {x; y; z}"""
    return f"{{{fmt_num(v[0])};  {fmt_num(v[1])};  {fmt_num(v[2])}}}"


def simplify_plane_eq(A: sp.Expr, B: sp.Expr, C: sp.Expr, D: sp.Expr) -> Tuple[sp.Expr, sp.Expr, sp.Expr, sp.Expr, str]:
    """
    Приведение уравнения плоскости Ax + By + Cz + D = 0 к каноническому целочисленному виду.
    """
    coeffs = [A, B, C, D]
    
    if all(sp.sympify(c).is_rational for c in coeffs):
        lcm_den = sp.ilcm(*[sp.Rational(c).q for c in coeffs if c != 0] or [1])
        int_coeffs = [sp.Integer(sp.Rational(c) * lcm_den) for c in coeffs]
        gcd_num = sp.igcd(*[c for c in int_coeffs if c != 0] or [1])
        coeffs = [c // gcd_num for c in int_coeffs]

    for c in coeffs:
        if c != 0:
            if c < 0:
                coeffs = [-x_ for x_ in coeffs]
            break

    A_s, B_s, C_s, D_s = coeffs
    
    terms = []
    if A_s != 0:
        if A_s == 1: terms.append("x")
        elif A_s == -1: terms.append("-x")
        else: terms.append(f"{A_s}x")
    
    if B_s != 0:
        sign = "+ " if B_s > 0 and terms else ("- " if B_s < 0 and terms else ("-" if B_s < 0 else ""))
        abs_b = abs(B_s)
        val = "y" if abs_b == 1 else f"{abs_b}y"
        terms.append(f"{sign}{val}")

    if C_s != 0:
        sign = "+ " if C_s > 0 and terms else ("- " if C_s < 0 and terms else ("-" if C_s < 0 else ""))
        abs_c = abs(C_s)
        val = "z" if abs_c == 1 else f"{abs_c}z"
        terms.append(f"{sign}{val}")

    if D_s != 0:
        sign = "+ " if D_s > 0 and terms else ("- " if D_s < 0 and terms else ("-" if D_s < 0 else ""))
        terms.append(f"{sign}{abs(D_s)}")

    eq_str = " ".join(terms) if terms else "0"
    eq_str = f"{eq_str} = 0"
    return A_s, B_s, C_s, D_s, eq_str


COL_MAIN = "#3B82F6"
COL_RED = "#EF4444"
COL_GREEN = "#10B981"
COL_AMBER = "#F59E0B"
COL_PINK = "#EC4899"
COL_GRAY = "#94A3B8"


def simp(v):
    """Упрощение выражения (корни, дроби)."""
    return sp.simplify(sp.radsimp(sp.sympify(v)))


def sgn(v) -> int:
    """Знак числа (с числовой проверкой нуля)."""
    f = float(sp.N(v, 30))
    if abs(f) < 1e-12:
        return 0
    return 1 if f > 0 else -1


def ex(v) -> str:
    """Точное значение без десятичного приближения."""
    return to_pretty_math(simp(v))


def signed(v) -> str:
    """Слагаемое со знаком: '+ 4' или '- 4'."""
    v = simp(v)
    return f"- {ex(-v)}" if sgn(v) < 0 else f"+ {ex(v)}"


def shifted(var: str, v0) -> str:
    """Выражение (var − v0) без двойных знаков."""
    v0 = simp(v0)
    if sgn(v0) == 0:
        return var
    return f"({var} + {ex(-v0)})" if sgn(v0) < 0 else f"({var} − {ex(v0)})"


def pt_str(p) -> str:
    return "(" + "; ".join(ex(c) for c in p) + ")"


def pt_full(p) -> str:
    return "(" + "; ".join(fmt_num(simp(c)) for c in p) + ")"


def vec_str(p) -> str:
    return "(" + "; ".join(ex(c) for c in p) + ")"


def dist(p, q):
    return simp(sp.sqrt(sum((a - b) ** 2 for a, b in zip(p, q))))


def num(v) -> float:
    return float(sp.N(v, 20))


def box(lines: List[str], kind: str = "formula") -> List[str]:
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


def line_eq(A, B, C) -> Tuple[str, Tuple]:
    """Общее уравнение прямой Ax + By + C = 0 в приведённом виде. Возвращает (строка, (A, B, C))."""
    A, B, C = simp(A), simp(B), simp(C)
    As, Bs, _, Cs, eq = simplify_plane_eq(A, B, sp.Integer(0), C)
    return to_pretty_math(eq), (As, Bs, Cs)


def slope_form(A, B, C) -> str:
    """Уравнение с угловым коэффициентом y = kx + b (или x = const)."""
    if sgn(B) == 0:
        return f"x = {ex(-C / A)}  (вертикальная прямая, углового коэффициента нет)"
    k = simp(-A / B)
    b = simp(-C / B)
    if sgn(b) == 0:
        return f"y = {ex(k)}·x"
    sign = "+" if sgn(b) > 0 else "-"
    return f"y = {ex(k)}·x {sign} {ex(abs(b))}"


def line_through(p, q) -> Tuple[sp.Expr, sp.Expr, sp.Expr]:
    """Коэффициенты (A, B, C) прямой через две точки плоскости."""
    A = q[1] - p[1]
    B = p[0] - q[0]
    C = -(A * p[0] + B * p[1])
    return simp(A), simp(B), simp(C)


def parse_point(p, dim: int = 2):
    pt = [parse_number(c) for c in p]
    if len(pt) != dim:
        raise ValueError(f"Ожидалась точка с {dim} координатами")
    return tuple(pt)
