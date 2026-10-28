"""
Страница задачи. Форма ввода строится автоматически по описанию Task из реестра;
справа — вкладки «Решение», «Чертёж 2D», «3D».
"""

import threading
import time
from typing import Any, Dict

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFormLayout, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton,
    QScrollArea, QSplitter, QTabWidget, QVBoxLayout, QWidget,
)

from ..core.data import load_table_file
from ..tasks.registry import Task
from .plot_widgets import Plot2DWidget, Plot3DWidget
from .solution_view import SolutionView, steps_to_html


def _run_task(task: Task, values: Dict[str, Any]):
    """Решение задачи; ошибки ввода и математические исключения превращаются в текст для пользователя."""
    try:
        return task.run(values), ""
    except Exception as ex:
        return None, (str(ex) or ex.__class__.__name__)


class _Relay(QObject):
    """Передаёт результат из рабочего потока в поток интерфейса (сигнал ставится в очередь событий)."""
    done = Signal(int, object, str)


class TaskPage(QWidget):
    status = Signal(str, bool)  # текст, признак ошибки

    TAB_SOLUTION, TAB_2D, TAB_3D = 0, 1, 2

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self.editors: Dict[str, Any] = {}
        self.result = None
        self._request = 0
        self._started = 0.0
        self._relay = _Relay(self)
        self._relay.done.connect(self._on_done)
        self._busy_timer = QTimer(self)
        self._busy_timer.timeout.connect(self._tick)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)

        title = QLabel(task.title)
        title.setObjectName("taskTitle")
        root.addWidget(title)
        crumbs = QLabel(f"{task.section} › {task.group}" + (f"  —  {task.description}" if task.description else ""))
        crumbs.setObjectName("hint")
        crumbs.setWordWrap(True)
        root.addWidget(crumbs)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter, 1)
        splitter.addWidget(self._build_form())
        splitter.addWidget(self._build_results())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([400, 900])

        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self.solve)
        QShortcut(QKeySequence("Ctrl+Enter"), self, activated=self.solve)

    # ------------------------------------------------------------------ форма
    def _build_form(self) -> QWidget:
        holder = QWidget()
        lay = QVBoxLayout(holder)
        lay.setContentsMargins(0, 6, 6, 0)

        if self.task.presets:
            row = QHBoxLayout()
            row.addWidget(QLabel("Пример:"))
            self.preset_box = QComboBox()
            self.preset_box.addItem("— выберите —")
            for p in self.task.presets:
                self.preset_box.addItem(p.name)
            self.preset_box.activated.connect(self._on_preset)
            row.addWidget(self.preset_box, 1)
            lay.addLayout(row)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        for f in self.task.fields:
            if f.kind == "vector":
                box = QWidget()
                grid = QGridLayout(box)
                grid.setContentsMargins(0, 0, 0, 0)
                per_row = 3 if len(f.components) > 4 else len(f.components)
                edits = []
                for i, (comp, val) in enumerate(zip(f.components, f.default)):
                    r, c = divmod(i, per_row)
                    grid.addWidget(QLabel(f"{comp}:"), r, 2 * c)
                    e = QLineEdit(str(val))
                    e.setMinimumWidth(48)
                    e.returnPressed.connect(self.solve)
                    grid.addWidget(e, r, 2 * c + 1)
                    grid.setColumnStretch(2 * c + 1, 1)
                    edits.append(e)
                self.editors[f.key] = edits
                widget = box
            elif f.kind == "choice":
                cb = QComboBox()
                cb.addItems(list(f.choices))
                cb.setCurrentText(f.default)
                self.editors[f.key] = cb
                widget = cb
            elif f.kind == "text":
                widget = self._text_editor(f)
            else:
                e = QLineEdit(str(f.default))
                e.returnPressed.connect(self.solve)
                self.editors[f.key] = e
                widget = e
            label = QLabel(f.label)
            label.setObjectName("groupLabel")
            if f.hint:
                label.setToolTip(f.hint)
                wrap = QWidget()
                vl = QVBoxLayout(wrap)
                vl.setContentsMargins(0, 0, 0, 0)
                vl.addWidget(widget)
                hint = QLabel(f.hint)
                hint.setObjectName("hint")
                hint.setWordWrap(True)
                vl.addWidget(hint)
                widget = wrap
            if f.kind in ("text", "formula"):
                form.addRow(label)
                form.addRow(widget)
            else:
                form.addRow(label, widget)
        lay.addLayout(form)

        kinds = {f.kind for f in self.task.fields}
        notes = []
        if kinds & {"expr", "vector"}:
            notes.append("Числа: дроби 1/2, десятичные 2.5 или 2,5, корни sqrt(3) или √3, pi.")
        if "formula" in kinds:
            notes.append("Формулы: x^2, 2x, sin x, exp(x), ln x, lg x, sqrt(x), abs(x), pi, e; десятичная точка.")
        if any(f.kind == "text" and f.file_import for f in self.task.fields):
            notes.append("Данные: числа через пробел, «;» или с новой строки; можно вставить столбцы из Excel "
                         "или загрузить CSV/Excel кнопкой «Из файла…».")
        for n in notes:
            note = QLabel(n)
            note.setObjectName("hint")
            note.setWordWrap(True)
            lay.addWidget(note)

        self.btn_solve = QPushButton("Решить   (Ctrl+Enter)")
        self.btn_solve.setObjectName("primary")
        self.btn_solve.clicked.connect(lambda: self.solve())
        lay.addWidget(self.btn_solve)
        self.btn_cancel = QPushButton("Прервать")
        self.btn_cancel.clicked.connect(self.cancel)
        self.btn_cancel.setVisible(False)
        lay.addWidget(self.btn_cancel)

        self.error_label = QLabel("")
        self.error_label.setObjectName("error")
        self.error_label.setWordWrap(True)
        lay.addWidget(self.error_label)
        lay.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(holder)
        scroll.setMinimumWidth(340)
        return scroll

    def _text_editor(self, f) -> QWidget:
        box = QWidget()
        vl = QVBoxLayout(box)
        vl.setContentsMargins(0, 0, 0, 0)
        ed = QPlainTextEdit(str(f.default))
        mono = QFont("Consolas")
        mono.setStyleHint(QFont.Monospace)
        ed.setFont(mono)
        ed.setTabChangesFocus(False)
        ed.setFixedHeight(max(3, f.rows) * 20 + 12)
        self.editors[f.key] = ed
        vl.addWidget(ed)
        if f.file_import:
            row = QHBoxLayout()
            btn = QPushButton("Из файла…")
            btn.setToolTip("Загрузить данные из CSV, TXT или Excel (первый лист)")
            btn.clicked.connect(lambda _=False, e=ed: self._import_file(e))
            clear = QPushButton("Очистить")
            clear.clicked.connect(ed.clear)
            row.addWidget(btn)
            row.addWidget(clear)
            row.addStretch(1)
            vl.addLayout(row)
        return box

    def _import_file(self, editor):
        path, _ = QFileDialog.getOpenFileName(self, "Загрузить данные", "",
                                              "Данные (*.csv *.tsv *.txt *.dat *.xlsx *.xlsm);;Все файлы (*)")
        if not path:
            return
        try:
            editor.setPlainText(load_table_file(path))
            self.status.emit(f"Данные загружены: {path}", False)
        except Exception as ex:
            self.error_label.setText(f"Не удалось прочитать файл: {ex}")

    def values(self) -> Dict[str, Any]:
        out = {}
        for f in self.task.fields:
            ed = self.editors[f.key]
            if f.kind == "vector":
                out[f.key] = tuple(e.text().strip() for e in ed)
            elif f.kind == "choice":
                out[f.key] = ed.currentText()
            elif f.kind == "text":
                out[f.key] = ed.toPlainText()
            else:
                out[f.key] = ed.text().strip()
        return out

    def set_values(self, values: Dict[str, Any]):
        for f in self.task.fields:
            if f.key not in values:
                continue
            ed, val = self.editors[f.key], values[f.key]
            if f.kind == "vector":
                for e, v in zip(ed, val):
                    e.setText(str(v))
            elif f.kind == "choice":
                ed.setCurrentText(str(val))
            elif f.kind == "text":
                ed.setPlainText(str(val))
            else:
                ed.setText(str(val))

    def _on_preset(self, index: int, blocking: bool = False):
        if index <= 0:
            return
        self.set_values(self.task.presets[index - 1].values)
        self.solve(blocking)

    # ------------------------------------------------------------------ результаты
    def _build_results(self) -> QWidget:
        holder = QWidget()
        lay = QVBoxLayout(holder)
        lay.setContentsMargins(6, 6, 0, 0)

        bar = QHBoxLayout()
        self.summary = QLabel("")
        self.summary.setWordWrap(True)
        self.summary.setTextInteractionFlags(Qt.TextSelectableByMouse)
        bar.addWidget(self.summary, 1)
        self.btn_copy = QPushButton("Копировать решение")
        self.btn_copy.clicked.connect(self.copy_solution)
        self.btn_save = QPushButton("Сохранить…")
        self.btn_save.setToolTip("Сохранить решение в HTML или TXT")
        self.btn_save.clicked.connect(self.save_solution)
        for b in (self.btn_copy, self.btn_save):
            b.setEnabled(False)
            bar.addWidget(b)
        lay.addLayout(bar)

        self.tabs = QTabWidget()
        self.solution = SolutionView()
        self.plot2d = Plot2DWidget()
        self.plot3d = Plot3DWidget()
        self.tabs.addTab(self.solution, "Решение")
        self.tabs.addTab(self.plot2d, "Чертёж 2D")
        self.tabs.addTab(self.plot3d, "3D")
        self.tabs.setTabEnabled(self.TAB_2D, False)
        self.tabs.setTabEnabled(self.TAB_3D, False)
        lay.addWidget(self.tabs, 1)
        return holder

    # ------------------------------------------------------------------ решение в фоновом потоке
    def solve(self, blocking: bool = False):
        """
        Запуск решения. По умолчанию — в фоновом потоке, чтобы окно не «зависало» на долгих
        символьных вычислениях; blocking=True — синхронно (тесты, сценарии).
        """
        values = self.values()
        if blocking:
            self._request += 1
            self._finish(self._request, *_run_task(self.task, values))
            return
        self._request += 1
        req = self._request
        self._started = time.monotonic()
        self._set_busy(True)
        threading.Thread(target=lambda: self._relay.done.emit(req, *_run_task(self.task, values)), daemon=True).start()

    def cancel(self):
        """Прервать ожидание: результат текущего вычисления будет отброшен (поток завершится сам)."""
        self._request += 1
        self._set_busy(False)
        self.status.emit("Вычисление прервано", True)

    def _set_busy(self, busy: bool):
        self.btn_solve.setEnabled(not busy)
        self.btn_cancel.setVisible(busy)
        if busy:
            self.btn_solve.setText("Вычисляю…")
            self._busy_timer.start(250)
        else:
            self.btn_solve.setText("Решить   (Ctrl+Enter)")
            self._busy_timer.stop()

    def _tick(self):
        dt = time.monotonic() - self._started
        msg = f"Вычисляю… {dt:.0f} с"
        if dt > 5:
            msg += " — сложные символьные вычисления могут занимать время; можно прервать"
        self.status.emit(msg, False)

    def _on_done(self, req: int, res, err: str):
        if req != self._request:  # устаревший результат (пользователь прервал или запустил заново)
            return
        self._set_busy(False)
        self._finish(req, res, err)

    def _finish(self, req: int, res, err: str):
        if err:
            self.error_label.setText(f"Ошибка: {err}")
            self.status.emit(f"Ошибка: {err}", True)
            return
        self.error_label.setText("")
        self.result = res
        self.solution.set_steps(res.steps)
        self.summary.setText(res.summary)
        has2d, has3d = res.scene2d is not None, res.scene3d is not None and not res.scene3d.is_empty()
        self.tabs.setTabEnabled(self.TAB_2D, has2d)
        self.tabs.setTabEnabled(self.TAB_3D, has3d)
        self.plot2d.set_scene(res.scene2d if has2d else None)
        self.plot3d.set_scene(res.scene3d if has3d else None)
        if not self.tabs.isTabEnabled(self.tabs.currentIndex()):
            self.tabs.setCurrentIndex(self.TAB_SOLUTION)
        self.btn_copy.setEnabled(True)
        self.btn_save.setEnabled(True)
        extra = " Есть чертёж." if has2d else (" Есть 3D-сцена." if has3d else "")
        self.status.emit(f"Решено: {res.summary}.{extra}", False)

    def copy_solution(self):
        if self.solution.raw_text:
            QApplication.clipboard().setText(self.solution.raw_text)
            self.status.emit("Решение скопировано в буфер обмена", False)

    def save_solution(self):
        if not self.solution.raw_text:
            return
        path, flt = QFileDialog.getSaveFileName(self, "Сохранить решение", f"{self.task.title}.html",
                                                "HTML (*.html);;Текст (*.txt)")
        if not path:
            return
        content = self.solution.raw_text if path.lower().endswith(".txt") else steps_to_html(self.solution.raw_text, dark=False)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        self.status.emit(f"Решение сохранено: {path}", False)

    def apply_theme(self, dark: bool, plot_theme):
        self.solution.set_dark(dark)
        self.plot2d.set_theme(plot_theme)
        self.plot3d.set_theme(plot_theme)
