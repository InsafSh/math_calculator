"""Все задачи реестра решаются на значениях по умолчанию и на всех примерах; сцены рисуются."""

import matplotlib
import matplotlib.pyplot as plt
import pytest

from mathcalc.core.result import Result
from mathcalc.plotting import DARK, LIGHT, render_scene2d, render_scene3d
from mathcalc.tasks import all_tasks, tree, register, Task
from mathcalc.tasks.registry import num

matplotlib.use("Agg")

CASES = [(t, None) for t in all_tasks()] + [(t, p) for t in all_tasks() for p in t.presets]


@pytest.mark.parametrize("task, preset", CASES, ids=lambda x: getattr(x, 'id', None) or getattr(x, 'name', None))
def test_task_solves(task, preset):
    res = task.run(preset.values if preset else None)
    assert isinstance(res, Result)
    assert res.steps.strip()
    assert res.summary.strip()


@pytest.mark.parametrize("task", all_tasks(), ids=lambda t: t.id)
def test_scenes_render(task):
    res = task.run()
    for theme in (DARK, LIGHT):
        if res.scene2d is not None:
            fig, ax = plt.subplots()
            render_scene2d(ax, res.scene2d, theme)
            plt.close(fig)
        if res.scene3d is not None:
            fig = plt.figure()
            ax = fig.add_subplot(projection='3d')
            render_scene3d(ax, res.scene3d, theme)
            plt.close(fig)


def test_presets_reference_existing_fields():
    for task in all_tasks():
        keys = {f.key for f in task.fields}
        for p in task.presets:
            assert set(p.values) <= keys, (task.id, p.name)


def test_tree_is_ordered_and_complete():
    t = tree()
    assert "Аналитическая геометрия" in t
    assert sum(len(ts) for groups in t.values() for ts in groups.values()) == len(all_tasks())


def test_duplicate_registration_rejected():
    task = all_tasks()[0]
    with pytest.raises(ValueError):
        register(Task(task.id, "S", "G", "T", [num('a', 'a')], lambda v: Result("x")))
