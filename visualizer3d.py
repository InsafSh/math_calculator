"""
Visualizer 3D - Модуль интерактивной 3D визуализации плоскостей, прямых, векторов и точек.
Использует Matplotlib 3D с интеграцией в CustomTkinter и удобной навигацией возврата к расчету.
"""

import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import customtkinter as ctk
from typing import List, Dict, Any, Optional, Tuple, Callable


class Visualizer3DPanel(ctk.CTkFrame):
    """Виджет интерактивной 3D сцены для отображения аналитической геометрии."""

    COLORS = [
        '#3B82F6',  # Blue
        '#EF4444',  # Red
        '#10B981',  # Emerald
        '#F59E0B',  # Amber
        '#8B5CF6',  # Purple
        '#EC4899',  # Pink
        '#06B6D4',  # Cyan
    ]

    def __init__(self, master, bg_dark: bool = True, on_back: Optional[Callable] = None, on_navigate: Optional[Callable] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.bg_dark = bg_dark
        self.on_back_callback = on_back
        self.on_navigate_callback = on_navigate
        self.last_tab_name = "📐 Плоскость"

        # Данные сцены
        self.planes: List[Dict[str, Any]] = []
        self.lines: List[Dict[str, Any]] = []
        self.points: List[Dict[str, Any]] = []
        self.vectors: List[Dict[str, Any]] = []
        self.segments: List[Dict[str, Any]] = []

        # 1. Верхняя панель навигации (кнопка возврата к меню ввода)
        self._build_top_nav()

        # 2. Создаем фигуру Matplotlib
        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.fig.add_subplot(111, projection='3d')
        self._apply_theme()

        # Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=4, pady=2)

        # 3. Нижняя панель управления камерой
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=4)
        self._build_controls()

        self.reset_scene()

    def _build_top_nav(self):
        """Панель навигации вверху 3D экрана с кнопкой возврата."""
        self.top_nav = ctk.CTkFrame(self, corner_radius=8, fg_color=("#E2E8F0", "#1E2235"))
        self.top_nav.pack(side=tk.TOP, fill=tk.X, padx=6, pady=(4, 6))

        # Главная кнопка возврата назад к расчету
        self.btn_back = ctk.CTkButton(
            self.top_nav,
            text=f"⬅ ВЕРНУТЬСЯ К ВВОДУ И РАСЧЕТУ ({self.last_tab_name})",
            font=("Segoe UI", 13, "bold"),
            height=34,
            fg_color="#10B981",
            hover_color="#059669",
            command=self._on_back_clicked
        )
        self.btn_back.pack(side=tk.LEFT, padx=8, pady=6)

        # Разделитель и быстрые кнопки перехода
        lbl_jump = ctk.CTkLabel(self.top_nav, text="Перейти в:", font=("Segoe UI", 11, "bold"), text_color=("#64748B", "#94A3B8"))
        lbl_jump.pack(side=tk.LEFT, padx=(10, 4))

        quick_tabs = [
            ("📐 Плоскость", "📐"),
            ("📏 Прямая", "📏"),
            ("⚖️ Взаимное расположение", "⚖️"),
            ("🎯 Расстояния и проекции", "🎯"),
            ("🌀 Пучок плоскостей", "🌀"),
            ("📝 КР: Блок II", "📝")
        ]

        for full_name, short_label in quick_tabs:
            btn_tab = ctk.CTkButton(
                self.top_nav, text=short_label, width=38, height=30,
                font=("Segoe UI", 12),
                fg_color=("#CBD5E1", "#2D3748"),
                hover_color=("#94A3B8", "#4A5568"),
                command=lambda fn=full_name: self._on_navigate_clicked(fn)
            )
            btn_tab.pack(side=tk.LEFT, padx=2)

        # Подсказка по управлению мышью справа
        lbl_hint = ctk.CTkLabel(
            self.top_nav,
            text="🖱 Вращение: ЛКМ | Масштаб: колесо | Панорама: ПКМ",
            font=("Segoe UI", 11),
            text_color=("#64748B", "#94A3B8")
        )
        lbl_hint.pack(side=tk.RIGHT, padx=12, pady=6)

    def set_last_tab(self, tab_name: str):
        """Обновление названия вкладки для возврата."""
        self.last_tab_name = tab_name
        self.btn_back.configure(text=f"⬅ ВЕРНУТЬСЯ К ВВОДУ И РАСЧЕТУ ({tab_name})")

    def _on_back_clicked(self):
        if self.on_back_callback:
            self.on_back_callback(self.last_tab_name)

    def _on_navigate_clicked(self, tab_name: str):
        if self.on_navigate_callback:
            self.on_navigate_callback(tab_name)
        elif self.on_back_callback:
            self.on_back_callback(tab_name)

    def _apply_theme(self):
        """Стилизация под темную или светлую тему."""
        if self.bg_dark:
            bg_color = '#1A1B26'
            pane_color = '#24283B'
            text_color = '#C0CAF5'
            grid_color = '#414868'
        else:
            bg_color = '#F8FAFC'
            pane_color = '#E2E8F0'
            text_color = '#1E293B'
            grid_color = '#CBD5E1'

        self.fig.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)

        for axis in (self.ax.xaxis, self.ax.yaxis, self.ax.zaxis):
            axis.pane.set_facecolor(pane_color)
            axis.pane.set_alpha(0.6)
            axis.pane.set_edgecolor(grid_color)
            axis.line.set_color(text_color)

        self.ax.tick_params(colors=text_color, labelsize=8)
        self.ax.set_xlabel('X', color=text_color, labelpad=4, fontweight='bold')
        self.ax.set_ylabel('Y', color=text_color, labelpad=4, fontweight='bold')
        self.ax.set_zlabel('Z', color=text_color, labelpad=4, fontweight='bold')
        self.ax.grid(True, linestyle='--', alpha=0.4, color=grid_color)

    def _build_controls(self):
        """Кнопки видов камеры и очистки."""
        btn_iso = ctk.CTkButton(
            self.controls_frame, text="Изометрия", width=80, height=26,
            command=lambda: self.set_camera(elev=25, azim=45)
        )
        btn_iso.pack(side=tk.LEFT, padx=3)

        btn_top = ctk.CTkButton(
            self.controls_frame, text="Сверху (XY)", width=80, height=26,
            command=lambda: self.set_camera(elev=90, azim=-90)
        )
        btn_top.pack(side=tk.LEFT, padx=3)

        btn_front = ctk.CTkButton(
            self.controls_frame, text="Спереди (XZ)", width=85, height=26,
            command=lambda: self.set_camera(elev=0, azim=-90)
        )
        btn_front.pack(side=tk.LEFT, padx=3)

        btn_side = ctk.CTkButton(
            self.controls_frame, text="Сбоку (YZ)", width=80, height=26,
            command=lambda: self.set_camera(elev=0, azim=0)
        )
        btn_side.pack(side=tk.LEFT, padx=3)

        btn_clear = ctk.CTkButton(
            self.controls_frame, text="Очистить сцену", width=110, height=26,
            fg_color="#EF4444", hover_color="#DC2626",
            command=self.clear_objects
        )
        btn_clear.pack(side=tk.RIGHT, padx=3)

    def set_camera(self, elev: float, azim: float):
        """Установка угла обзора камеры."""
        self.ax.view_init(elev=elev, azim=azim)
        self.canvas.draw_idle()

    def clear_objects(self):
        """Очистить все объекты и перерисовать координатную сетку."""
        self.planes.clear()
        self.lines.clear()
        self.points.clear()
        self.vectors.clear()
        self.segments.clear()
        self.redraw()

    def reset_scene(self):
        """Сброс до стандартного вида [-5, 5]."""
        self.clear_objects()
        self.ax.set_xlim([-5, 5])
        self.ax.set_ylim([-5, 5])
        self.ax.set_zlim([-5, 5])
        self.set_camera(elev=25, azim=45)

    def add_plane(self, A: float, B: float, C: float, D: float, label: str = "Плоскость", color: Optional[str] = None):
        """Добавить плоскость Ax + By + Cz + D = 0."""
        c = color or self.COLORS[len(self.planes) % len(self.COLORS)]
        self.planes.append({'A': float(A), 'B': float(B), 'C': float(C), 'D': float(D), 'label': label, 'color': c})

    def add_line(self, x0: float, y0: float, z0: float, m: float, p: float, q: float, label: str = "Прямая", color: Optional[str] = None):
        """Добавить прямую."""
        c = color or self.COLORS[(len(self.lines) + 2) % len(self.COLORS)]
        self.lines.append({'x0': float(x0), 'y0': float(y0), 'z0': float(z0), 'm': float(m), 'p': float(p), 'q': float(q), 'label': label, 'color': c})

    def add_point(self, x: float, y: float, z: float, label: str = "Точка", color: str = "#F59E0B"):
        """Добавить точку."""
        self.points.append({'x': float(x), 'y': float(y), 'z': float(z), 'label': label, 'color': color})

    def add_vector(self, x0: float, y0: float, z0: float, vx: float, vy: float, vz: float, label: str = "Вектор", color: str = "#10B981"):
        """Добавить вектор."""
        self.vectors.append({'x0': float(x0), 'y0': float(y0), 'z0': float(z0), 'vx': float(vx), 'vy': float(vy), 'vz': float(vz), 'label': label, 'color': color})

    def add_segment(self, p1: Tuple[float, float, float], p2: Tuple[float, float, float], label: str = "", color: str = "#94A3B8"):
        """Добавить отрезок (например, пунктир проекции)."""
        self.segments.append({'p1': p1, 'p2': p2, 'label': label, 'color': color})

    def redraw(self):
        """Отрисовка всех объектов на 3D сцене."""
        self.ax.cla()
        self._apply_theme()

        all_pts_x, all_pts_y, all_pts_z = [], [], []

        for pt in self.points:
            all_pts_x.append(pt['x'])
            all_pts_y.append(pt['y'])
            all_pts_z.append(pt['z'])

        for ln in self.lines:
            all_pts_x.extend([ln['x0'] - 2 * ln['m'], ln['x0'] + 2 * ln['m']])
            all_pts_y.extend([ln['y0'] - 2 * ln['p'], ln['y0'] + 2 * ln['p']])
            all_pts_z.extend([ln['z0'] - 2 * ln['q'], ln['z0'] + 2 * ln['q']])

        for seg in self.segments:
            all_pts_x.extend([seg['p1'][0], seg['p2'][0]])
            all_pts_y.extend([seg['p1'][1], seg['p2'][1]])
            all_pts_z.extend([seg['p1'][2], seg['p2'][2]])

        if all_pts_x:
            min_x, max_x = min(all_pts_x) - 2.5, max(all_pts_x) + 2.5
            min_y, max_y = min(all_pts_y) - 2.5, max(all_pts_y) + 2.5
            min_z, max_z = min(all_pts_z) - 2.5, max(all_pts_z) + 2.5
        else:
            min_x, max_x = -5.0, 5.0
            min_y, max_y = -5.0, 5.0
            min_z, max_z = -5.0, 5.0

        span = max(max_x - min_x, max_y - min_y, max_z - min_z, 6.0)
        cx = (min_x + max_x) / 2.0
        cy = (min_y + max_y) / 2.0
        cz = (min_z + max_z) / 2.0
        half_s = span / 2.0

        r_x = (cx - half_s, cx + half_s)
        r_y = (cy - half_s, cy + half_s)
        r_z = (cz - half_s, cz + half_s)

        grid_res = 12
        for pl in self.planes:
            A, B, C, D = pl['A'], pl['B'], pl['C'], pl['D']
            color = pl['color']

            if abs(C) >= 1e-5:
                gx = np.linspace(r_x[0], r_x[1], grid_res)
                gy = np.linspace(r_y[0], r_y[1], grid_res)
                X, Y = np.meshgrid(gx, gy)
                Z = (-A * X - B * Y - D) / C
                self.ax.plot_surface(X, Y, Z, alpha=0.35, color=color, edgecolor=color, linewidth=0.4)
            elif abs(B) >= 1e-5:
                gx = np.linspace(r_x[0], r_x[1], grid_res)
                gz = np.linspace(r_z[0], r_z[1], grid_res)
                X, Z = np.meshgrid(gx, gz)
                Y = (-A * X - D) / B
                self.ax.plot_surface(X, Y, Z, alpha=0.35, color=color, edgecolor=color, linewidth=0.4)
            elif abs(A) >= 1e-5:
                gy = np.linspace(r_y[0], r_y[1], grid_res)
                gz = np.linspace(r_z[0], r_z[1], grid_res)
                Y, Z = np.meshgrid(gy, gz)
                X = np.full_like(Y, -D / A)
                self.ax.plot_surface(X, Y, Z, alpha=0.35, color=color, edgecolor=color, linewidth=0.4)

        t_span = np.linspace(-half_s * 1.5, half_s * 1.5, 40)
        for ln in self.lines:
            x0, y0, z0 = ln['x0'], ln['y0'], ln['z0']
            m, p, q = ln['m'], ln['p'], ln['q']
            norm_s = np.sqrt(m**2 + p**2 + q**2) or 1.0
            lx = x0 + (m / norm_s) * t_span
            ly = y0 + (p / norm_s) * t_span
            lz = z0 + (q / norm_s) * t_span
            self.ax.plot(lx, ly, lz, color=ln['color'], linewidth=2.5, label=ln['label'])

        for seg in self.segments:
            p1, p2 = seg['p1'], seg['p2']
            self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]],
                         linestyle='--', color=seg['color'], linewidth=1.8, alpha=0.9)

        for vec in self.vectors:
            self.ax.quiver(vec['x0'], vec['y0'], vec['z0'],
                           vec['vx'], vec['vy'], vec['vz'],
                           color=vec['color'], linewidth=2.0, arrow_length_ratio=0.2)
            self.ax.text(vec['x0'] + vec['vx'], vec['y0'] + vec['vy'], vec['z0'] + vec['vz'],
                         f" {vec['label']}", color=vec['color'], fontsize=9, fontweight='bold')

        for pt in self.points:
            self.ax.scatter([pt['x']], [pt['y']], [pt['z']],
                            color=pt['color'], s=60, edgecolors='white', linewidth=1.2, zorder=10)
            self.ax.text(pt['x'] + 0.15, pt['y'] + 0.15, pt['z'] + 0.15,
                         f" {pt['label']}({pt['x']:.2g}; {pt['y']:.2g}; {pt['z']:.2g})",
                         color=pt['color'], fontsize=9, fontweight='bold')

        self.ax.set_xlim(r_x)
        self.ax.set_ylim(r_y)
        self.ax.set_zlim(r_z)

        handles, labels = self.ax.get_legend_handles_labels()
        if labels:
            leg = self.ax.legend(loc='upper right', fontsize=8, facecolor='#24283B' if self.bg_dark else '#E2E8F0')
            for text in leg.get_texts():
                text.set_color('#C0CAF5' if self.bg_dark else '#1E293B')

        self.canvas.draw_idle()
