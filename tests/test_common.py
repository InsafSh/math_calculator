import pytest
import sympy as sp

from mathcalc.core.common import parse_number, simplify_plane_eq, fmt_num


@pytest.mark.parametrize("text, expected", [
    ("2", 2), ("-1/3", sp.Rational(-1, 3)), ("2,5", sp.Rational(5, 2)), ("0.1", sp.Rational(1, 10)),
    ("√3", sp.sqrt(3)), ("√(2)+1", 1 + sp.sqrt(2)), ("2^3", 8), ("−4", -4), ("pi/4", sp.pi / 4),
])
def test_parse_number_accepts(text, expected):
    assert sp.simplify(parse_number(text) - expected) == 0


@pytest.mark.parametrize("text", ["", "abc", "abc+", "x+1", "sqrt(-1)", "1/"])
def test_parse_number_rejects_with_readable_error(text):
    with pytest.raises(ValueError) as err:
        parse_number(text)
    assert "Sympify" not in str(err.value)


def test_simplify_plane_eq_normalizes_sign_and_gcd():
    A, B, C, D, eq = simplify_plane_eq(-4, 2, -6, 8)
    assert (A, B, C, D) == (2, -1, 3, -4)
    assert eq == "2x - y + 3z - 4 = 0"


def test_fmt_num_shows_exact_and_decimal():
    assert fmt_num(sp.Rational(1, 3)).startswith("1/3")
    assert "≈" in fmt_num(sp.sqrt(2))
    assert fmt_num(5) == "5"
