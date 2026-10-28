"""Проверки интерфейса без дисплея (QT_QPA_PLATFORM=offscreen)."""

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QSettings  # noqa: E402
from PySide6.QtGui import QTextDocument  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from mathcalc.gui.solution_view import steps_to_html  # noqa: E402
from mathcalc.tasks import all_tasks, get_task  # noqa: E402


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance() or QApplication([])
    QSettings("MathCalc", "MathCalc").clear()
    yield application


@pytest.fixture(scope="module")
def window(app):
    from mathcalc.gui.main_window import MainWindow
    w = MainWindow()
    w.show()
    yield w
    w.close()


def test_html_has_no_empty_colored_blocks(app):
    """Пустые строки решения не должны превращаться в пустые цветные карточки."""
    for task in all_tasks():
        doc = QTextDocument()
        doc.setHtml(steps_to_html(task.run().steps, dark=True))
        block = doc.begin()
        colored_empty_run = 0
        while block.isValid():
            colored = block.blockFormat().background().style() != 0
            colored_empty_run = colored_empty_run + 1 if (colored and not block.text().strip()) else 0
            # допускается одна пустая строка-отступ сверху и снизу карточки
            assert colored_empty_run <= 2, task.id
            block = block.next()


def test_every_task_page_solves(window, app):
    for task in all_tasks():
        window.open_item(task.id)
        page = window.pages[task.id]
        page.solve()
        app.processEvents()
        assert page.error_label.text() == "", (task.id, page.error_label.text())
        assert page.solution.raw_text


def test_bad_input_shows_error_not_exception(window, app):
    window.open_item("geometry.plane.point_normal")
    page = window.pages["geometry.plane.point_normal"]
    page.editors['n'][0].setText("abc+")
    page.solve()
    assert "Не удалось разобрать" in page.error_label.text()
    page.editors['n'][0].setText("2")
    page.solve()
    assert page.error_label.text() == ""


def test_preset_loads_values(window, app):
    task = get_task("geometry.planar.triangle")
    window.open_item(task.id)
    page = window.pages[task.id]
    page._on_preset(2)
    assert page.values()['A'] == task.presets[1].values['A']


def test_search_filters_tree(window, app):
    window.search.setText("биссектр")
    app.processEvents()
    visible = []
    stack = [window.nav.invisibleRootItem()]
    while stack:
        node = stack.pop()
        for i in range(node.childCount()):
            ch = node.child(i)
            if not ch.isHidden():
                stack.append(ch)
                if ch.childCount() == 0:
                    visible.append(ch.text(0))
    window.search.clear()
    assert visible and all("Треугольник" in v for v in visible)


def test_theme_switch(window, app):
    window.set_dark(False)
    window.set_dark(True)
