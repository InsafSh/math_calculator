"""
Разбор математических формул, введённых пользователем.

Поддерживается привычная запись: 2x, x^2, sin x, ln(x), lg(x), √x, e^x, arctg x.
Разрешены только перечисленные функции и константы и заданные переменные — произвольный код
выполнить нельзя. Неизвестные имена дают понятную ошибку.
"""

import re
from typing import Callable, Dict, Iterable, Sequence

import numpy as np
import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor, implicit_multiplication_application, parse_expr, standard_transformations,
)

_TRANSFORMS = standard_transformations + (implicit_multiplication_application, convert_xor)

FUNCTIONS: Dict[str, object] = {
    'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan, 'tg': sp.tan, 'cot': sp.cot, 'ctg': sp.cot,
    'sec': sp.sec, 'csc': sp.csc,
    'asin': sp.asin, 'acos': sp.acos, 'atan': sp.atan, 'acot': sp.acot,
    'arcsin': sp.asin, 'arccos': sp.acos, 'arctan': sp.atan, 'arctg': sp.atan, 'arcctg': sp.acot,
    'sinh': sp.sinh, 'cosh': sp.cosh, 'tanh': sp.tanh, 'sh': sp.sinh, 'ch': sp.cosh, 'th': sp.tanh,
    'asinh': sp.asinh, 'acosh': sp.acosh, 'atanh': sp.atanh,
    'exp': sp.exp, 'log': sp.log, 'ln': sp.log, 'lg': lambda a: sp.log(a, 10), 'log10': lambda a: sp.log(a, 10),
    'log2': lambda a: sp.log(a, 2),
    'sqrt': sp.sqrt, 'cbrt': lambda a: sp.real_root(a, 3), 'root': sp.real_root,
    'abs': sp.Abs, 'Abs': sp.Abs, 'sign': sp.sign, 'floor': sp.floor, 'ceil': sp.ceiling,
    'gamma': sp.gamma, 'erf': sp.erf, 'factorial': sp.factorial, 'Heaviside': sp.Heaviside,
    'min': sp.Min, 'max': sp.Max,
}
CONSTANTS: Dict[str, object] = {'pi': sp.pi, 'e': sp.E, 'E': sp.E, 'oo': sp.oo, 'inf': sp.oo}

_GLOBALS = {
    'Integer': sp.Integer, 'Float': sp.Float, 'Rational': sp.Rational, 'Symbol': sp.Symbol,
    'Function': sp.Function, '__builtins__': {},
}


def _clean(text: str) -> str:
    s = str(text).strip()
    # «y = …», «f(x) = …», «z(x, y) = …» — оставляем правую часть
    s = re.sub(r'^\s*[A-Za-z]\w*\s*(\([^()]*\))?\s*=(?!=)', '', s)
    s = s.replace('−', '-').replace('·', '*').replace('×', '*').replace('÷', '/').replace('²', '^2').replace('³', '^3')
    s = re.sub(r'√\s*(\d+(?:\.\d+)?|[A-Za-z]\w*)', r'sqrt(\1)', s).replace('√', 'sqrt')
    s = s.replace('∞', 'oo')
    return s


def parse_expression(text: str, variables: Sequence[str] = ('x',), extra: Iterable[str] = ()) -> sp.Expr:
    """
    Разбор формулы. variables — имена переменных (вещественные символы), extra — дополнительные
    разрешённые имена (например, параметры модели). Возвращает выражение SymPy.
    """
    raw = str(text).strip()
    if not raw:
        raise ValueError("Пустая формула")
    s = _clean(raw)
    if '__' in s or re.search(r'[;\\`$@!?{}\[\]]', s):
        raise ValueError(f"Недопустимые символы в формуле «{raw}»")
    names = list(variables) + list(extra)
    local = {n: sp.Symbol(n, real=True) for n in names}
    local.update(CONSTANTS)
    local.update(FUNCTIONS)
    # имена переменных важнее одноимённых констант (например, переменная e)
    for n in names:
        local[n] = sp.Symbol(n, real=True)
    try:
        expr = parse_expr(s, local_dict=local, global_dict=dict(_GLOBALS), transformations=_TRANSFORMS, evaluate=True)
    except Exception:
        expr = None
    if not isinstance(expr, sp.Expr):
        hint = " В формулах десятичный разделитель — точка: 2.5, а не 2,5." if re.search(r'\d,\d', s) else ""
        raise ValueError(f"Не удалось разобрать формулу «{raw}». Пример записи: x^2*sin(x) + exp(-x)/2.{hint}")
    unknown = sorted(str(sym) for sym in expr.free_symbols if str(sym) not in names)
    if unknown:
        allowed = ", ".join(names) if names else "нет"
        raise ValueError(f"Неизвестные имена в формуле: {', '.join(unknown)}. Допустимые переменные: {allowed}")
    return expr


def symbols(names: Sequence[str]):
    return [sp.Symbol(n, real=True) for n in names]


def to_numpy(expr: sp.Expr, variables: Sequence[str]) -> Callable:
    """Быстрая числовая функция от массивов NumPy; константа возвращается массивом нужной формы."""
    syms = symbols(variables)
    extra = {
        'Heaviside': lambda a, h=0.5: np.heaviside(a, h),
        # производные |x|, sign x: дельта-функция численно равна 0 вне особой точки
        'DiracDelta': lambda a, *k: np.zeros_like(np.asarray(a, dtype=float)),
    }
    # scipy — для спецфункций (erf, gamma, …), которые сам numpy не векторизует
    f = sp.lambdify(syms, expr, modules=[extra, 'scipy', 'numpy'])

    def wrapped(*args):
        with np.errstate(all='ignore'):
            out = f(*args)
        out = np.asarray(out, dtype=complex if np.iscomplexobj(out) else float)
        if np.iscomplexobj(out):
            out = np.where(np.abs(out.imag) < 1e-12, out.real, np.nan)
        if args and out.shape != np.shape(args[0]):
            out = np.broadcast_to(out, np.broadcast(*args).shape).astype(float)
        return out

    return wrapped


def parse_bound(text: str) -> sp.Expr:
    """Предел интегрирования / точка: число, выражение с pi, или ±∞ (oo, inf, ∞)."""
    raw = str(text).strip().replace(',', '.')
    if raw in ('+oo', '+inf', '+∞'):
        raw = 'oo'
    expr = parse_expression(raw, variables=())
    if not (expr.is_number or expr in (sp.oo, -sp.oo)):
        raise ValueError(f"«{text}» — не число")
    return expr
