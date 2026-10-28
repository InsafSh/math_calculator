"""
Задачи всех разделов. Импорт этого пакета регистрирует задачи в реестре.
Чтобы добавить раздел, создайте модуль с вызовами register() и импортируйте его здесь.
"""

from . import geometry  # noqa: F401
from .registry import Task, Field, Preset, register, get_task, all_tasks, tree, SECTION_ORDER  # noqa: F401
