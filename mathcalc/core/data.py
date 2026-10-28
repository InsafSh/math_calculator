"""
Табличные данные: разбор вставленного текста (из Excel, CSV, блокнота), импорт файлов,
округление результата измерений, форматирование чисел.
"""

import csv
import io
import math
import os
import re
from typing import List, Optional, Sequence, Tuple

import numpy as np

_NUM_RE = re.compile(r'^[+-]?(\d+([.,]\d*)?|[.,]\d+)([eE][+-]?\d+)?$')


def _split_line(line: str) -> List[str]:
    """
    Разделение строки на ячейки. Правила:
      * табуляция или «;» — разделители, запятая — десятичный знак (русский Excel, CSV с «;»);
      * иначе пробелы — разделители, запятая — десятичный знак («1,5 2,7»);
      * строка без пробелов с запятыми и точками («1.5,2.7») — английский CSV.
    """
    line = line.strip()
    if '\t' in line or ';' in line:
        cells = re.split(r'[\t;]+', line)
    elif re.search(r'\s', line):
        cells = re.split(r'\s+', line)
    elif ',' in line and '.' in line:
        cells = line.split(',')
    elif line.count(',') > 1:
        cells = line.split(',')
    else:
        cells = [line]
    return [c.strip() for c in cells if c.strip() != '']


def _to_float(cell: str) -> float:
    c = cell.replace(',', '.').replace('−', '-')
    if not _NUM_RE.match(cell.replace('−', '-')):
        raise ValueError(cell)
    return float(c)


def parse_table(text: str, min_cols: int = 1) -> Tuple[np.ndarray, List[str]]:
    """
    Разбор таблицы из текста. Первая строка, содержащая не числа, считается заголовком.
    Возвращает (матрица n×k, заголовки).
    """
    rows, headers = [], []
    for ln, line in enumerate(str(text).splitlines(), 1):
        if not line.strip() or line.strip().startswith('#'):
            continue
        cells = _split_line(line)
        try:
            vals = [_to_float(c) for c in cells]
        except ValueError:
            if not rows and not headers:
                headers = cells
                continue
            raise ValueError(f"Строка {ln}: не удалось прочитать число в «{line.strip()}»") from None
        rows.append(vals)
    if not rows:
        raise ValueError("Нет данных: вставьте числа (по строкам или из Excel)")
    width = len(rows[0])
    for i, r in enumerate(rows):
        if len(r) != width:
            raise ValueError(f"Разное число столбцов: в первой строке данных {width}, в строке {i + 1} — {len(r)}")
    if width < min_cols:
        raise ValueError(f"Нужно столбцов: {min_cols}, найдено: {width}")
    return np.array(rows, dtype=float), headers


def parse_series(text: str) -> np.ndarray:
    """Ряд чисел: все числа из текста по порядку (в строку, столбец или таблицей)."""
    vals = []
    for line in str(text).splitlines():
        if not line.strip() or line.strip().startswith('#'):
            continue
        for cell in _split_line(line):
            try:
                vals.append(_to_float(cell))
            except ValueError:
                raise ValueError(f"Не удалось прочитать число «{cell}»") from None
    if not vals:
        raise ValueError("Нет данных: введите числа через пробел, с новой строки или вставьте столбец из Excel")
    return np.array(vals, dtype=float)


def load_table_file(path: str) -> str:
    """Чтение файла данных в текст с табуляцией: .csv, .tsv, .txt, .dat, .xlsx."""
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.xlsx', '.xlsm'):
        try:
            import openpyxl
        except ImportError:
            raise ValueError("Для чтения Excel установите пакет openpyxl: pip install openpyxl") from None
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.worksheets[0]
        lines = []
        for row in ws.iter_rows(values_only=True):
            cells = ["" if v is None else str(v) for v in row]
            while cells and cells[-1] == "":
                cells.pop()
            if cells:
                lines.append("\t".join(cells))
        wb.close()
        return "\n".join(lines)
    with open(path, 'rb') as fh:
        raw = fh.read()
    for enc in ('utf-8-sig', 'cp1251', 'latin-1'):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if ext == '.csv':
        # стандартный CSV с запятой-разделителем и точкой-десятичным знаком → в табуляцию
        sample = text[:2048]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
            reader = csv.reader(io.StringIO(text), dialect)
            return "\n".join("\t".join(r) for r in reader if r)
        except csv.Error:
            pass
    return text


# ----------------------------------------------------------------------------- числа и округление

def fmt_float(x: float, sig: int = 6) -> str:
    """Число с sig значащими цифрами без лишних нулей и без экспоненты для обычных величин."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    if isinstance(x, float) and math.isinf(x):
        return "∞" if x > 0 else "−∞"
    if x == 0:
        return "0"
    ax = abs(x)
    if 1e-4 <= ax < 1e7:
        decimals = max(0, sig - 1 - int(math.floor(math.log10(ax))))
        s = f"{x:.{decimals}f}"
        if '.' in s:
            s = s.rstrip('0').rstrip('.')
        return s
    mant, exp = f"{x:.{sig - 1}e}".split('e')
    if '.' in mant:
        mant = mant.rstrip('0').rstrip('.')
    return f"{mant}e{int(exp)}"


def round_measurement(value: float, error: float) -> Tuple[str, str, int]:
    """
    Округление результата по погрешности: погрешность — до двух значащих цифр, если первая
    значащая цифра 1 или 2, иначе до одной; результат — до того же разряда.
    Возвращает (значение, погрешность, число знаков после запятой; отрицательное — разряд десятков и выше).
    """
    if not error or error <= 0 or not math.isfinite(error):
        return fmt_float(value), fmt_float(error or 0.0), 6
    exp = int(math.floor(math.log10(error)))
    first_digit = int(error / 10 ** exp)
    nsig = 2 if first_digit <= 2 else 1
    decimals = -(exp - (nsig - 1))
    err_r = round(error, decimals)
    # после округления первая цифра могла стать 3 (например, 0.0296 → 0.030): правило не меняем
    if err_r >= 10 ** (exp + 1) and nsig == 1:
        decimals -= 1
        err_r = round(error, decimals)
    val_r = round(value, decimals)
    if decimals > 0:
        return f"{val_r:.{decimals}f}", f"{err_r:.{decimals}f}", decimals
    return f"{val_r:.0f}", f"{err_r:.0f}", decimals


def student_t(P: float, dof: int) -> float:
    """Коэффициент Стьюдента для двусторонней доверительной вероятности P и dof степеней свободы."""
    from scipy import stats
    if dof < 1:
        raise ValueError("Нужно хотя бы 2 измерения")
    return float(stats.t.ppf((1 + P) / 2, dof))


def table_lines(headers: Sequence[str], rows: Sequence[Sequence[str]], max_rows: Optional[int] = None) -> List[str]:
    """Моноширинная таблица для вывода в шагах решения."""
    rows = [list(map(str, r)) for r in rows]
    shown = rows if max_rows is None or len(rows) <= max_rows else rows[:max_rows - 1] + [["…"] * len(headers)] + [rows[-1]]
    widths = [max(len(str(h)), *(len(r[i]) for r in shown)) for i, h in enumerate(headers)]
    line = "  ".join(str(h).rjust(w) for h, w in zip(headers, widths))
    out = [line, "  ".join("─" * w for w in widths)]
    for r in shown:
        out.append("  ".join(c.rjust(w) for c, w in zip(r, widths)))
    return out
