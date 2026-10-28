"""
Раздел «Обработка эксперимента»: регистрация задач и примеры.
"""

from ..core.common import parse_number
from ..core.experiment import (
    MODELS, direct_measurements, indirect_measurement, least_squares_fit, tabular_function,
)
from ..core.result import Result
from .registry import Preset, Task, choice, formula, num, register, text

SECTION = "Обработка эксперимента"
P_CHOICES = ("0.95", "0.99", "0.90", "0.68")


def _add(task_id, group, title, fields, solve, description="", presets=None):
    register(Task(id=f"experiment.{task_id}", section=SECTION, group=group, title=title, fields=fields,
                  solve=solve, description=description, presets=[Preset(n, v) for n, v in (presets or [])]))


def _float(text, name):
    try:
        return float(parse_number(text))
    except ValueError as ex:
        raise ValueError(f"{name}: {ex}") from None


# --------------------------------------------------------------------- прямые измерения
OUTLIER_MODES = {"Проверить и исключить": "exclude", "Только проверить": "check", "Не проверять": "none"}


def _direct(v):
    theta = _float(v['theta'] or "0", "Погрешность прибора")
    res = direct_measurements(v['data'], float(v['P']), theta, v['unit'].strip(), v['name'].strip() or "x",
                              OUTLIER_MODES[v['outliers']])
    return Result(res['steps'], res['result'], res, scene2d=res['plot2d'])


_add("direct", "Измерения и погрешности", "Прямые многократные измерения",
     [text('data', "Результаты измерений", "10.1 10.3 10.2 10.4 10.2 10.3 10.1 12.9 10.2 10.3", rows=5),
      formula('name', "Обозначение величины", "L"),
      formula('unit', "Единицы измерения", "мм"),
      num('theta', "Погрешность прибора θ", "0.05", hint="Предел допускаемой погрешности; 0 — не учитывать"),
      choice('P', "Доверительная вероятность P", P_CHOICES),
      choice('outliers', "Грубые погрешности (критерий Граббса)", tuple(OUTLIER_MODES))],
     _direct, "Среднее, СКО, промахи по Граббсу, коэффициент Стьюдента, учёт погрешности прибора по ГОСТ Р 8.736-2011, "
              "округление результата.",
     [("Длина с промахом (штангенциркуль)", {'data': "10.1 10.3 10.2 10.4 10.2 10.3 10.1 12.9 10.2 10.3",
                                            'name': "L", 'unit': "мм", 'theta': "0.05", 'P': "0.95"}),
      ("Период колебаний (секундомер)", {'data': "2.01\n1.98\n2.03\n2.00\n1.99\n2.02\n2.01", 'name': "T", 'unit': "с",
                                         'theta': "0.01", 'P': "0.95"}),
      ("Напряжение (вольтметр класса 0,5 на 10 В)", {'data': "4.96; 4.98; 4.97; 4.99; 4.97", 'name': "U", 'unit': "В",
                                                    'theta': "0.05", 'P': "0.95"})])


# --------------------------------------------------------------------- косвенные измерения
def _indirect(v):
    res = indirect_measurement(v['formula'], v['values'], v['unit'].strip(), float(v['P']))
    return Result(res['steps'], res['result'], res, scene2d=res['plot2d'])


_add("indirect", "Измерения и погрешности", "Косвенные измерения: погрешность функции",
     [formula('formula', "Расчётная формула", "g = 4*pi^2*L/T^2",
              hint="Слева — обозначение результата (необязательно)"),
      text('values', "Измеренные величины", "L = 1.000 ± 0.002\nT = 2.006 ± 0.005", rows=5, file_import=False,
           hint="По строке на величину: имя = значение ± погрешность (можно в %: R = 100 ± 1%)"),
      formula('unit', "Единицы результата", "м/с²"),
      choice('P', "Доверительная вероятность (для записи результата)", P_CHOICES)],
     _indirect, "Частные производные вычисляются символьно; погрешности складываются квадратично; показан вклад "
                "каждой величины — какую измерять точнее.",
     [("Ускорение свободного падения (маятник)", {'formula': "g = 4*pi^2*L/T^2",
                                                  'values': "L = 1.000 ± 0.002\nT = 2.006 ± 0.005", 'unit': "м/с²"}),
      ("Плотность цилиндра", {'formula': "rho = 4*m/(pi*d^2*h)",
                              'values': "m = 125.4 ± 0.1\nd = 2.01 ± 0.01\nh = 5.02 ± 0.02", 'unit': "г/см³"}),
      ("Сопротивление по закону Ома", {'formula': "R = U/I", 'values': "U = 4.97 ± 0.05\nI = 0.152 ± 1.5%",
                                       'unit': "Ом"}),
      ("Жёсткость пружины по периоду", {'formula': "k = 4*pi^2*m/T^2",
                                        'values': "m = 0.200 ± 0.001\nT = 0.62 ± 0.01", 'unit': "Н/м"})])


# --------------------------------------------------------------------- аппроксимация
def _fit(v):
    res = least_squares_fit(v['data'], v['model'], v['custom'], v['guess'], float(v['P']))
    return Result(res['steps'], f"y = {res['equation']},  R² = {res['r2']:.5g}", res, scene2d=res['plot2d'])


OHM = "I, А\tU, В\n0.10\t0.52\n0.20\t1.01\n0.30\t1.49\n0.40\t2.05\n0.50\t2.48\n0.60\t3.03\n0.70\t3.49"
DISCHARGE = ("t, с\tU, В\tσU\n0\t9.95\t0.05\n2\t7.42\t0.05\n4\t5.51\t0.05\n6\t4.08\t0.05\n8\t3.04\t0.05\n"
             "10\t2.27\t0.05\n12\t1.68\t0.05\n14\t1.25\t0.05")
OSC = ("t\tx\n0\t1.00\n0.25\t0.62\n0.5\t-0.08\n0.75\t-0.65\n1\t-0.78\n1.25\t-0.42\n1.5\t0.12\n1.75\t0.52\n2\t0.58\n"
       "2.25\t0.26\n2.5\t-0.15\n2.75\t-0.42\n3\t-0.40\n3.25\t-0.13\n3.5\t0.17\n3.75\t0.31")

_add("fit", "Аппроксимация и табличные данные", "Аппроксимация методом наименьших квадратов",
     [text('data', "Данные: x, y [, σy]", OHM, rows=8,
           hint="Столбцы через табуляцию, пробел или «;». Третий столбец (необязательно) — погрешности y"),
      choice('model', "Модель", tuple(MODELS)),
      formula('custom', "Своя формула (для модели «Своя формула»)", "a*exp(-k*x)*cos(w*x + phi)",
              hint="Переменная x; параметры: a, b, c, d, k, m, A, B, C, D, x0, w, tau, phi"),
      formula('guess', "Начальные приближения (для нелинейных моделей)", "a = 1; k = 0.5; w = 2.5; phi = 0"),
      choice('P', "Доверительная вероятность P", P_CHOICES)],
     _fit, "Параметры с доверительными интервалами, R², χ²/ν при заданных σy, таблица остатков, "
           "доверительная полоса кривой.",
     [("Закон Ома U(I) — прямая", {'data': OHM, 'model': "Линейная  y = a + b·x"}),
      ("Разряд конденсатора — экспонента с погрешностями", {'data': DISCHARGE, 'model': "Экспонента  y = a·exp(b·x)"}),
      ("Затухающие колебания — своя формула", {'data': OSC, 'model': "Своя формула",
                                               'custom': "a*exp(-k*x)*cos(w*x + phi)",
                                               'guess': "a = 1; k = 0.5; w = 2.5; phi = 0"}),
      ("Полином 2-й степени", {'data': "x y\n-2 9.1\n-1 3.9\n0 1.1\n1 0.2\n2 1.9\n3 6.2\n4 12.8",
                               'model': "Квадратичная  y = a + b·x + c·x²"})])


# --------------------------------------------------------------------- табличная функция
def _tabular(v):
    res = tabular_function(v['data'], v['points'], v['method'])
    integral = res['simpson'] if res['simpson'] == res['simpson'] else res['trapezoid']  # NaN при n < 3
    return Result(res['steps'], f"Интеграл ≈ {integral:.6g}", res, scene2d=res['plot2d'])


SPEED = "t, с\tv, м/с\n0\t0\n1\t2.9\n2\t5.6\n3\t7.8\n4\t9.5\n5\t10.6\n6\t11.2\n7\t11.5\n8\t11.6"

_add("tabular", "Аппроксимация и табличные данные", "Табличная функция: интерполяция, производная, интеграл",
     [text('data', "Данные: x, y", SPEED, rows=8),
      formula('points', "Точки интерполяции x (через пробел)", "2.5 6.3"),
      choice('method', "Интерполяция", ("Кубический сплайн", "Линейная"))],
     _tabular, "Значения между узлами, численная производная (центральные разности), интеграл методами трапеций и Симпсона.",
     [("Скорость → путь и ускорение", {'data': SPEED, 'points': "2.5 6.3"}),
      ("Мощность во времени → энергия", {'data': "t, ч\tP, кВт\n0\t1.2\n2\t1.5\n4\t2.8\n6\t3.1\n8\t2.4\n10\t1.9\n12\t1.3",
                                         'points': "5 9"})])
