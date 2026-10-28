"""Виджеты графиков: холст matplotlib с панелью инструментов (масштаб, сдвиг, сохранение PNG/SVG/PDF)."""

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

from ..plotting import DARK, render_scene2d, render_scene3d


class _PlotBase(QWidget):
    def __init__(self, parent=None, projection=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(6, 5), dpi=100, layout="tight" if projection is None else None)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_subplot(111, projection=projection)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.scene = None
        self.theme = DARK
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.top = QHBoxLayout()
        self.top.addWidget(self.toolbar)
        self.top.addStretch(1)
        lay.addLayout(self.top)
        lay.addWidget(self.canvas, 1)

    def set_scene(self, scene):
        self.scene = scene
        self.redraw()

    def set_theme(self, theme):
        self.theme = theme
        self.redraw()

    def redraw(self):
        raise NotImplementedError


class Plot2DWidget(_PlotBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.redraw()

    def redraw(self):
        render_scene2d(self.ax, self.scene, self.theme)
        self.canvas.draw_idle()


class Plot3DWidget(_PlotBase):
    VIEWS = (("Изометрия", 25, 45), ("XY", 90, -90), ("XZ", 0, -90), ("YZ", 0, 0))

    def __init__(self, parent=None):
        super().__init__(parent, projection='3d')
        for name, elev, azim in self.VIEWS:
            btn = QPushButton(name)
            btn.setToolTip(f"Вид камеры: {name}")
            btn.clicked.connect(lambda _=False, e=elev, a=azim: self.set_view(e, a))
            self.top.addWidget(btn)
        self.ax.view_init(elev=25, azim=45)
        self.redraw()

    def set_view(self, elev, azim):
        self.ax.view_init(elev=elev, azim=azim)
        self.canvas.draw_idle()

    def redraw(self):
        elev, azim = self.ax.elev, self.ax.azim
        render_scene3d(self.ax, self.scene, self.theme)
        self.ax.view_init(elev=elev, azim=azim)
        self.canvas.draw_idle()
