"""Эталонные ответы для разделов этапа 1: данные и формулы, эксперимент, функции, анализ."""

import math

import numpy as np
import pytest
import sympy as sp

from mathcalc.core.calculus import (
    definite_integral, derivative, extrema_multivar, indefinite_integral, limit, multiple_integral,
    partial_derivatives, series_sum, taylor,
)
from mathcalc.core.data import parse_series, parse_table, round_measurement
from mathcalc.core.experiment import (
    direct_measurements, grubbs_critical, indirect_measurement, least_squares_fit, parse_quantities, tabular_function,
)
from mathcalc.core.expr import parse_expression
from mathcalc.core.functions import investigate_function, numeric_roots, parametric_curve, polar_curve

x = sp.Symbol('x', real=True)


# ----------------------------------------------------------------------------- формулы и данные
@pytest.mark.parametrize("text, expected", [
    ("2x", 2 * x), ("x^2 sin x", x ** 2 * sp.sin(x)), ("y = e^x", sp.exp(x)), ("lg(100) + ln(e)", 3),
    ("√x", sp.sqrt(x)), ("arctg x", sp.atan(x)), ("f(x) = x³", x ** 3),
])
def test_parse_expression(text, expected):
    assert sp.simplify(parse_expression(text) - expected) == 0


@pytest.mark.parametrize("text", ["abc", "x;import os", "__import__('os')", "2,5x", ""])
def test_parse_expression_rejects(text):
    with pytest.raises(ValueError):
        parse_expression(text)


def test_parse_table_formats():
    t, h = parse_table("x\ty\n1,5\t2,5\n3\t4")          # вставка из русского Excel
    assert h == ["x", "y"] and t.tolist() == [[1.5, 2.5], [3, 4]]
    assert parse_table("1.5,2.5\n3,4.0")[0].tolist() == [[1.5, 2.5], [3, 4]]   # английский CSV
    assert parse_table("1;2\n3;4")[0].tolist() == [[1, 2], [3, 4]]
    assert parse_series("1.2 1.3\n1,4;1,5").tolist() == [1.2, 1.3, 1.4, 1.5]
    with pytest.raises(ValueError):
        parse_table("1 2\n3")


def test_load_table_files(tmp_path):
    from mathcalc.core.data import load_table_file
    ru = tmp_path / "ru.csv"
    ru.write_bytes("t;U\n0;9,95\n2;7,42\n".encode("cp1251"))
    assert parse_table(load_table_file(str(ru)))[0].tolist() == [[0, 9.95], [2, 7.42]]
    en = tmp_path / "en.csv"
    en.write_text("t,U\n0,9.95\n2,7.42\n", encoding="utf-8")
    assert parse_table(load_table_file(str(en)))[0].tolist() == [[0, 9.95], [2, 7.42]]
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in (("t", "U"), (0, 9.95), (2, 7.42)):
        ws.append(row)
    path = tmp_path / "data.xlsx"
    wb.save(path)
    table, headers = parse_table(load_table_file(str(path)))
    assert headers == ["t", "U"] and table.tolist() == [[0, 9.95], [2, 7.42]]


@pytest.mark.parametrize("value, err, expected", [
    (9.81234, 0.0234, ("9.812", "0.023")),   # первая цифра 2 — две значащие
    (9.81234, 0.0456, ("9.81", "0.05")),     # первая цифра 4 — одна значащая
    (0.0123456, 0.000149, ("0.01235", "0.00015")),
    (1234.5, 27, ("1234", "27")),
])
def test_round_measurement(value, err, expected):
    assert round_measurement(value, err)[:2] == expected


# ----------------------------------------------------------------------------- эксперимент
def test_grubbs_critical_matches_gost_table():
    # ГОСТ Р 8.736-2011, табл. А.1, уровень значимости 5 %
    for n, g in ((3, 1.153), (5, 1.672), (10, 2.176), (20, 2.557)):
        assert abs(grubbs_critical(n, 0.05) - g) < 2e-3


def test_direct_measurements_outlier_and_combination():
    r = direct_measurements("10.1 10.3 10.2 10.4 10.2 10.3 10.1 12.9 10.2 10.3", 0.95, 0.05, "мм", "L")
    assert r['excluded'] == [12.9] and r['n'] == 9
    assert abs(r['mean'] - 10.2333333) < 1e-6
    assert abs(r['t'] - 2.306) < 1e-3
    assert "K·S_Σ" in r['rule']
    assert r['value_str'] == "10.23" and r['error_str'] == "0.09"


def test_direct_measurements_only_random():
    r = direct_measurements("5 6 7", 0.95, 0.0)
    # x̄ = 6, S = 1, t(0.95; 2) = 4.303 → Δ = 4.303/√3
    assert abs(r['delta'] - 4.302653 / math.sqrt(3)) < 1e-5


def test_indirect_pendulum():
    r = indirect_measurement("g = 4*pi^2*L/T^2", "L = 1.000 ± 0.002\nT = 2.006 ± 0.005")
    g = 4 * math.pi ** 2 / 2.006 ** 2
    dg = g * math.sqrt((0.002 / 1.0) ** 2 + (2 * 0.005 / 2.006) ** 2)
    assert abs(r['value'] - g) < 1e-9 and abs(r['delta'] - dg) < 1e-9
    assert r['shares']['T'] > r['shares']['L']


def test_parse_quantities_percent():
    q = parse_quantities("R = 200 ± 1%\nU 5,0 0,1")
    assert q['R'] == (200.0, 2.0) and q['U'] == (5.0, 0.1)


def test_fit_linear_matches_polyfit_and_ci():
    xs = np.arange(1, 9.0)
    ys = 2.5 + 1.7 * xs + np.array([.1, -.2, .05, .15, -.1, 0, .12, -.08])
    r = least_squares_fit("\n".join(f"{a} {b}" for a, b in zip(xs, ys)), "Линейная  y = a + b·x")
    b, a = np.polyfit(xs, ys, 1)
    assert abs(r['params']['a'] - a) < 1e-10 and abs(r['params']['b'] - b) < 1e-10
    # стандартная ошибка наклона: sqrt(s² / Σ(x − x̄)²)
    resid = ys - (a + b * xs)
    se_b = math.sqrt((resid ** 2).sum() / (len(xs) - 2) / ((xs - xs.mean()) ** 2).sum())
    assert abs(r['se']['b'] - se_b) < 1e-12


def test_fit_nonlinear_custom():
    xs = np.linspace(0, 4, 15)
    ys = 3 * np.exp(-0.8 * xs) + 1
    r = least_squares_fit("\n".join(f"{a} {b}" for a, b in zip(xs, ys)), "Своя формула", "a*exp(-k*x) + c", "a = 2; k = 1; c = 0")
    assert abs(r['params']['a'] - 3) < 1e-6 and abs(r['params']['k'] - 0.8) < 1e-6 and abs(r['params']['c'] - 1) < 1e-6


def test_fit_weighted_chi2():
    xs = np.arange(1, 8.0)
    ys = 1 + 2 * xs
    r = least_squares_fit("\n".join(f"{a} {b} 0.1" for a, b in zip(xs, ys)), "Линейная  y = a + b·x")
    assert r['chi2'] is not None and r['chi2'] < 1e-12


def test_fit_rejects_too_few_points():
    with pytest.raises(ValueError):
        least_squares_fit("1 2\n2 3", "Квадратичная  y = a + b·x + c·x²")


def test_tabular_integral_and_derivative():
    xs = np.linspace(0, 2, 11)
    r = tabular_function("\n".join(f"{a} {a ** 2}" for a in xs), "0.5 1.5")
    assert abs(r['simpson'] - 8 / 3) < 1e-12
    assert np.allclose(r['derivative'], 2 * xs, atol=1e-9)


# ----------------------------------------------------------------------------- функции
def test_investigate_rational():
    info = investigate_function("(x^2 - 1)/(x - 2)", "-6", "8")['info']
    assert [str(z) for z in info['zeros']] == ['-1', '1']
    assert [str(v) for v in info['vertical']] == ['2']
    kinds = {str(c): k for c, _, k in info['extrema']}
    assert kinds == {'2 - sqrt(3)': 'максимум', 'sqrt(3) + 2': 'минимум'}


def test_investigate_gauss_inflections():
    info = investigate_function("exp(-x^2)", "-3", "3")['info']
    assert sorted(float(c) for c, _ in info['inflections']) == pytest.approx([-math.sqrt(0.5), math.sqrt(0.5)])


def test_numeric_roots_skip_poles():
    roots = numeric_roots(np.tan, -4, 4)
    assert roots == pytest.approx([-math.pi, 0, math.pi], abs=1e-9)


def test_curves_lengths_and_areas():
    assert parametric_curve("cos(t)", "sin(t)", "0", "2*pi")['area'] == pytest.approx(math.pi, rel=1e-6)
    assert parametric_curve("cos(t)", "sin(t)", "0", "2*pi")['length'] == pytest.approx(2 * math.pi, rel=1e-6)
    assert polar_curve("1 + cos(phi)", "0", "2pi")['area'] == pytest.approx(1.5 * math.pi, rel=1e-6)


# ----------------------------------------------------------------------------- анализ
@pytest.mark.parametrize("f, a, expected", [
    ("sin(x)/x", "0", 1), ("(1 + 1/x)^x", "oo", sp.E), ("(exp(x) - 1 - x)/x^2", "0", sp.Rational(1, 2)),
    ("(3x^2 + 2x)/(5x^2 - 1)", "oo", sp.Rational(3, 5)),
])
def test_limits(f, a, expected):
    assert limit(f, a)['result'] == expected


def test_limit_one_sided_differ():
    r = limit("1/(x - 1)", "1")
    assert r['result'] is None and r['one_sided'] == (-sp.oo, sp.oo)


def test_derivative_and_tangent():
    r = derivative("x^2", 1, "1")
    assert r['values'][1] == 2 and "y = 2x - 1" in r['steps']


def test_partials_and_jacobian():
    r = partial_derivatives("x^2*y + exp(x*y)", "x y", "1 0")
    assert r['values']['grad'] == [0, 2]
    r = partial_derivatives("r*cos(t); r*sin(t)", "r t")
    assert sp.simplify(r['values']['det'] - sp.Symbol('r', real=True)) == 0


def test_extrema_classification():
    pts = extrema_multivar("x^3 + y^3 - 3*x*y", "x y")['points']
    kinds = sorted(k for _, k, _ in pts)
    assert any("минимум" in k for k in kinds) and any("седлов" in k for k in kinds)


@pytest.mark.parametrize("f, expected", [
    ("x*exp(x)", (x - 1) * sp.exp(x)), ("1/(x^2 + 4)", sp.atan(x / 2) / 2), ("sin(x)^2", x / 2 - sp.sin(2 * x) / 4),
])
def test_indefinite(f, expected):
    F = indefinite_integral(f)['antiderivative']
    assert sp.simplify(sp.diff(F - expected, x)) == 0


def test_definite_and_improper():
    assert definite_integral("x^2", "0", "3")['exact'] == 9
    r = definite_integral("exp(-x^2)", "-oo", "oo")
    assert r['exact'] == sp.sqrt(sp.pi) and r['numeric'] == pytest.approx(math.sqrt(math.pi))
    assert definite_integral("1/x", "1", "oo")['exact'] == sp.oo


def test_multiple_integrals():
    assert multiple_integral("x*y", "y: 0 .. x\nx: 0 .. 1")['exact'] == sp.Rational(1, 8)
    assert multiple_integral("1", "z: 0 .. 1-x-y\ny: 0 .. 1-x\nx: 0 .. 1")['exact'] == sp.Rational(1, 6)


def test_taylor_exp():
    assert sp.expand(taylor("exp(x)", "0", 4)['polynomial'] - (1 + x + x ** 2 / 2 + x ** 3 / 6 + x ** 4 / 24)) == 0


@pytest.mark.parametrize("a, conv, s", [
    ("1/n^2", True, sp.pi ** 2 / 6), ("1/n", False, None), ("(-1)^(n+1)/n", True, sp.log(2)),
])
def test_series(a, conv, s):
    r = series_sum(a)
    assert r['convergent'] is conv
    if s is not None:
        assert sp.simplify(r['sum'] - s) == 0
