"""
Раздел «Функции и графики»: регистрация задач и примеры.
"""

from ..core.functions import (
    implicit_curve, investigate_function, parametric_curve, plot_functions, polar_curve, surface,
)
from ..core.result import Result
from .registry import Preset, Task, choice, formula, register

SECTION = "Функции и графики"


def _add(task_id, group, title, fields, solve, description="", presets=None):
    register(Task(id=f"functions.{task_id}", section=SECTION, group=group, title=title, fields=fields,
                  solve=solve, description=description, presets=[Preset(n, v) for n, v in (presets or [])]))


G2 = "Графики на плоскости"
G3 = "Функции двух переменных"


def _plot(v):
    res = plot_functions(v['f'], v['a'], v['b'])
    return Result(res['steps'], f"Построено графиков: {len(res['exprs'])}", res, scene2d=res['plot2d'])


_add("plot", G2, "Графики функций y = f(x)",
     [formula('f', "Функции (через «;» или с новой строки)", "sin(x); cos(x); x/3"),
      formula('a', "x от", "-2*pi"), formula('b', "x до", "2*pi")],
     _plot, "Несколько графиков на одних осях, таблица значений, точки пересечения графиков.",
     [("Тригонометрия", {'f': "sin(x); cos(x); x/3", 'a': "-2*pi", 'b': "2*pi"}),
      ("Рост функций", {'f': "ln(x); sqrt(x); x; x^2; exp(x)", 'a': "0.01", 'b': "4"}),
      ("Затухающие колебания", {'f': "exp(-0.3x)*cos(3x); exp(-0.3x); -exp(-0.3x)", 'a': "0", 'b': "12"})])


def _investigate(v):
    res = investigate_function(v['f'], v['a'], v['b'])
    return Result(res['steps'], f"Исследование y = {v['f']} выполнено", res, scene2d=res['plot2d'])


_add("investigate", G2, "Полное исследование функции",
     [formula('f', "Функция y = f(x)", "(x^2 - 1)/(x - 2)",
              hint="Кубический корень из отрицательных чисел — cbrt(x), а не x^(1/3)"),
      formula('a', "x от", "-6"), formula('b', "x до", "8")],
     _investigate, "Область определения, чётность, нули, асимптоты, монотонность и экстремумы, выпуклость и перегибы, "
                   "наибольшее и наименьшее значения на отрезке; точные значения, где возможно.",
     [("Дробно-рациональная с наклонной асимптотой", {'f': "(x^2 - 1)/(x - 2)", 'a': "-6", 'b': "8"}),
      ("Многочлен", {'f': "x^3 - 3x", 'a': "-2.5", 'b': "2.5"}),
      ("Функция Гаусса", {'f': "exp(-x^2)", 'a': "-3", 'b': "3"}),
      ("ln x / x", {'f': "ln(x)/x", 'a': "0.2", 'b': "12"}),
      ("Две вертикальные асимптоты", {'f': "x^3/(x^2 - 4)", 'a': "-6", 'b': "6"})])


def _parametric(v):
    res = parametric_curve(v['x'], v['y'], v['t0'], v['t1'])
    return Result(res['steps'], f"Длина дуги ≈ {res['length']:.6g}", res, scene2d=res['plot2d'])


_add("parametric", G2, "Параметрическая кривая x(t), y(t)",
     [formula('x', "x(t)", "2*cos(t) - cos(2t)"), formula('y', "y(t)", "2*sin(t) - sin(2t)"),
      formula('t0', "t от", "0"), formula('t1', "t до", "2*pi")],
     _parametric, "Кривая, производные, длина дуги и площадь.",
     [("Кардиоида", {'x': "2*cos(t) - cos(2t)", 'y': "2*sin(t) - sin(2t)", 't0': "0", 't1': "2*pi"}),
      ("Циклоида", {'x': "t - sin(t)", 'y': "1 - cos(t)", 't0': "0", 't1': "4*pi"}),
      ("Фигура Лиссажу 3:2", {'x': "sin(3t)", 'y': "sin(2t)", 't0': "0", 't1': "2*pi"})])


def _polar(v):
    res = polar_curve(v['r'], v['p0'], v['p1'])
    return Result(res['steps'], f"Площадь ≈ {res['area']:.6g}", res, scene2d=res['plot2d'])


_add("polar", G2, "Кривая в полярных координатах r(φ)",
     [formula('r', "r(φ), переменная phi", "1 + cos(phi)"), formula('p0', "φ от", "0"), formula('p1', "φ до", "2*pi")],
     _polar, "Кривая, длина и площадь сектора.",
     [("Кардиоида", {'r': "1 + cos(phi)", 'p0': "0", 'p1': "2*pi"}),
      ("Четырёхлепестковая роза", {'r': "cos(2phi)", 'p0': "0", 'p1': "2*pi"}),
      ("Спираль Архимеда", {'r': "phi/(2pi)", 'p0': "0", 'p1': "6*pi"})])


def _implicit(v):
    res = implicit_curve(v['eq'], v['x0'], v['x1'], v['y0'], v['y1'])
    return Result(res['steps'], "Кривая F(x, y) = 0 построена", res, scene2d=res['plot2d'])


_add("implicit", G2, "Неявная кривая F(x, y) = 0",
     [formula('eq', "Уравнение", "x^3 + y^3 = 3*x*y"), formula('x0', "x от", "-3"), formula('x1', "x до", "3"),
      formula('y0', "y от", "-3"), formula('y1', "y до", "3")],
     _implicit, "Кривая по уравнению без выражения y через x; производная неявной функции; особые точки.",
     [("Декартов лист", {'eq': "x^3 + y^3 = 3*x*y", 'x0': "-3", 'x1': "3", 'y0': "-3", 'y1': "3"}),
      ("Лемниската Бернулли", {'eq': "(x^2 + y^2)^2 = 2*(x^2 - y^2)", 'x0': "-2", 'x1': "2", 'y0': "-1.5", 'y1': "1.5"}),
      ("Эллипс", {'eq': "x^2/9 + y^2/4 = 1", 'x0': "-4", 'x1': "4", 'y0': "-3", 'y1': "3"})])


def _surface(v):
    res = surface(v['f'], v['x0'], v['x1'], v['y0'], v['y1'], int(v['levels']))
    return Result(res['steps'], "Поверхность и линии уровня построены", res, scene2d=res['plot2d'], scene3d=res['scene3d'])


_add("surface", G3, "Поверхность z = f(x, y) и линии уровня",
     [formula('f', "z = f(x, y)", "sin(x)*cos(y)"), formula('x0', "x от", "-pi"), formula('x1', "x до", "pi"),
      formula('y0', "y от", "-pi"), formula('y1', "y до", "pi"),
      choice('levels', "Число линий уровня", ("15", "10", "20", "30"))],
     _surface, "3D-поверхность (вращение мышью) и карта линий уровня; частные производные и градиент.",
     [("sin x · cos y", {'f': "sin(x)*cos(y)", 'x0': "-pi", 'x1': "pi", 'y0': "-pi", 'y1': "pi"}),
      ("Седло", {'f': "x^2 - y^2", 'x0': "-2", 'x1': "2", 'y0': "-2", 'y1': "2"}),
      ("Гауссов купол", {'f': "exp(-(x^2 + y^2))", 'x0': "-2.5", 'x1': "2.5", 'y0': "-2.5", 'y1': "2.5"}),
      ("Функция Розенброка", {'f': "(1 - x)^2 + 100*(y - x^2)^2", 'x0': "-2", 'x1': "2", 'y0': "-1", 'y1': "3"})])
