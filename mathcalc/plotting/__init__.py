"""
Отрисовка сцен на осях matplotlib. Не зависит от GUI: те же функции используются
в окне приложения, в тестах и при экспорте графиков в файлы.
"""

from .theme import PlotTheme, DARK, LIGHT  # noqa: F401
from .plot2d import render_scene2d  # noqa: F401
from .plot3d import render_scene3d  # noqa: F401
