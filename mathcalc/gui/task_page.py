"""
Страница задачи. Форма ввода строится автоматически по описанию Task из реестра;
справа — вкладки «Решение», «Чертёж 2D», «3D».
"""

from typing import Any, Dict

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFormLayout, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QSplitter, QTabWidget, QVBoxLayout, QWidget,
)

from ..tasks.registry import Task
from .plot_widgets import Plot2DWidget, Plot3DWidget
from .solution_view import SolutionView, steps_to_html


class TaskPage(QWidget):
    status = Signal(str, bool)  # текст, признак ошибки

    TAB_SOLUTION, TAB_2D, TAB_3D = 0, 1, 2

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self.editors: Dict[str, Any] = {}
        self.result = None

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
                vl.addWidget(hint)
                widget = wrap
            form.addRow(label, widget)
        lay.addLayout(form)

        note = QLabel("Допустимы дроби (1/2), десятичные (2.5 или 2,5), корни sqrt(3) или √3, pi.")
        note.setObjectName("hint")
        note.setWordWrap(True)
        lay.addWidget(note)

        self.btn_solve = QPushButton("Решить   (Ctrl+Enter)")
        self.btn_solve.setObjectName("primary")
        self.btn_solve.clicked.connect(self.solve)
        lay.addWidget(self.btn_solve)

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

    def values(self) -> Dict[str, Any]:
        out = {}
        for f in self.task.fields:
            ed = self.editors[f.key]
            if f.kind == "vector":
                out[f.key] = tuple(e.text().strip() for e in ed)
            elif f.kind == "choice":
                out[f.key] = ed.currentText()
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
            else:
                ed.setText(str(val))

    def _on_preset(self, index: int):
        if index <= 0:
            return
        self.set_values(self.task.presets[index - 1].values)
        self.solve()

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

    def solve(self):
        try:
            res = self.task.run(self.values())
        except Exception as ex:  # ошибки ввода и математические исключения показываем пользователю
            msg = str(ex) or ex.__class__.__name__
            self.error_label.setText(f"Ошибка: {msg}")
            self.status.emit(f"Ошибка: {msg}", True)
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
