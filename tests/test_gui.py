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


def test_solution_fits_narrow_width(app):
    """Длинные строки (в т.ч. в карточках формул и ответов) переносятся и не выходят за ширину окна."""
    from PySide6.QtGui import QTextOption
    width = 520
    for task in all_tasks():
        for preset in [None] + task.presets:
            doc = QTextDocument()
            opt = QTextOption()
            opt.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
            doc.setDefaultTextOption(opt)
            doc.setHtml(steps_to_html(task.run(preset.values if preset else None).steps))
            doc.setTextWidth(width)
            assert doc.idealWidth() <= width + 1, (task.id, preset and preset.name, doc.idealWidth())


def test_every_task_page_solves(window, app):
    for task in all_tasks():
        window.open_item(task.id)
        page = window.pages[task.id]
        page.solve(blocking=True)
        app.processEvents()
        assert page.error_label.text() == "", (task.id, page.error_label.text())
        assert page.solution.raw_text


def _wait(app, cond, timeout=30.0):
    import time
    end = time.monotonic() + timeout
    while not cond() and time.monotonic() < end:
        app.processEvents()
        time.sleep(0.01)
    return cond()


def test_background_solve_and_cancel(window, app):
    """Решение в фоновом потоке: интерфейс получает результат; прерванный результат отбрасывается."""
    window.open_item("calculus.definite")
    page = window.pages["calculus.definite"]
    page.solution.set_placeholder()
    page.solve()
    assert not page.btn_solve.isEnabled()
    assert _wait(app, lambda: page.btn_solve.isEnabled())
    assert page.solution.raw_text and page.error_label.text() == ""

    page.solution.set_placeholder()
    page.solve()
    page.cancel()
    assert page.btn_solve.isEnabled()
    _wait(app, lambda: False, timeout=1.5)  # даём потоку завершиться
    assert page.solution.raw_text == ""      # результат прерванного вычисления не показан


def test_bad_input_shows_error_not_exception(window, app):
    window.open_item("geometry.plane.point_normal")
    page = window.pages["geometry.plane.point_normal"]
    page.editors['n'][0].setText("abc+")
    page.solve(blocking=True)
    assert "Не удалось разобрать" in page.error_label.text()
    page.editors['n'][0].setText("2")
    page.solve(blocking=True)
    assert page.error_label.text() == ""


def test_text_and_formula_fields(window, app):
    window.open_item("experiment.fit")
    page = window.pages["experiment.fit"]
    page.set_values({'data': "1 2\n2 4.1\n3 5.9\n4 8.2", 'model': "Пропорциональность  y = b·x"})
    page.solve(blocking=True)
    assert page.error_label.text() == ""
    assert abs(page.result.values['params']['b'] - 2.02) < 0.05
    assert page.tabs.isTabEnabled(page.TAB_2D)


def test_preset_loads_values(window, app):
    task = get_task("geometry.planar.triangle")
    window.open_item(task.id)
    page = window.pages[task.id]
    page._on_preset(2, blocking=True)
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


def test_each_section_opens_its_own_handbook(window, app):
    from mathcalc.core.handbooks import HANDBOOKS
    from mathcalc.gui.main_window import HANDBOOK_PREFIX
    for section, (_title, sections) in HANDBOOKS.items():
        window.open_item(HANDBOOK_PREFIX + section)
        assert window.pages[HANDBOOK_PREFIX + section].sections is sections


def test_theme_switch(window, app):
    window.set_dark(False)
    window.set_dark(True)
