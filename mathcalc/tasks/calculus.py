"""
Раздел «Математический анализ»: регистрация задач и примеры.
"""

from ..core.calculus import (
    definite_integral, derivative, extrema_multivar, indefinite_integral, limit, multiple_integral,
    partial_derivatives, series_sum, taylor,
)
from ..core.result import Result
from .registry import Preset, Task, choice, formula, register, text

SECTION = "Математический анализ"


def _add(task_id, group, title, fields, solve, description="", presets=None):
    register(Task(id=f"calculus.{task_id}", section=SECTION, group=group, title=title, fields=fields,
                  solve=solve, description=description, presets=[Preset(n, v) for n, v in (presets or [])]))


G_LIM, G_DIFF, G_INT, G_SER = "Пределы", "Производные", "Интегралы", "Ряды"


def _limit(v):
    res = limit(v['f'], v['a'], v['dir'])
    summary = f"lim = {res['result']}" if res['result'] is not None else "Предел не существует (односторонние пределы различны)"
    return Result(res['steps'], summary, res, scene2d=res['plot2d'])


_add("limit", G_LIM, "Предел функции",
     [formula('f', "f(x)", "sin(x)/x"),
      formula('a', "x стремится к", "0", hint="Число, выражение (pi/2) или oo / -oo для ±∞"),
      choice('dir', "Направление", ("двусторонний", "справа (x → a+0)", "слева (x → a−0)"))],
     _limit, "Подстановка, тип неопределённости, правило Лопиталя по шагам, односторонние пределы, численная проверка.",
     [("Первый замечательный", {'f': "sin(x)/x", 'a': "0"}),
      ("Второй замечательный", {'f': "(1 + 1/x)^x", 'a': "oo"}),
      ("0/0, Лопиталь дважды", {'f': "(exp(x) - 1 - x)/x^2", 'a': "0"}),
      ("Разные односторонние пределы", {'f': "1/(x - 1)", 'a': "1"}),
      ("∞/∞", {'f': "(3x^2 + 2x)/(5x^2 - 1)", 'a': "oo"}),
      ("Предела нет (колебания)", {'f': "sin(1/x)", 'a': "0"})])


def _deriv(v):
    res = derivative(v['f'], int(v['n']), v['x0'])
    return Result(res['steps'], f"y′ = {res['derivatives'][1]}", res, scene2d=res['plot2d'])


_add("derivative", G_DIFF, "Производная, касательная и нормаль",
     [formula('f', "f(x)", "x^2*sin(x)"), choice('n', "Порядок производной", tuple(str(i) for i in range(1, 7))),
      formula('x0', "Точка x₀ (необязательно)", "pi/2", hint="Значения производных, касательная и нормаль в точке")],
     _deriv, "Производные до 6-го порядка с упрощением, значения в точке, уравнения касательной и нормали, графики f и f′.",
     [("Произведение", {'f': "x^2*sin(x)", 'n': "2", 'x0': "pi/2"}),
      ("Сложная функция", {'f': "ln(1 + x^2)", 'n': "1", 'x0': "1"}),
      ("Частное", {'f': "(x + 1)/(x^2 + 1)", 'n': "1", 'x0': "0"})])


def _partials(v):
    res = partial_derivatives(v['f'], v['vars'], v['point'])
    return Result(res['steps'], "Частные производные вычислены", res)


_add("partials", G_DIFF, "Частные производные, градиент, гессиан, якобиан",
     [formula('f', "Функция (несколько через «;» — якобиан)", "x^2*y + exp(x*y)"),
      formula('vars', "Переменные", "x y"),
      formula('point', "Точка (необязательно)", "1 0", hint="Координаты через пробел")],
     _partials, "Для одной функции — градиент, матрица Гессе, лапласиан; для нескольких — матрица и определитель Якоби.",
     [("Градиент и гессиан", {'f': "x^2*y + exp(x*y)", 'vars': "x y", 'point': "1 0"}),
      ("Три переменные", {'f': "x*y*z + x^2 - ln(y)", 'vars': "x y z", 'point': "1 1 2"}),
      ("Якобиан полярной замены", {'f': "r*cos(t); r*sin(t)", 'vars': "r t", 'point': ""}),
      ("Якобиан сферической замены", {'f': "r*sin(t)*cos(p); r*sin(t)*sin(p); r*cos(t)", 'vars': "r t p", 'point': ""})])


def _extrema(v):
    res = extrema_multivar(v['f'], v['vars'])
    return Result(res['steps'], f"Стационарных точек: {len(res['points'])}", res,
                  scene2d=res['plot2d'], scene3d=res['scene3d'])


_add("extrema", G_DIFF, "Экстремумы функции нескольких переменных",
     [formula('f', "f", "x^3 + y^3 - 3*x*y"), formula('vars', "Переменные", "x y")],
     _extrema, "Стационарные точки (символьно или численно), матрица Гессе, критерий Сильвестра; для двух переменных — "
               "поверхность и линии уровня.",
     [("Декартов лист", {'f': "x^3 + y^3 - 3*x*y", 'vars': "x y"}),
      ("Седло и минимум", {'f': "x^4 + y^4 - 4*x*y + 1", 'vars': "x y"}),
      ("Три переменные", {'f': "x^2 + y^2 + z^2 - 2x + 4z", 'vars': "x y z"})])


def _indef(v):
    res = indefinite_integral(v['f'], v['var'])
    summary = f"∫ = {res['antiderivative']} + C" if res['antiderivative'] is not None else "Не берётся в элементарных функциях"
    return Result(res['steps'], summary, res, scene2d=res['plot2d'])


_add("indefinite", G_INT, "Неопределённый интеграл (с ходом решения)",
     [formula('f', "Подынтегральная функция", "x*exp(x)"), formula('var', "Переменная интегрирования", "x")],
     _indef, "Пошаговое решение: замена переменной, интегрирование по частям, табличные интегралы; проверка дифференцированием.",
     [("По частям", {'f': "x*exp(x)"}), ("Замена переменной", {'f': "2x/(x^2 + 1)"}),
      ("Циклическое по частям", {'f': "exp(x)*sin(x)"}), ("Простейшие дроби", {'f': "(x + 3)/(x^2 - 1)"}),
      ("Тригонометрия", {'f': "sin(x)^2*cos(x)"}), ("Неэлементарный", {'f': "exp(-x^2)"})])


def _definite(v):
    res = definite_integral(v['f'], v['a'], v['b'])
    summary = f"I = {res['exact']}" if res['exact'] is not None else f"I ≈ {res['numeric']:.10g}"
    return Result(res['steps'], summary, res, scene2d=res['plot2d'])


_add("definite", G_INT, "Определённый и несобственный интеграл",
     [formula('f', "f(x)", "x^2*exp(-x)"), formula('a', "Нижний предел", "0"),
      formula('b', "Верхний предел", "oo", hint="oo — бесконечность")],
     _definite, "Формула Ньютона — Лейбница (с предельным переходом для несобственных), численная проверка с оценкой "
                "погрешности, площадь под графиком.",
     [("Несобственный, сходится", {'f': "x^2*exp(-x)", 'a': "0", 'b': "oo"}),
      ("Интеграл Пуассона", {'f': "exp(-x^2)", 'a': "-oo", 'b': "oo"}),
      ("Обычный", {'f': "x*sin(x)", 'a': "0", 'b': "pi"}),
      ("Расходится", {'f': "1/x", 'a': "1", 'b': "oo"}),
      ("Только численно", {'f': "sin(x)/x", 'a': "0", 'b': "10"})])


def _multiple(v):
    res = multiple_integral(v['f'], v['limits'])
    summary = f"I = {res['exact']}" if res['exact'] is not None else f"I ≈ {res['numeric']:.10g}"
    return Result(res['steps'], summary, res, scene2d=res['plot2d'])


_add("multiple", G_INT, "Двойной и тройной интеграл",
     [formula('f', "Подынтегральная функция", "x*y"),
      text('limits', "Пределы — от внутренней переменной к внешней", "y: 0 .. x\nx: 0 .. 1", rows=3, file_import=False,
           hint="Формат: переменная: нижний .. верхний. Пределы могут зависеть от внешних переменных")],
     _multiple, "Повторное интегрирование с промежуточными результатами, численная проверка, область для двойного интеграла.",
     [("Треугольная область", {'f': "x*y", 'limits': "y: 0 .. x\nx: 0 .. 1"}),
      ("Между параболой и прямой", {'f': "x + y", 'limits': "y: x^2 .. x\nx: 0 .. 1"}),
      ("Объём тетраэдра", {'f': "1", 'limits': "z: 0 .. 1 - x - y\ny: 0 .. 1 - x\nx: 0 .. 1"}),
      ("Четверть круга (полярные: якобиан r)", {'f': "r", 'limits': "r: 0 .. 1\nt: 0 .. pi/2"})])


def _taylor(v):
    res = taylor(v['f'], v['x0'], int(v['n']))
    return Result(res['steps'], f"T(x) = {res['polynomial']}", res, scene2d=res['plot2d'])


_add("taylor", G_SER, "Ряд Тейлора",
     [formula('f', "f(x)", "sin(x)"), formula('x0', "Точка разложения x₀", "0"),
      choice('n', "Порядок", ("5", "1", "2", "3", "4", "6", "7", "8", "10", "12"))],
     _taylor, "Коэффициенты, многочлен Тейлора, графики приближений разных порядков.",
     [("sin x", {'f': "sin(x)", 'x0': "0", 'n': "7"}), ("e^x", {'f': "exp(x)", 'x0': "0", 'n': "5"}),
      ("ln x в точке 1", {'f': "ln(x)", 'x0': "1", 'n': "5"}), ("√(1 + x)", {'f': "sqrt(1 + x)", 'x0': "0", 'n': "4"})])


def _series(v):
    res = series_sum(v['a'], v['n0'])
    conv = {True: "сходится", False: "расходится", None: "не определено"}[res['convergent']]
    return Result(res['steps'], f"Ряд {conv}" + (f", S = {res['sum']}" if res['sum'] is not None else ""), res,
                  scene2d=res['plot2d'])


_add("series", G_SER, "Числовой ряд: сходимость и сумма",
     [formula('a', "Общий член aₙ (переменная n)", "1/n^2"), formula('n0', "Начальный номер", "1")],
     _series, "Необходимый признак, признаки Даламбера и Коши, абсолютная и условная сходимость, сумма ряда, частичные суммы.",
     [("Σ 1/n²", {'a': "1/n^2", 'n0': "1"}), ("Гармонический", {'a': "1/n", 'n0': "1"}),
      ("Знакочередующийся", {'a': "(-1)^(n+1)/n", 'n0': "1"}), ("Σ 2ⁿ/n!", {'a': "2^n/factorial(n)", 'n0': "0"}),
      ("Геометрический", {'a': "(2/3)^n", 'n0': "0"})])
