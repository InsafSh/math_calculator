"""Главное окно: дерево разделов с поиском слева, страница задачи справа."""

import sys

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication, QLabel, QLineEdit, QMainWindow, QMessageBox, QSplitter, QStackedWidget,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from .. import __version__
from ..core.geometry.handbook import HANDBOOK_SECTIONS
from ..tasks import get_task, tree
from .handbook_page import HandbookPage
from .task_page import TaskPage
from .theme import apply_theme

APP_NAME = "MathCalc"
ROLE_ID = Qt.UserRole
ROLE_SEARCH = Qt.UserRole + 1
HANDBOOK_ID = "handbook.geometry"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — расчёты с пошаговыми решениями")
        self.resize(1400, 880)
        self.settings = QSettings(APP_NAME, APP_NAME)
        self.dark = self.settings.value("dark", True, type=bool)
        self.plot_theme = apply_theme(QApplication.instance(), self.dark)
        self.pages = {}

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._build_nav())
        self.stack = QStackedWidget()
        self.stack.addWidget(self._welcome())
        splitter.addWidget(self.stack)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([360, 1040])
        self.setCentralWidget(splitter)

        self._build_menu()
        self.statusBar().showMessage("Выберите задачу в списке слева")

        last = self.settings.value("last_task", "", type=str)
        if last:
            self.open_item(last)
        geom = self.settings.value("geometry")
        if geom is not None:
            self.restoreGeometry(geom)

    # ------------------------------------------------------------------ навигация
    def _build_nav(self) -> QWidget:
        holder = QWidget()
        lay = QVBoxLayout(holder)
        lay.setContentsMargins(6, 6, 0, 6)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск задачи…  (Ctrl+F)")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._filter)
        lay.addWidget(self.search)

        self.nav = QTreeWidget()
        self.nav.setHeaderHidden(True)
        bold = QFont()
        bold.setBold(True)
        for section, groups in tree().items():
            s_item = QTreeWidgetItem([section])
            s_item.setFont(0, bold)
            s_item.setFlags(Qt.ItemIsEnabled)
            self.nav.addTopLevelItem(s_item)
            for group, tasks in groups.items():
                g_item = QTreeWidgetItem([group])
                g_item.setFlags(Qt.ItemIsEnabled)
                s_item.addChild(g_item)
                for t in tasks:
                    t_item = QTreeWidgetItem([t.title])
                    t_item.setData(0, ROLE_ID, t.id)
                    t_item.setData(0, ROLE_SEARCH, f"{t.title} {t.description}".lower())
                    t_item.setToolTip(0, f"<b>{t.title}</b><br>{t.description}" if t.description else t.title)
                    g_item.addChild(t_item)
            hb = QTreeWidgetItem(["Справочник по разделу"])
            hb.setData(0, ROLE_ID, HANDBOOK_ID)
            s_item.addChild(hb)
            s_item.setExpanded(True)
        self.nav.itemClicked.connect(self._on_item)
        self.nav.itemActivated.connect(self._on_item)
        lay.addWidget(self.nav, 1)
        return holder

    def _welcome(self) -> QWidget:
        w = QLabel(
            f"<h2>{APP_NAME} {__version__}</h2>"
            "<p>Выберите задачу в списке слева или найдите её поиском.</p>"
            "<p>Для каждой задачи: форма ввода, пошаговое решение, 2D-чертёж или 3D-сцена, "
            "экспорт решения (HTML, TXT) и графиков (PNG, SVG, PDF).</p>")
        w.setAlignment(Qt.AlignCenter)
        w.setWordWrap(True)
        return w

    def _filter(self, text: str):
        text = text.strip().lower()
        for i in range(self.nav.topLevelItemCount()):
            sec = self.nav.topLevelItem(i)
            sec_visible = False
            for j in range(sec.childCount()):
                node = sec.child(j)
                if node.childCount() == 0:  # отдельный пункт раздела (справочник)
                    vis = not text or text in node.text(0).lower()
                    node.setHidden(not vis)
                    sec_visible |= vis
                    continue
                group_match = text in node.text(0).lower()
                any_vis = False
                for k in range(node.childCount()):
                    leaf = node.child(k)
                    vis = not text or group_match or text in (leaf.data(0, ROLE_SEARCH) or leaf.text(0).lower())
                    leaf.setHidden(not vis)
                    any_vis |= vis
                node.setHidden(not any_vis)
                node.setExpanded(bool(text) and any_vis)
                sec_visible |= any_vis
            sec.setHidden(not sec_visible)
            sec.setExpanded(True)

    def _on_item(self, item: QTreeWidgetItem, _col: int = 0):
        item_id = item.data(0, ROLE_ID)
        if item_id:
            self.open_item(item_id)
        else:
            item.setExpanded(not item.isExpanded())

    def open_item(self, item_id: str):
        page = self.pages.get(item_id)
        if page is None:
            if item_id == HANDBOOK_ID:
                page = HandbookPage("Справочник: аналитическая геометрия", HANDBOOK_SECTIONS)
            else:
                try:
                    task = get_task(item_id)
                except KeyError:
                    return
                page = TaskPage(task)
                page.status.connect(self._on_status)
            page.apply_theme(self.dark, self.plot_theme)
            self.pages[item_id] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)
        self.statusBar().setStyleSheet("")
        self.statusBar().showMessage(getattr(getattr(page, 'task', None), 'title', "Справочник"))
        self.settings.setValue("last_task", item_id)
        self._select_in_nav(item_id)

    def _select_in_nav(self, item_id: str):
        it = self.nav.invisibleRootItem()
        stack = [it]
        while stack:
            node = stack.pop()
            if node.data(0, ROLE_ID) == item_id:
                self.nav.setCurrentItem(node)
                return
            stack.extend(node.child(i) for i in range(node.childCount()))

    def _on_status(self, text: str, is_error: bool):
        self.statusBar().setStyleSheet("color: #EF4444;" if is_error else "")
        self.statusBar().showMessage(text, 0 if is_error else 15000)

    # ------------------------------------------------------------------ меню и тема
    def _build_menu(self):
        m_file = self.menuBar().addMenu("&Файл")
        act_quit = QAction("Выход", self, shortcut="Ctrl+Q", triggered=self.close)
        m_file.addAction(act_quit)

        m_view = self.menuBar().addMenu("&Вид")
        self.act_dark = QAction("Тёмная тема", self, checkable=True, checked=self.dark, triggered=self.set_dark)
        m_view.addAction(self.act_dark)
        act_find = QAction("Найти задачу", self, shortcut="Ctrl+F", triggered=lambda: self.search.setFocus())
        m_view.addAction(act_find)

        m_help = self.menuBar().addMenu("&Справка")
        m_help.addAction(QAction("О программе", self, triggered=self._about))

    def set_dark(self, dark: bool):
        self.dark = dark
        self.settings.setValue("dark", dark)
        self.plot_theme = apply_theme(QApplication.instance(), dark)
        for page in self.pages.values():
            page.apply_theme(dark, self.plot_theme)

    def _about(self):
        QMessageBox.about(self, f"О программе {APP_NAME}",
                          f"<b>{APP_NAME} {__version__}</b><br>"
                          "Математические расчёты с прозрачными пошаговыми решениями и визуализацией.<br><br>"
                          "Ядро: SymPy, NumPy. Графики: Matplotlib. Интерфейс: PySide6 (Qt).")

    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)


def run() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    win = MainWindow()
    win.show()
    return app.exec()
