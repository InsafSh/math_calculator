"""
Geometry Core - Аналитическая геометрия в пространстве (Глава 4)
Символьные и числовые расчеты с пошаговыми объяснениями на русском языке.
Использует красивый Unicode вывод с реальными знаками корней (√), степенями (²) и индексами (₀).
"""

import sympy as sp
import numpy as np
import re
from typing import Tuple, List, Dict, Any, Optional

x, y, z, t = sp.symbols('x y z t', real=True)


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
    s = str(val_str).strip().replace(',', '.')
    # Поддерживаем ввод реального корня √
    s = s.replace('√', 'sqrt')
    if not s:
        raise ValueError("Пустое значение")
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
    expr = sp.sympify(s, locals=allowed_locals)
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


class PlaneSolver:
    """Решатель уравнений плоскости во всех аналитических случаях."""

    @staticmethod
    def by_point_and_normal(x0, y0, z0, A, B, C) -> Dict[str, Any]:
        """Плоскость через точку M0 с вектором нормали n = (A, B, C)."""
        x0, y0, z0 = parse_number(x0), parse_number(y0), parse_number(z0)
        A, B, C = parse_number(A), parse_number(B), parse_number(C)

        if A == 0 and B == 0 and C == 0:
            raise ValueError("Вектор нормали n⃗ не может быть нулевым (0, 0, 0)!")

        D = -(A * x0 + B * y0 + C * z0)
        As, Bs, Cs, Ds, eq_str = simplify_plane_eq(A, B, C, D)

        steps = [
            "📌 ЭТАП 1. ТЕОРЕТИЧЕСКАЯ ФОРМУЛА",
            "Уравнение плоскости, проходящей через точку M₀(x₀, y₀, z₀) перпендикулярно вектору нормали n⃗ = (A, B, C):",
            "   ┌────────────────────────────────────────────────────────┐",
            "   │   A·(x - x₀) + B·(y - y₀) + C·(z - z₀) = 0             │",
            "   └────────────────────────────────────────────────────────┘",
            "",
            "📝 ЭТАП 2. ПОДСТАНОВКА ИСХОДНЫХ ДАННЫХ",
            f"   ▸ Опорная точка M₀: ({fmt_num(x0)}; {fmt_num(y0)}; {fmt_num(z0)})",
            f"   ▸ Нормальный вектор n⃗: ({fmt_num(A)}; {fmt_num(B)}; {fmt_num(C)})",
            f"   {A}·(x - ({x0})) + {B}·(y - ({y0})) + {C}·(z - ({z0})) = 0",
            "",
            "⚙️ ЭТАП 3. РАСКРЫТИЕ СКОБОК И ВЫЧИСЛЕНИЯ",
            f"   {A}x - ({A * x0}) + {B}y - ({B * y0}) + {C}z - ({C * z0}) = 0",
            f"   Свободный член D = -({A}·({x0}) + {B}·({y0}) + {C}·({z0})) = {D}",
            "",
            "🎯 ИТОГОВЫЙ ОТВЕТ: ОБЩЕЕ УРАВНЕНИЕ ПЛОСКОСТИ",
            "   ╔════════════════════════════════════════════════════════╗",
            f"   ║   {eq_str:<50}   ║",
            "   ╚════════════════════════════════════════════════════════╝"
        ]

        return {
            'A': As, 'B': Bs, 'C': Cs, 'D': Ds,
            'equation_str': eq_str,
            'steps': "\n".join(steps),
            'point': (x0, y0, z0),
            'normal': (As, Bs, Cs)
        }

    @staticmethod
    def by_three_points(p1, p2, p3) -> Dict[str, Any]:
        """Уравнение плоскости через 3 точки M1, M2, M3."""
        x1, y1, z1 = [parse_number(c) for c in p1]
        x2, y2, z2 = [parse_number(c) for c in p2]
        x3, y3, z3 = [parse_number(c) for c in p3]

        u1, u2, u3 = x2 - x1, y2 - y1, z2 - z1
        v1, v2, v3 = x3 - x1, y3 - y1, z3 - z1

        A = u2 * v3 - u3 * v2
        B = u3 * v1 - u1 * v3
        C = u1 * v2 - u2 * v1

        if A == 0 and B == 0 and C == 0:
            raise ValueError("Данные 3 точки лежат на одной прямой (коллинеарны)! Плоскость не может быть задана однозначно.")

        D = -(A * x1 + B * y1 + C * z1)
        As, Bs, Cs, Ds, eq_str = simplify_plane_eq(A, B, C, D)

        steps = [
            "📌 ЭТАП 1. ТЕОРЕТИЧЕСКАЯ ФОРМУЛА",
            "Уравнение плоскости через три точки задается определителем 3-го порядка:",
            "   ┌  x - x₁   y - y₁   z - z₁ ┐",
            "   │ x₂ - x₁  y₂ - y₁  z₂ - z₁ │ = 0",
            "   └ x₃ - x₁  y₃ - y₁  z₃ - z₁ ┘",
            "",
            "📝 ЭТАП 2. НАПРАВЛЯЮЩИЕ ВЕКТОРЫ В ПЛОСКОСТИ",
            f"   ▸ Вектор u⃗ = M₁M₂⃗ = ({x2}-{x1}; {y2}-{y1}; {z2}-{z1}) = ({u1}; {u2}; {u3})",
            f"   ▸ Вектор v⃗ = M₁M₃⃗ = ({x3}-{x1}; {y3}-{y1}; {z3}-{z1}) = ({v1}; {v2}; {v3})",
            "",
            "⚙️ ЭТАП 3. ВЕКТОР НОРМАЛИ n⃗ = u⃗ × v⃗",
            "   │  i⃗    j⃗    k⃗ │",
            f"   │ {str(u1):>3}  {str(u2):>3}  {str(u3):>3} │",
            f"   │ {str(v1):>3}  {str(v2):>3}  {str(v3):>3} │",
            f"   A = ({u2})·({v3}) - ({u3})·({v2}) = {A}",
            f"   B = ({u3})·({v1}) - ({u1})·({v3}) = {B}",
            f"   C = ({u1})·({v2}) - ({u2})·({v1}) = {C}",
            f"   Нормальный вектор: n⃗ = ({A}; {B}; {C})",
            f"   Свободный член D = -({A}·({x1}) + {B}·({y1}) + {C}·({z1})) = {D}",
            "",
            "🎯 ИТОГОВЫЙ ОТВЕТ: ОБЩЕЕ УРАВНЕНИЕ ПЛОСКОСТИ",
            "   ╔════════════════════════════════════════════════════════╗",
            f"   ║   {eq_str:<50}   ║",
            "   ╚════════════════════════════════════════════════════════╝"
        ]

        return {
            'A': As, 'B': Bs, 'C': Cs, 'D': Ds,
            'equation_str': eq_str,
            'steps': "\n".join(steps),
            'points': [(x1, y1, z1), (x2, y2, z2), (x3, y3, z3)],
            'normal': (As, Bs, Cs)
        }

    @staticmethod
    def in_intercepts(a, b, c) -> Dict[str, Any]:
        """Уравнение плоскости в отрезках на осях: x/a + y/b + z/c = 1"""
        a, b, c = parse_number(a), parse_number(b), parse_number(c)
        if a == 0 or b == 0 or c == 0:
            raise ValueError("Отрезки на осях a, b, c не могут быть равны нулю!")

        A = b * c
        B = a * c
        C = a * b
        D = -a * b * c

        As, Bs, Cs, Ds, eq_str = simplify_plane_eq(A, B, C, D)

        steps = [
            "📌 ЭТАП 1. ТЕОРЕТИЧЕСКАЯ ФОРМУЛА В ОТРЕЗКАХ",
            "   ┌────────────────────────────────────────────────────────┐",
            "   │   x / a  +  y / b  +  z / c  =  1                      │",
            "   └────────────────────────────────────────────────────────┘",
            f"   где a = {fmt_num(a)} (по Ox), b = {fmt_num(b)} (по Oy), c = {fmt_num(c)} (по Oz).",
            "",
            "📝 ЭТАП 2. ПРИВЕДЕНИЕ К ОБЩЕМУ ЗНАМЕНАТЕЛЮ (abc)",
            f"   Умножаем обе части на a·b·c = {a * b * c}:",
            f"   ({b}·{c})x + ({a}·{c})y + ({a}·{b})z - ({a}·{b}·{c}) = 0",
            f"   {A}x + {B}y + {C}z + ({D}) = 0",
            "",
            "🎯 ИТОГОВЫЙ ОТВЕТ: ОБЩЕЕ УРАВНЕНИЕ ПЛОСКОСТИ",
            "   ╔════════════════════════════════════════════════════════╗",
            f"   ║   {eq_str:<50}   ║",
            "   ╚════════════════════════════════════════════════════════╝"
        ]

        return {
            'A': As, 'B': Bs, 'C': Cs, 'D': Ds,
            'equation_str': eq_str,
            'steps': "\n".join(steps),
            'intercepts': (a, b, c),
            'normal': (As, Bs, Cs)
        }

    @staticmethod
    def by_point_and_two_vectors(p0, v_u, v_v) -> Dict[str, Any]:
        """Плоскость через точку M0 параллельно векторам u и v."""
        x0, y0, z0 = [parse_number(c_) for c_ in p0]
        u1, u2, u3 = [parse_number(c_) for c_ in v_u]
        v1, v2, v3 = [parse_number(c_) for c_ in v_v]

        A = u2 * v3 - u3 * v2
        B = u3 * v1 - u1 * v3
        C = u1 * v2 - u2 * v1

        if A == 0 and B == 0 and C == 0:
            raise ValueError("Векторы u⃗ и v⃗ коллинеарны (параллельны друг другу)! Они не задают плоскость.")

        D = -(A * x0 + B * y0 + C * z0)
        As, Bs, Cs, Ds, eq_str = simplify_plane_eq(A, B, C, D)

        steps = [
            "📌 ЭТАП 1. ТЕОРЕТИЧЕСКАЯ ФОРМУЛА",
            "Нормальный вектор плоскости перпендикулярен направляющим векторам: n⃗ = u⃗ × v⃗",
            "",
            "📝 ЭТАП 2. ВЫЧИСЛЕНИЕ ВЕКТОРНОГО ПРОИЗВЕДЕНИЯ u⃗ × v⃗",
            f"   u⃗ = ({u1}; {u2}; {u3}),  v⃗ = ({v1}; {v2}; {v3})",
            f"   A = ({u2})·({v3}) - ({u3})·({v2}) = {A}",
            f"   B = ({u3})·({v1}) - ({u1})·({v3}) = {B}",
            f"   C = ({u1})·({v2}) - ({u2})·({v1}) = {C}",
            f"   Вектор нормали: n⃗ = ({A}; {B}; {C})",
            "",
            "⚙️ ЭТАП 3. СОСТАВЛЕНИЕ УРАВНЕНИЯ ЧЕРЕЗ ТОЧКУ M₀",
            f"   {A}·(x - ({x0})) + {B}·(y - ({y0})) + {C}·(z - ({z0})) = 0",
            f"   D = -({A}·{x0} + {B}·{y0} + {C}·{z0}) = {D}",
            "",
            "🎯 ИТОГОВЫЙ ОТВЕТ: ОБЩЕЕ УРАВНЕНИЕ ПЛОСКОСТИ",
            "   ╔════════════════════════════════════════════════════════╗",
            f"   ║   {eq_str:<50}   ║",
            "   ╚════════════════════════════════════════════════════════╝"
        ]

        return {
            'A': As, 'B': Bs, 'C': Cs, 'D': Ds,
            'equation_str': eq_str,
            'steps': "\n".join(steps),
            'point': (x0, y0, z0),
            'normal': (As, Bs, Cs)
        }

    @staticmethod
    def by_point_parallel_to_plane(p0, A1, B1, C1, D1) -> Dict[str, Any]:
        """Плоскость через точку M0 параллельно другой плоскости."""
        x0, y0, z0 = [parse_number(c_) for c_ in p0]
        A1, B1, C1, D1 = [parse_number(c_) for c_ in (A1, B1, C1, D1)]

        if A1 == 0 and B1 == 0 and C1 == 0:
            raise ValueError("Коэффициенты A=B=C=0 не задают плоскость!")

        A, B, C = A1, B1, C1
        D = -(A * x0 + B * y0 + C * z0)
        As, Bs, Cs, Ds, eq_str = simplify_plane_eq(A, B, C, D)

        steps = [
            "📌 ЭТАП 1. ТЕОРЕТИЧЕСКАЯ ПРЕДПОСЫЛКА",
            "Параллельные плоскости имеют одинаковый вектор нормали: n⃗₁ = n⃗₂ = (A, B, C).",
            f"Исходная плоскость: {A1}x + {B1}y + {C1}z + {D1} = 0  ⟹  n⃗ = ({A1}; {B1}; {C1})",
            "",
            "📝 ЭТАП 2. СОСТАВЛЕНИЕ УРАВНЕНИЯ ПАРАЛЛЕЛЬНОЙ ПЛОСКОСТИ",
            f"   {A1}·(x - ({x0})) + {B1}·(y - ({y0})) + {C1}·(z - ({z0})) = 0",
            f"   D = -({A1}·{x0} + {B1}·{y0} + {C1}·{z0}) = {D}",
            "",
            "🎯 ИТОГОВЫЙ ОТВЕТ: УРАВНЕНИЕ ПАРАЛЛЕЛЬНОЙ ПЛОСКОСТИ",
            "   ╔════════════════════════════════════════════════════════╗",
            f"   ║   {eq_str:<50}   ║",
            "   ╚════════════════════════════════════════════════════════╝"
        ]

        return {
            'A': As, 'B': Bs, 'C': Cs, 'D': Ds,
            'equation_str': eq_str,
            'steps': "\n".join(steps),
            'point': (x0, y0, z0),
            'normal': (As, Bs, Cs)
        }

    @staticmethod
    def by_point_perp_two_planes(p0, pl1, pl2) -> Dict[str, Any]:
        """Плоскость через точку M0 перпендикулярно двум плоскостям."""
        x0, y0, z0 = [parse_number(c_) for c_ in p0]
        A1, B1, C1, _ = [parse_number(c_) for c_ in pl1]
        A2, B2, C2, _ = [parse_number(c_) for c_ in pl2]

        A = B1 * C2 - C1 * B2
        B = C1 * A2 - A1 * C2
        C = A1 * B2 - B1 * A2

        if A == 0 and B == 0 and C == 0:
            raise ValueError("Две заданные плоскости параллельны между собой! Единственная перпендикулярная плоскость не определена.")

        D = -(A * x0 + B * y0 + C * z0)
        As, Bs, Cs, Ds, eq_str = simplify_plane_eq(A, B, C, D)

        steps = [
            "📌 ЭТАП 1. ТЕОРЕТИЧЕСКАЯ ФОРМУЛА",
            "Нормаль искомой плоскости перпендикулярна нормалям исходных плоскостей: n⃗ = n⃗₁ × n⃗₂",
            "",
            "📝 ЭТАП 2. ВЫЧИСЛЕНИЕ ВЕКТОРНОГО ПРОИЗВЕДЕНИЯ n⃗₁ × n⃗₂",
            f"   n⃗₁ = ({A1}; {B1}; {C1}),  n⃗₂ = ({A2}; {B2}; {C2})",
            f"   A = ({B1})·({C2}) - ({C1})·({B2}) = {A}",
            f"   B = ({C1})·({A2}) - ({A1})·({C2}) = {B}",
            f"   C = ({A1})·({B2}) - ({B1})·({A2}) = {C}",
            f"   Вектор нормали: n⃗ = ({A}; {B}; {C})",
            f"   Свободный член D = -({A}·{x0} + {B}·{y0} + {C}·{z0}) = {D}",
            "",
            "🎯 ИТОГОВЫЙ ОТВЕТ: УРАВНЕНИЕ ПЛОСКОСТИ",
            "   ╔════════════════════════════════════════════════════════╗",
            f"   ║   {eq_str:<50}   ║",
            "   ╚════════════════════════════════════════════════════════╝"
        ]

        return {
            'A': As, 'B': Bs, 'C': Cs, 'D': Ds,
            'equation_str': eq_str,
            'steps': "\n".join(steps),
            'point': (x0, y0, z0),
            'normal': (As, Bs, Cs)
        }

    @staticmethod
    def by_line_and_point(line_m0, line_s, p_ext) -> Dict[str, Any]:
        """Плоскость через прямую L(M_L, s) и точку M1 вне неё."""
        x0, y0, z0 = [parse_number(c_) for c_ in line_m0]
        m, p, q = [parse_number(c_) for c_ in line_s]
        x1, y1, z1 = [parse_number(c_) for c_ in p_ext]

        w1, w2, w3 = x1 - x0, y1 - y0, z1 - z0
        A = p * w3 - q * w2
        B = q * w1 - m * w3
        C = m * w2 - p * w1

        if A == 0 and B == 0 and C == 0:
            raise ValueError("Точка принадлежит самой прямой! Через прямую и точку на ней проходит бесконечно много плоскостей.")

        D = -(A * x0 + B * y0 + C * z0)
        As, Bs, Cs, Ds, eq_str = simplify_plane_eq(A, B, C, D)

        steps = [
            "📌 ЭТАП 1. АНАЛИЗ УСЛОВИЯ",
            f"   ▸ Прямая L: точка M_L({x0}; {y0}; {z0}), направляющий вектор s⃗ = ({m}; {p}; {q})",
            f"   ▸ Точка вне прямой: M₁({x1}; {y1}; {z1})",
            f"   ▸ Вектор w⃗ = M_L M₁⃗ = ({w1}; {w2}; {w3})",
            "",
            "📝 ЭТАП 2. ВЫЧИСЛЕНИЕ ВЕКТОРА НОРМАЛИ n⃗ = s⃗ × w⃗",
            f"   A = ({p})·({w3}) - ({q})·({w2}) = {A}",
            f"   B = ({q})·({w1}) - ({m})·({w3}) = {B}",
            f"   C = ({m})·({w2}) - ({p})·({w1}) = {C}",
            f"   Нормальный вектор: n⃗ = ({A}; {B}; {C})",
            f"   Свободный член D = {D}",
            "",
            "🎯 ИТОГОВЫЙ ОТВЕТ: УРАВНЕНИЕ ПЛОСКОСТИ",
            "   ╔════════════════════════════════════════════════════════╗",
            f"   ║   {eq_str:<50}   ║",
            "   ╚════════════════════════════════════════════════════════╝"
        ]

        return {
            'A': As, 'B': Bs, 'C': Cs, 'D': Ds,
            'equation_str': eq_str,
            'steps': "\n".join(steps),
            'point': (x0, y0, z0),
            'normal': (As, Bs, Cs)
        }

    @staticmethod
    def normal_form(A, B, C, D) -> Dict[str, Any]:
        """Приведение к нормальному виду: x·cos(α) + y·cos(β) + z·cos(γ) - p = 0"""
        A, B, C, D = [parse_number(c_) for c_ in (A, B, C, D)]
        len_n_sq = A**2 + B**2 + C**2
        if len_n_sq == 0:
            raise ValueError("A, B, C не могут одновременно равняться 0!")

        len_n = sp.sqrt(len_n_sq)
        sign = 1 if D <= 0 else -1
        mu = sign / len_n

        cos_alpha = A * mu
        cos_beta = B * mu
        cos_gamma = C * mu
        p_dist = -D * mu

        # Формируем уравнение
        norm_eq = f"({fmt_num(cos_alpha)})x + ({fmt_num(cos_beta)})y + ({fmt_num(cos_gamma)})z - ({fmt_num(p_dist)}) = 0"

        steps = [
            "📌 ЭТАП 1. ТЕОРЕТИЧЕСКАЯ ФОРМУЛА",
            "Нормальное уравнение плоскости имеет вид:",
            "   ┌────────────────────────────────────────────────────────┐",
            "   │   x·cos(α) + y·cos(β) + z·cos(γ) - p = 0,   (p ≥ 0)    │",
            "   └────────────────────────────────────────────────────────┘",
            "где cos²(α) + cos²(β) + cos²(γ) = 1, а p — расстояние от начала координат O(0,0,0) до плоскости.",
            "",
            "📝 ЭТАП 2. ВЫЧИСЛЕНИЕ НОРМИРУЮЩЕГО МНОЖИТЕЛЯ μ",
            "   μ = ± 1 / √(A² + B² + C²)",
            f"   Длина нормали |n⃗| = √({A}² + {B}² + {C}²) = √{len_n_sq} = {fmt_num(len_n)}",
            f"   Так как D = {D}, выбираем знак μ: {'+' if sign > 0 else '-'}",
            f"   μ = {fmt_num(mu)}",
            "",
            "⚙️ ЭТАП 3. НАПРАВЛЯЮЩИЕ КОСИНУСЫ И РАССТОЯНИЕ p",
            f"   ▸ cos(α) = A · μ = {fmt_num(cos_alpha)}",
            f"   ▸ cos(β) = B · μ = {fmt_num(cos_beta)}",
            f"   ▸ cos(γ) = C · μ = {fmt_num(cos_gamma)}",
            f"   ▸ Расстояние p = -D · μ = {fmt_num(p_dist)}",
            "",
            "🎯 ИТОГОВЫЙ ОТВЕТ: НОРМАЛЬНОЕ УРАВНЕНИЕ",
            "   ╔══════════════════════════════════════════════════════════════════╗",
            f"   ║   {norm_eq:<60}   ║",
            "   ╚══════════════════════════════════════════════════════════════════╝"
        ]

        return {
            'mu': mu,
            'cos_alpha': cos_alpha,
            'cos_beta': cos_beta,
            'cos_gamma': cos_gamma,
            'p': p_dist,
            'steps': "\n".join(steps)
        }


class LineSolver:
    """Решатель аналитических задач на прямую в пространстве."""

    @staticmethod
    def by_point_and_vector(x0, y0, z0, m, p, q) -> Dict[str, Any]:
        """Канонические и параметрические уравнения по точке M0 и вектору s=(m, p, q)."""
        x0, y0, z0 = parse_number(x0), parse_number(y0), parse_number(z0)
        m, p, q = parse_number(m), parse_number(p), parse_number(q)

        if m == 0 and p == 0 and q == 0:
            raise ValueError("Направляющий вектор s⃗ не может быть нулевым (0, 0, 0)!")

        s_coeffs = [m, p, q]
        if all(sp.sympify(c_).is_rational for c_ in s_coeffs):
            lcm_d = sp.ilcm(*[sp.Rational(c_).q for c_ in s_coeffs if c_ != 0] or [1])
            int_s = [sp.Integer(sp.Rational(c_) * lcm_d) for c_ in s_coeffs]
            gcd_s = sp.igcd(*[c_ for c_ in int_s if c_ != 0] or [1])
            m_s, p_s, q_s = [c_ // gcd_s for c_ in int_s]
        else:
            m_s, p_s, q_s = m, p, q

        def coord_term(c):
            if c > 0: return f"x - {c}"
            elif c < 0: return f"x + {abs(c)}"
            return "x"

        term_x = coord_term(x0)
        term_y = coord_term(y0).replace('x', 'y')
        term_z = coord_term(z0).replace('x', 'z')

        canonical_str = f"({term_x}) / {m_s} = ({term_y}) / {p_s} = ({term_z}) / {q_s}"

        def param_term(coord0, dir_c):
            if dir_c == 0:
                return f"{coord0}"
            sign = "+ " if dir_c > 0 else "- "
            val = abs(dir_c)
            t_part = "t" if val == 1 else f"{val}t"
            if coord0 == 0:
                return f"{'-' if dir_c < 0 else ''}{t_part}"
            return f"{coord0} {sign}{t_part}"

        p_x = param_term(x0, m_s)
        p_y = param_term(y0, p_s)
        p_z = param_term(z0, q_s)

        steps = [
            "📌 ЭТАП 1. КАНОНИЧЕСКИЕ УРАВНЕНИЯ ПРЯМОЙ",
            "Уравнения прямой через точку M₀(x₀, y₀, z₀) с вектором s⃗ = (m, p, q):",
            "   ┌────────────────────────────────────────────────────────┐",
            "   │   (x - x₀) / m  =  (y - y₀) / p  =  (z - z₀) / q       │",
            "   └────────────────────────────────────────────────────────┘",
            f"   ▸ Опорная точка M₀: ({x0}; {y0}; {z0})",
            f"   ▸ Направляющий вектор s⃗: ({m_s}; {p_s}; {q_s})",
            "",
            "🎯 КАНОНИЧЕСКИЙ ВИД:",
            f"   ⟹  {canonical_str}",
            "",
            "📌 ЭТАП 2. ПАРАМЕТРИЧЕСКИЕ УРАВНЕНИЯ ПРЯМОЙ",
            "Приравнивая каждое отношение к параметру t:",
            "   ╔════════════════════════════════════════════════════════╗",
            f"   ║   x = {p_x:<48} ║",
            f"   ║   y = {p_y:<48} ║",
            f"   ║   z = {p_z:<48} ║",
            "   ╚════════════════════════════════════════════════════════╝"
        ]

        return {
            'M0': (x0, y0, z0),
            's': (m_s, p_s, q_s),
            'canonical_str': canonical_str,
            'param_str': f"x = {p_x}, y = {p_y}, z = {p_z}",
            'steps': "\n".join(steps)
        }

    @staticmethod
    def by_two_points(p1, p2) -> Dict[str, Any]:
        """Прямая через две точки M1 и M2."""
        x1, y1, z1 = [parse_number(c_) for c_ in p1]
        x2, y2, z2 = [parse_number(c_) for c_ in p2]

        m, p, q = x2 - x1, y2 - y1, z2 - z1
        if m == 0 and p == 0 and q == 0:
            raise ValueError("Точки M₁ и M₂ совпадают! Прямую провести невозможно.")

        res = LineSolver.by_point_and_vector(x1, y1, z1, m, p, q)
        prefix = [
            "📝 ВЫЧИСЛЕНИЕ НАПРАВЛЯЮЩЕГО ВЕКТОРА s⃗ = M₁M₂⃗",
            f"   s⃗ = ({x2} - ({x1});  {y2} - ({y1});  {z2} - ({z1})) = ({m}; {p}; {q})",
            ""
        ]
        res['steps'] = "\n".join(prefix) + res['steps']
        res['points'] = [(x1, y1, z1), (x2, y2, z2)]
        return res

    @staticmethod
    def from_general_to_canonical(pl1, pl2) -> Dict[str, Any]:
        """Перевод общих уравнений прямой в канонические."""
        A1, B1, C1, D1 = [parse_number(c_) for c_ in pl1]
        A2, B2, C2, D2 = [parse_number(c_) for c_ in pl2]

        m = B1 * C2 - C1 * B2
        p = C1 * A2 - A1 * C2
        q = A1 * B2 - B1 * A2

        if m == 0 and p == 0 and q == 0:
            raise ValueError("Плоскости параллельны или совпадают — они не пересекаются по единственной прямой!")

        det_xy = A1 * B2 - A2 * B1
        det_xz = A1 * C2 - A2 * C1
        det_yz = B1 * C2 - B2 * C1

        if det_xy != 0:
            z0 = sp.Integer(0)
            x0 = (B1 * D2 - B2 * D1) / det_xy
            y0 = (A2 * D1 - A1 * D2) / det_xy
            fixed_var = "z₀ = 0"
        elif det_xz != 0:
            y0 = sp.Integer(0)
            x0 = (C1 * D2 - C2 * D1) / det_xz
            z0 = (A2 * D1 - A1 * D2) / det_xz
            fixed_var = "y₀ = 0"
        else:
            x0 = sp.Integer(0)
            y0 = (C1 * D2 - C2 * D1) / det_yz
            z0 = (B2 * D1 - B1 * D2) / det_yz
            fixed_var = "x₀ = 0"

        line_res = LineSolver.by_point_and_vector(x0, y0, z0, m, p, q)

        steps = [
            "📌 ЭТАП 1. НАХОЖДЕНИЕ НАПРАВЛЯЮЩЕГО ВЕКТОРА s⃗ = n⃗₁ × n⃗₂",
            f"   P₁: {A1}x + {B1}y + {C1}z + {D1} = 0  ⟹  n⃗₁ = ({A1}; {B1}; {C1})",
            f"   P₂: {A2}x + {B2}y + {C2}z + {D2} = 0  ⟹  n⃗₂ = ({A2}; {B2}; {C2})",
            f"   s⃗ = n⃗₁ × n⃗₂ = ({m}; {p}; {q})",
            "",
            "📝 ЭТАП 2. НАХОЖДЕНИЕ ЧАСТНОЙ ТОЧКИ M₀",
            f"   Положим {fixed_var}. Решая систему двух уравнений с двумя неизвестными:",
            f"   Получаем точку M₀ = {fmt_point((x0, y0, z0))}",
            "",
            line_res['steps']
        ]

        return {
            'M0': (x0, y0, z0),
            's': (m, p, q),
            'canonical_str': line_res['canonical_str'],
            'param_str': line_res['param_str'],
            'steps': "\n".join(steps)
        }


class RelationsSolver:
    """Решатель взаимного расположения плоскостей и прямых."""

    @staticmethod
    def two_planes(pl1, pl2) -> Dict[str, Any]:
        """Взаимное расположение двух плоскостей."""
        A1, B1, C1, D1 = [parse_number(c_) for c_ in pl1]
        A2, B2, C2, D2 = [parse_number(c_) for c_ in pl2]

        cx = B1 * C2 - C1 * B2
        cy = C1 * A2 - A1 * C2
        cz = A1 * B2 - B1 * A2

        is_parallel = (cx == 0 and cy == 0 and cz == 0)

        len1_sq = A1**2 + B1**2 + C1**2
        len2_sq = A2**2 + B2**2 + C2**2
        len1 = sp.sqrt(len1_sq)
        len2 = sp.sqrt(len2_sq)

        dot_p = A1 * A2 + B1 * B2 + C1 * C2

        if is_parallel:
            k = None
            if A2 != 0: k = A1 / A2
            elif B2 != 0: k = B1 / B2
            elif C2 != 0: k = C1 / C2

            is_coincident = (D1 == k * D2)
            if is_coincident:
                status = "Плоскости совпадают (одна и та же плоскость)"
                dist = sp.Integer(0)
            else:
                status = "Плоскости строго параллельны (не совпадают)"
                dist = sp.Abs(D1 - k * D2) / len1

            steps = [
                "📌 ЭТАП 1. ПРОВЕРКА УСЛОВИЯ ПАРАЛЛЕЛЬНОСТИ",
                "Условие параллельности плоскостей — коллинеарность нормалей n⃗₁ и n⃗₂:",
                "   A₁ / A₂ = B₁ / B₂ = C₁ / C₂ = k",
                f"   Векторное произведение n⃗₁ × n⃗₂ = ({cx}; {cy}; {cz}) = 0.",
                f"   Коэффициент пропорциональности: k = {k}",
                "",
                "🎯 РЕЗУЛЬТАТ ВЗАИМНОГО РАСПОЛОЖЕНИЯ:",
                "   ╔════════════════════════════════════════════════════════╗",
                f"   ║   {status:<50}   ║",
                "   ╚════════════════════════════════════════════════════════╝"
            ]
            if not is_coincident:
                steps.extend([
                    "",
                    "📏 РАССТОЯНИЕ МЕЖДУ ПАРАЛЛЕЛЬНЫМИ ПЛОСКОСТЯМИ:",
                    "   d = |D₁ - k·D₂| / √(A₁² + B₁² + C₁²)",
                    f"   d = |{D1} - ({k})·({D2})| / √{len1_sq} = {fmt_num(dist)}"
                ])

            return {
                'status': status,
                'is_parallel': True,
                'is_coincident': is_coincident,
                'distance': dist,
                'steps': "\n".join(steps)
            }
        else:
            cos_phi = sp.Abs(dot_p) / (len1 * len2)
            angle_rad = sp.acos(cos_phi)
            angle_deg = float(angle_rad.evalf()) * 180.0 / np.pi
            is_perp = (dot_p == 0)

            status = "Плоскости взаимно перпендикулярны" if is_perp else "Плоскости пересекаются по прямой линии"
            line_data = LineSolver.from_general_to_canonical(pl1, pl2)

            b1_A = A1 / len1 - A2 / len2
            b1_B = B1 / len1 - B2 / len2
            b1_C = C1 / len1 - C2 / len2
            b1_D = D1 / len1 - D2 / len2
            _, _, _, _, bisector1_eq = simplify_plane_eq(b1_A, b1_B, b1_C, b1_D)

            b2_A = A1 / len1 + A2 / len2
            b2_B = B1 / len1 + B2 / len2
            b2_C = C1 / len1 + C2 / len2
            b2_D = D1 / len1 + D2 / len2
            _, _, _, _, bisector2_eq = simplify_plane_eq(b2_A, b2_B, b2_C, b2_D)

            steps = [
                "📌 ЭТАП 1. АНАЛИЗ НОРМАЛЬНЫХ ВЕКТОРОВ",
                f"   ▸ n⃗₁ = ({A1}; {B1}; {C1}),  |n⃗₁| = √{len1_sq} = {fmt_num(len1)}",
                f"   ▸ n⃗₂ = ({A2}; {B2}; {C2}),  |n⃗₂| = √{len2_sq} = {fmt_num(len2)}",
                f"   ▸ Скалярное произведение n⃗₁ · n⃗₂ = ({A1})·({A2}) + ({B1})·({B2}) + ({C1})·({C2}) = {dot_p}",
                "",
                "📐 ЭТАП 2. УГОЛ МЕЖДУ ПЛОСКОСТЯМИ",
                "   cos(φ) = |n⃗₁ · n⃗₂| / (|n⃗₁| · |n⃗₂|)",
                f"   cos(φ) = |{dot_p}| / ({fmt_num(len1)} · {fmt_num(len2)}) = {fmt_num(cos_phi)}",
                f"   φ = {angle_deg:.2f}°  ({float(angle_rad.evalf()):.4f} рад)",
                "",
                "🎯 РЕЗУЛЬТАТ: ВЗАИМНОЕ РАСПОЛОЖЕНИЕ",
                "   ╔════════════════════════════════════════════════════════╗",
                f"   ║   {status:<50}   ║",
                "   ╚════════════════════════════════════════════════════════╝",
                "",
                "📏 ПРЯМАЯ ПЕРЕСЕЧЕНИЯ ПЛОСКОСТЕЙ:",
                f"   Канонический вид: {line_data['canonical_str']}",
                f"   Параметрический:  {line_data['param_str']}",
                "",
                "📐 УРАВНЕНИЯ БИССЕКТОРНЫХ ПЛОСКОСТЕЙ:",
                f"   Биссектриса 1: {bisector1_eq}",
                f"   Биссектриса 2: {bisector2_eq}"
            ]

            return {
                'status': status,
                'is_parallel': False,
                'is_perpendicular': is_perp,
                'cos_angle': cos_phi,
                'angle_deg': angle_deg,
                'intersection_line': line_data,
                'bisectors': (bisector1_eq, bisector2_eq),
                'steps': "\n".join(steps)
            }

    @staticmethod
    def line_and_plane(line_m0, line_s, pl) -> Dict[str, Any]:
        """Взаимное расположение прямой и плоскости."""
        x0, y0, z0 = [parse_number(c_) for c_ in line_m0]
        m, p, q = [parse_number(c_) for c_ in line_s]
        A, B, C, D = [parse_number(c_) for c_ in pl]

        dot_ns = A * m + B * p + C * q
        len_n_sq = A**2 + B**2 + C**2
        len_s_sq = m**2 + p**2 + q**2
        len_n = sp.sqrt(len_n_sq)
        len_s = sp.sqrt(len_s_sq)

        val_m0 = A * x0 + B * y0 + C * z0 + D

        if dot_ns == 0:
            if val_m0 == 0:
                status = "Прямая целиком лежит в плоскости"
                steps = [
                    "📌 ЭТАП 1. ПРОВЕРКА УСЛОВИЯ ОРТОГОНАЛЬНОСТИ ВЕКТОРОВ",
                    f"   n⃗ · s⃗ = ({A})·({m}) + ({B})·({p}) + ({C})·({q}) = 0",
                    "   Вектор направления прямой перпендикулярен нормали плоскости.",
                    "",
                    "📝 ЭТАП 2. ПРОВЕРКА ПРИНАДЛЕЖНОСТИ ОПОРНОЙ ТОЧКИ M₀",
                    f"   A·x₀ + B·y₀ + C·z₀ + D = {val_m0} = 0",
                    "",
                    "🎯 РЕЗУЛЬТАТ:",
                    "   ╔════════════════════════════════════════════════════════╗",
                    f"   ║   {status:<50}   ║",
                    "   ╚════════════════════════════════════════════════════════╝"
                ]
                return {
                    'status': status,
                    'is_in_plane': True,
                    'is_parallel': False,
                    'steps': "\n".join(steps)
                }
            else:
                status = "Прямая строго параллельна плоскости"
                dist = sp.Abs(val_m0) / len_n
                steps = [
                    "📌 ЭТАП 1. ПРОВЕРКА УСЛОВИЯ ПАРАЛЛЕЛЬНОСТИ",
                    f"   n⃗ · s⃗ = ({A})·({m}) + ({B})·({p}) + ({C})·({q}) = 0",
                    f"   Опорная точка M₀({x0}; {y0}; {z0}) не лежит в плоскости: отклонение = {val_m0} ≠ 0.",
                    "",
                    "🎯 РЕЗУЛЬТАТ:",
                    "   ╔════════════════════════════════════════════════════════╗",
                    f"   ║   {status:<50}   ║",
                    "   ╚════════════════════════════════════════════════════════╝",
                    "",
                    "📏 РАССТОЯНИЕ ОТ ПРЯМОЙ ДО ПЛОСКОСТИ:",
                    "   d = |A·x₀ + B·y₀ + C·z₀ + D| / √(A² + B² + C²)",
                    f"   d = |{val_m0}| / √{len_n_sq} = {fmt_num(dist)}"
                ]
                return {
                    'status': status,
                    'is_in_plane': False,
                    'is_parallel': True,
                    'distance': dist,
                    'steps': "\n".join(steps)
                }
        else:
            t_inter = -val_m0 / dot_ns
            x_int = x0 + m * t_inter
            y_int = y0 + p * t_inter
            z_int = z0 + q * t_inter

            sin_theta = sp.Abs(dot_ns) / (len_n * len_s)
            theta_rad = sp.asin(sin_theta)
            theta_deg = float(theta_rad.evalf()) * 180.0 / np.pi

            cx = p * C - q * B
            cy = q * A - m * C
            cz = m * B - p * A
            is_perp = (cx == 0 and cy == 0 and cz == 0)

            status = "Прямая перпендикулярна плоскости" if is_perp else "Прямая пересекает плоскость в точке"

            proj_scale = (m * A + p * B + q * C) / len_n_sq
            s_proj_x = m - proj_scale * A
            s_proj_y = p - proj_scale * B
            s_proj_z = q - proj_scale * C

            pt_int_str = f"K({fmt_num(x_int)}; {fmt_num(y_int)}; {fmt_num(z_int)})"

            steps = [
                "📌 ЭТАП 1. ТОЧКА ПЕРЕСЕЧЕНИЯ ПРЯМОЙ И ПЛОСКОСТИ",
                "   Подставим x = x₀ + mt, y = y₀ + pt, z = z₀ + qt в уравнение плоскости:",
                f"   {A}·({x0} + ({m})t) + {B}·({y0} + ({p})t) + {C}·({z0} + ({q})t) + ({D}) = 0",
                f"   t = -({val_m0}) / ({dot_ns}) = {fmt_num(t_inter)}",
                "",
                "🎯 ТОЧКА ПЕРЕСЕЧЕНИЯ K:",
                "   ╔════════════════════════════════════════════════════════╗",
                f"   ║   {pt_int_str:<50}   ║",
                "   ╚════════════════════════════════════════════════════════╝",
                "",
                "📐 ЭТАП 2. УГОЛ МЕЖДУ ПРЯМОЙ И ПЛОСКОСТЬЮ",
                "   sin(θ) = |n⃗ · s⃗| / (|n⃗| · |s⃗|)",
                f"   sin(θ) = |{dot_ns}| / (√{len_n_sq} · √{len_s_sq}) = {fmt_num(sin_theta)}",
                f"   θ = {theta_deg:.2f}°  ({float(theta_rad.evalf()):.4f} рад)",
                "",
                "🎯 РЕЗУЛЬТАТ ВЗАИМНОГО РАСПОЛОЖЕНИЯ:",
                f"   {status}"
            ]

            return {
                'status': status,
                'intersection_point': (x_int, y_int, z_int),
                't_inter': t_inter,
                'angle_deg': theta_deg,
                'sin_theta': sin_theta,
                'is_perpendicular': is_perp,
                'projection_vector': (s_proj_x, s_proj_y, s_proj_z),
                'steps': "\n".join(steps)
            }

    @staticmethod
    def two_lines(l1_m, l1_s, l2_m, l2_s) -> Dict[str, Any]:
        """Взаимное расположение двух прямых в пространстве."""
        x1, y1, z1 = [parse_number(c_) for c_ in l1_m]
        m1, p1, q1 = [parse_number(c_) for c_ in l1_s]
        x2, y2, z2 = [parse_number(c_) for c_ in l2_m]
        m2, p2, q2 = [parse_number(c_) for c_ in l2_s]

        cx = p1 * q2 - q1 * p2
        cy = q1 * m2 - m1 * q2
        cz = m1 * p2 - p1 * m2

        len_cross_sq = cx**2 + cy**2 + cz**2
        len_cross = sp.sqrt(len_cross_sq)

        w1, w2, w3 = x2 - x1, y2 - y1, z2 - z1
        mixed_p = w1 * cx + w2 * cy + w3 * cz

        len_s1 = sp.sqrt(m1**2 + p1**2 + q1**2)
        len_s2 = sp.sqrt(m2**2 + p2**2 + q2**2)
        dot_s = m1 * m2 + p1 * p2 + q1 * q2
        cos_phi = sp.Abs(dot_s) / (len_s1 * len_s2)
        angle_deg = float(sp.acos(cos_phi).evalf()) * 180.0 / np.pi

        if len_cross == 0:
            wx = w2 * q1 - w3 * p1
            wy = w3 * m1 - w1 * q1
            wz = w1 * p1 - w2 * m1
            if wx == 0 and wy == 0 and wz == 0:
                status = "Прямые совпадают"
                dist = sp.Integer(0)
            else:
                status = "Прямые параллельны (не совпадают)"
                dist = sp.sqrt(wx**2 + wy**2 + wz**2) / len_s1

            steps = [
                "📌 ЭТАП 1. ПРОВЕРКА КОЛЛИНЕАРНОСТИ НАПРАВЛЯЮЩИХ ВЕКТОРОВ",
                f"   s⃗₁ × s⃗₂ = ({cx}; {cy}; {cz}) = 0.",
                "",
                "🎯 РЕЗУЛЬТАТ:",
                "   ╔════════════════════════════════════════════════════════╗",
                f"   ║   {status:<50}   ║",
                "   ╚════════════════════════════════════════════════════════╝"
            ]
            if status != "Прямые совпадают":
                steps.extend([
                    "",
                    "📏 РАССТОЯНИЕ МЕЖДУ ПАРАЛЛЕЛЬНЫМИ ПРЯМЫМИ:",
                    "   d = |M₁M₂⃗ × s⃗₁| / |s⃗₁|",
                    f"   d = {fmt_num(dist)}"
                ])
            return {
                'status': status,
                'is_parallel': True,
                'distance': dist,
                'steps': "\n".join(steps)
            }
        else:
            if mixed_p == 0:
                status = "Прямые пересекаются в единственной точке"
                det_sys = m1 * (-p2) - (-m2) * p1
                if det_sys != 0:
                    t_val = (w1 * (-p2) - (-m2) * w2) / det_sys
                else:
                    det_sys_z = p1 * (-q2) - (-p2) * q1
                    t_val = (w2 * (-q2) - (-p2) * w3) / det_sys_z

                xi = x1 + m1 * t_val
                yi = y1 + p1 * t_val
                zi = z1 + q1 * t_val
                pt_str = f"M_int({fmt_num(xi)}; {fmt_num(yi)}; {fmt_num(zi)})"

                steps = [
                    "📌 ЭТАП 1. ПРОВЕРКА КОМПЛАНАРНОСТИ (СМЕШАННОЕ ПРОИЗВЕДЕНИЕ)",
                    f"   (M₁M₂⃗, s⃗₁, s⃗₂) = {mixed_p} = 0  ⟹  прямые лежат в одной плоскости.",
                    "",
                    "🎯 РЕЗУЛЬТАТ:",
                    "   ╔════════════════════════════════════════════════════════╗",
                    f"   ║   {status:<50}   ║",
                    "   ╚════════════════════════════════════════════════════════╝",
                    "",
                    "📍 ТОЧКА ПЕРЕСЕЧЕНИЯ:",
                    f"   {pt_str}",
                    "",
                    "📐 УГОЛ МЕЖДУ ПРЯМЫМИ:",
                    f"   cos(φ) = {fmt_num(cos_phi)}  ⟹  φ = {angle_deg:.2f}°"
                ]

                return {
                    'status': status,
                    'is_intersecting': True,
                    'intersection_point': (xi, yi, zi),
                    'angle_deg': angle_deg,
                    'distance': sp.Integer(0),
                    'steps': "\n".join(steps)
                }
            else:
                status = "Прямые скрещиваются"
                dist = sp.Abs(mixed_p) / len_cross

                steps = [
                    "📌 ЭТАП 1. ПРОВЕРКА УСЛОВИЯ СКРЕЩИВАНИЯ",
                    f"   Смешанное произведение (M₁M₂⃗, s⃗₁, s⃗₂) = {mixed_p} ≠ 0.",
                    "   Прямые не лежат в одной плоскости и не пересекаются.",
                    "",
                    "🎯 РЕЗУЛЬТАТ:",
                    "   ╔════════════════════════════════════════════════════════╗",
                    f"   ║   {status:<50}   ║",
                    "   ╚════════════════════════════════════════════════════════╝",
                    "",
                    "📏 КРАТЧАЙШЕЕ РАССТОЯНИЕ МЕЖДУ СКРЕЩИВАЮЩИМИСЯ ПРЯМЫМИ:",
                    "   d = |(M₁M₂⃗, s⃗₁, s⃗₂)| / |s⃗₁ × s⃗₂|",
                    f"   |s⃗₁ × s⃗₂| = √{len_cross_sq} = {fmt_num(len_cross)}",
                    f"   d = |{mixed_p}| / {fmt_num(len_cross)} = {fmt_num(dist)}",
                    "",
                    "📐 УГОЛ МЕЖДУ НАПРАВЛЕНИЯМИ ПРЯМЫХ:",
                    f"   cos(φ) = {fmt_num(cos_phi)}  ⟹  φ = {angle_deg:.2f}°"
                ]

                return {
                    'status': status,
                    'is_skew': True,
                    'distance': dist,
                    'angle_deg': angle_deg,
                    'steps': "\n".join(steps)
                }


class DistancesAndProjections:
    """Вычисление расстояний, проекций и симметричных точек."""

    @staticmethod
    def point_to_plane(pt, pl) -> Dict[str, Any]:
        """Расстояние от точки до плоскости, проекция H и симметричная точка."""
        x0, y0, z0 = [parse_number(c_) for c_ in pt]
        A, B, C, D = [parse_number(c_) for c_ in pl]

        val = A * x0 + B * y0 + C * z0 + D
        len_sq = A**2 + B**2 + C**2
        len_n = sp.sqrt(len_sq)

        dist = sp.Abs(val) / len_n

        t_proj = -val / len_sq
        Hx = x0 + t_proj * A
        Hy = y0 + t_proj * B
        Hz = z0 + t_proj * C

        Sx = x0 + 2 * t_proj * A
        Sy = y0 + 2 * t_proj * B
        Sz = z0 + 2 * t_proj * C

        h_str = f"H({fmt_num(Hx)}; {fmt_num(Hy)}; {fmt_num(Hz)})"
        sym_str = f"M'({fmt_num(Sx)}; {fmt_num(Sy)}; {fmt_num(Sz)})"

        steps = [
            "📌 ЭТАП 1. ТЕОРЕТИЧЕСКАЯ ФОРМУЛА РАССТОЯНИЯ",
            "   ┌────────────────────────────────────────────────────────┐",
            "   │   d = |A·x₀ + B·y₀ + C·z₀ + D| / √(A² + B² + C²)       │",
            "   └────────────────────────────────────────────────────────┘",
            f"   ▸ Числитель (отклонение Δ): {A}·({x0}) + {B}·({y0}) + {C}·({z0}) + ({D}) = {val}",
            f"   ▸ Длина нормали |n⃗|: √({A}² + {B}² + {C}²) = √{len_sq} = {fmt_num(len_n)}",
            "",
            "🎯 ИТОГОВОЕ РАССТОЯНИЕ d:",
            "   ╔════════════════════════════════════════════════════════╗",
            f"   ║   d = |{val}| / {fmt_num(len_n)} = {fmt_num(dist):<30} ║",
            "   ╚════════════════════════════════════════════════════════╝",
            "",
            "📍 ЭТАП 2. ОРТОГОНАЛЬНАЯ ПРОЕКЦИЯ ТОЧКИ M₀ НА ПЛОСКОСТЬ (ТОЧКА H)",
            f"   Смещение по нормали t_H = -Δ / |n⃗|² = {fmt_num(t_proj)}",
            f"   H = M₀ + t_H · n⃗  ⟹  {h_str}",
            "",
            "🔄 ЭТАП 3. СИММЕТРИЧНАЯ ТОЧКА M' ОТНОСИТЕЛЬНО ПЛОСКОСТИ",
            f"   M' = 2·H - M₀  ⟹  {sym_str}"
        ]

        return {
            'distance': dist,
            'projection': (Hx, Hy, Hz),
            'symmetric': (Sx, Sy, Sz),
            'steps': "\n".join(steps)
        }

    @staticmethod
    def point_to_line(pt, line_m, line_s) -> Dict[str, Any]:
        """Расстояние от точки до прямой, проекция H и симметричная точка."""
        x0, y0, z0 = [parse_number(c_) for c_ in pt]
        x1, y1, z1 = [parse_number(c_) for c_ in line_m]
        m, p, q = [parse_number(c_) for c_ in line_s]

        w1, w2, w3 = x0 - x1, y0 - y1, z0 - z1
        cx = w2 * q - w3 * p
        cy = w3 * m - w1 * q
        cz = w1 * p - w2 * m

        len_cross_sq = cx**2 + cy**2 + cz**2
        len_cross = sp.sqrt(len_cross_sq)
        len_s_sq = m**2 + p**2 + q**2
        len_s = sp.sqrt(len_s_sq)

        dist = len_cross / len_s

        dot_ws = w1 * m + w2 * p + w3 * q
        t_proj = dot_ws / len_s_sq

        Hx = x1 + t_proj * m
        Hy = y1 + t_proj * p
        Hz = z1 + t_proj * q

        Sx = 2 * Hx - x0
        Sy = 2 * Hy - y0
        Sz = 2 * Hz - z0

        h_str = f"H({fmt_num(Hx)}; {fmt_num(Hy)}; {fmt_num(Hz)})"
        sym_str = f"M'({fmt_num(Sx)}; {fmt_num(Sy)}; {fmt_num(Sz)})"

        steps = [
            "📌 ЭТАП 1. ТЕОРЕТИЧЕСКАЯ ФОРМУЛА РАССТОЯНИЯ",
            "   ┌────────────────────────────────────────────────────────┐",
            "   │   d = |M₁M₀⃗ × s⃗| / |s⃗|                                │",
            "   └────────────────────────────────────────────────────────┘",
            f"   ▸ Вектор w⃗ = M₁M₀⃗ = ({w1}; {w2}; {w3})",
            f"   ▸ Векторное произведение w⃗ × s⃗ = ({cx}; {cy}; {cz})",
            f"   ▸ |w⃗ × s⃗| = √{len_cross_sq} = {fmt_num(len_cross)}",
            f"   ▸ |s⃗| = √{len_s_sq} = {fmt_num(len_s)}",
            "",
            "🎯 ИТОГОВОЕ РАССТОЯНИЕ d:",
            "   ╔════════════════════════════════════════════════════════╗",
            f"   ║   d = {fmt_num(len_cross)} / {fmt_num(len_s)} = {fmt_num(dist):<30} ║",
            "   ╚════════════════════════════════════════════════════════╝",
            "",
            "📍 ЭТАП 2. ОРТОГОНАЛЬНАЯ ПРОЕКЦИЯ ТОЧКИ НА ПРЯМУЮ (ТОЧКА H)",
            f"   t_H = (w⃗ · s⃗) / |s⃗|² = {fmt_num(t_proj)}",
            f"   H = M₁ + t_H · s⃗  ⟹  {h_str}",
            "",
            "🔄 ЭТАП 3. СИММЕТРИЧНАЯ ТОЧКА M' ОТНОСИТЕЛЬНО ПРЯМОЙ",
            f"   M' = 2·H - M₀  ⟹  {sym_str}"
        ]

        return {
            'distance': dist,
            'projection': (Hx, Hy, Hz),
            'symmetric': (Sx, Sy, Sz),
            'steps': "\n".join(steps)
        }


class PlanePencilSolver:
    """Пучок плоскостей: α(P1) + β(P2) = 0"""

    @staticmethod
    def pencil_through_point(pl1, pl2, pt) -> Dict[str, Any]:
        """Плоскость из пучка, проходящая через точку M0."""
        A1, B1, C1, D1 = [parse_number(c_) for c_ in pl1]
        A2, B2, C2, D2 = [parse_number(c_) for c_ in pl2]
        x0, y0, z0 = [parse_number(c_) for c_ in pt]

        v1 = A1 * x0 + B1 * y0 + C1 * z0 + D1
        v2 = A2 * x0 + B2 * y0 + C2 * z0 + D2

        if v1 == 0 and v2 == 0:
            raise ValueError("Точка лежит на самой оси пучка (прямой пересечения)! Через неё проходит весь пучок.")

        A = v2 * A1 - v1 * A2
        B = v2 * B1 - v1 * B2
        C = v2 * C1 - v1 * C2
        D = v2 * D1 - v1 * D2

        As, Bs, Cs, Ds, eq_str = simplify_plane_eq(A, B, C, D)

        steps = [
            "📌 ЭТАП 1. УРАВНЕНИЕ ПУЧКА ПЛОСКОСТЕЙ",
            "   ┌────────────────────────────────────────────────────────┐",
            "   │   α·(A₁x + B₁y + C₁z + D₁) + β·(A₂x + B₂y + C₂z + D₂) = 0 │",
            "   └────────────────────────────────────────────────────────┘",
            "",
            "📝 ЭТАП 2. ПОДСТАНОВКА ТОЧКИ M₀",
            f"   ▸ P₁(M₀) = {A1}·({x0}) + {B1}·({y0}) + {C1}·({z0}) + {D1} = {v1}",
            f"   ▸ P₂(M₀) = {A2}·({x0}) + {B2}·({y0}) + {C2}·({z0}) + {D2} = {v2}",
            f"   α·({v1}) + β·({v2}) = 0  ⟹  выбираем α = {v2}, β = -({v1})",
            "",
            "⚙️ ЭТАП 3. РАСКРЫТИЕ СКОБОК И ПРИВЕДЕНИЕ ПОДОБНЫХ",
            f"   ({v2})·({A1}x + {B1}y + {C1}z + {D1}) - ({v1})·({A2}x + {B2}y + {C2}z + {D2}) = 0",
            "",
            "🎯 ИТОГОВЫЙ ОТВЕТ: УРАВНЕНИЕ ПЛОСКОСТИ ИЗ ПУЧКА",
            "   ╔════════════════════════════════════════════════════════╗",
            f"   ║   {eq_str:<50}   ║",
            "   ╚════════════════════════════════════════════════════════╝"
        ]

        return {
            'A': As, 'B': Bs, 'C': Cs, 'D': Ds,
            'equation_str': eq_str,
            'steps': "\n".join(steps)
        }
