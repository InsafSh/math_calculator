"""
Вкладка «КР: Блок II» - решение типовых задач 6-10 контрольной работы
(аналитическая геометрия на плоскости и в пространстве) с пошаговым решением,
2D-чертежом (matplotlib) и выводом в 3D-визуализатор для пространственной задачи.
"""

import tkinter as tk
from tkinter import messagebox
import numpy as np
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from kr_block2 import (
    SegmentSolver, TriangleSolver, PlaneLineSolver, ConicSolver, SpaceTaskSolver
)
from geometry_core import parse_number

TAB_NAME = "📝 КР: Блок II"

MODE_SEGMENT = "6. Деление отрезка, середина, центр масс треугольника"
MODE_TRIANGLE = "7. Треугольник на плоскости (стороны, медиана, высота, угол, биссектриса)"
MODE_LINE2D = "8. Прямая и точка на плоскости (∥, ⊥, проекция, симметрия)"
MODE_CONIC = "9. Кривая 2-го порядка → канонический вид"
MODE_SPACE = "10. Плоскость ABC, прямая AD, перпендикуляр DH, прямая l"

MODES = [MODE_SEGMENT, MODE_TRIANGLE, MODE_LINE2D, MODE_CONIC, MODE_SPACE]

# Примеры из трёх вариантов КР (кнопка «Пример задачи» переключает варианты по кругу)
PRESETS = {
    MODE_SEGMENT: [
        dict(A=("-3", "2"), B=("7", "-3"), K=("2", "4"), m="3", n="2"),
        dict(A=("4", "-1"), B=("-6", "4"), K=("-1", "3"), m="2", n="3"),
        dict(A=("-2", "-5"), B=("6", "7"), K=("5", "1"), m="1", n="3"),
    ],
    MODE_TRIANGLE: [
        dict(A=("1", "2"), B=("4", "6"), C=("6", "-10")),
        dict(A=("-2", "1"), B=("2", "4"), C=("3", "13")),
        dict(A=("1", "-1"), B=("-2", "3"), C=("13", "4")),
    ],
    MODE_LINE2D: [
        dict(a="3", b="-4", c="12", M=("6", "-5")),
        dict(a="4", b="3", c="-6", M=("7", "1")),
        dict(a="5", b="-12", c="2", M=("7", "-11")),
    ],
    MODE_CONIC: [
        dict(c=("4", "0", "9", "-16", "54", "61")),
        dict(c=("0", "0", "1", "-8", "-4", "20")),
        dict(c=("9", "0", "-16", "36", "32", "-124")),
        dict(c=("1", "0", "0", "6", "4", "1")),
        dict(c=("25", "0", "16", "50", "-64", "-311")),
        dict(c=("0", "0", "1", "6", "2", "-11")),
        dict(c=("5", "2", "5", "-12", "-12", "0")),
        dict(c=("2", "2*sqrt(3)", "0", "-4", "-2*sqrt(3)", "-1")),
    ],
    MODE_SPACE: [
        dict(A=("2", "0", "0"), B=("0", "-4", "0"), C=("0", "0", "2"), D=("5", "-2", "5"),
             P1=("2", "-1", "1", "-2"), P2=("2", "-1", "-1", "0")),
        dict(A=("-2", "0", "0"), B=("0", "-1", "0"), C=("0", "0", "1"), D=("4", "3", "-3"),
             P1=("1", "1", "-1", "-1"), P2=("1", "-1", "-1", "1")),
        dict(A=("3", "0", "0"), B=("0", "3", "0"), C=("0", "0", "-6"), D=("-3", "-3", "0"),
             P1=("1", "1", "0", "-3"), P2=("1", "1", "2", "-3")),
    ],
}


class KRBlock2Tab:
    """Строит содержимое вкладки КР и обрабатывает вычисления."""

    def __init__(self, app, tab, solution_box_cls):
        self.app = app
        self.tab = tab
        self.solution_box_cls = solution_box_cls
        self.inputs = {}
        self.preset_idx = {m: 0 for m in MODES}
        self.last_plot = None
        self._build()

    # ------------------------------------------------------------------ каркас
    def _build(self):
        app, tab = self.app, self.tab

        top_bar = ctk.CTkFrame(tab, fg_color="transparent")
        top_bar.pack(fill=tk.X, padx=10, pady=(6, 10))
        ctk.CTkLabel(top_bar, text="Тип задачи (блок II):", font=("Segoe UI", 13, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        self.mode_cb = ctk.CTkOptionMenu(top_bar, values=MODES, width=520, command=self._on_mode_changed)
        self.mode_cb.pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(top_bar, text="📋 Пример задачи", width=130, command=self._next_preset).pack(side=tk.RIGHT, padx=5)

        panes = ctk.CTkFrame(tab, fg_color="transparent")
        panes.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        self.input_frame = ctk.CTkScrollableFrame(panes, width=420, label_text="Входные параметры")
        self.input_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 8), pady=2)

        right = ctk.CTkFrame(panes)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=2)

        self.right_tabs = ctk.CTkTabview(right, height=300)
        self.right_tabs.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        sol_tab = self.right_tabs.add("📝 Решение")
        plot_tab = self.right_tabs.add("📈 Чертёж (2D)")

        sol_header = ctk.CTkFrame(sol_tab, fg_color="transparent")
        sol_header.pack(fill=tk.X, padx=4, pady=(2, 6))
        ctk.CTkLabel(sol_header, text="Пошаговое аналитическое решение", font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT)
        self.btn_3d = ctk.CTkButton(sol_header, text="🔮 Показать в 3D", width=120, fg_color="#3B82F6",
                                    command=app.show_in_3d, state="disabled")
        self.btn_3d.pack(side=tk.RIGHT, padx=5)
        self.btn_copy = ctk.CTkButton(sol_header, text="📄 Копировать", width=110,
                                      command=lambda: app.copy_to_clipboard(self.sol_box), state="disabled")
        self.btn_copy.pack(side=tk.RIGHT, padx=5)

        self.sol_box = self.solution_box_cls(sol_tab)
        self.sol_box.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
        app.solution_boxes.append(self.sol_box)

        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_tab)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self._draw_plot(None)

        self._on_mode_changed(MODES[0])

    # ------------------------------------------------------------------ ввод
    def _row(self, label, default):
        return self.app._create_entry_row(self.input_frame, label, default)

    def _title(self, text, first=False):
        ctk.CTkLabel(self.input_frame, text=text, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4 if first else 10, 2))

    def _point_inputs(self, key, title, vals, dim):
        self._title(title)
        names = ["x", "y", "z"][:dim]
        self.inputs[key] = [self._row(f"{n}:", vals[i]) for i, n in enumerate(names)]

    def _vertex_menu(self, key, label, default):
        row = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        row.pack(fill=tk.X, pady=3)
        ctk.CTkLabel(row, text=label, width=160, anchor="w", font=("Segoe UI", 12)).pack(side=tk.LEFT)
        menu = ctk.CTkOptionMenu(row, values=["A", "B", "C"], width=90)
        menu.set(default)
        menu.pack(side=tk.LEFT)
        self.inputs[key] = menu

    def _on_mode_changed(self, mode, idx=None):
        for w in self.input_frame.winfo_children():
            w.destroy()
        self.inputs = {}
        if idx is None:
            idx = self.preset_idx[mode]
        pr = PRESETS[mode][idx % len(PRESETS[mode])]

        if mode == MODE_SEGMENT:
            self._point_inputs('A', "Точка A:", pr['A'], 2)
            self._point_inputs('B', "Точка B:", pr['B'], 2)
            self._point_inputs('K', "Точка K (третья вершина треугольника ABK):", pr['K'], 2)
            self._title("Отношение AC : CB = m : n (отрицательное — внешнее деление)")
            self.inputs['m'] = self._row("m:", pr['m'])
            self.inputs['n'] = self._row("n:", pr['n'])
        elif mode == MODE_TRIANGLE:
            self._point_inputs('A', "Вершина A:", pr['A'], 2)
            self._point_inputs('B', "Вершина B:", pr['B'], 2)
            self._point_inputs('C', "Вершина C:", pr['C'], 2)
            self._title("Какие элементы построить")
            self._vertex_menu('med', "Медиана из вершины:", "A")
            self._vertex_menu('alt', "Высота из вершины:", "B")
            self._vertex_menu('ang', "Угол и биссектриса при вершине:", "A")
        elif mode == MODE_LINE2D:
            self._title("Прямая l:  A·x + B·y + C = 0", first=True)
            self.inputs['a'] = self._row("A:", pr['a'])
            self.inputs['b'] = self._row("B:", pr['b'])
            self.inputs['c'] = self._row("C:", pr['c'])
            self._point_inputs('M', "Точка M:", pr['M'], 2)
        elif mode == MODE_CONIC:
            self._title("A·x² + B·xy + C·y² + D·x + E·y + F = 0", first=True)
            ctk.CTkLabel(self.input_frame, text="Допустимы дроби, десятичные числа, sqrt(3).\nЕсли B ≠ 0, будет выполнен поворот осей.",
                         font=("Segoe UI", 11), text_color="#94A3B8", justify="left").pack(anchor="w")
            labels = ["A (при x²):", "B (при xy):", "C (при y²):", "D (при x):", "E (при y):", "F (свободный):"]
            self.inputs['coef'] = [self._row(labels[i], pr['c'][i]) for i in range(6)]
        elif mode == MODE_SPACE:
            self._point_inputs('A', "Точка A:", pr['A'], 3)
            self._point_inputs('B', "Точка B:", pr['B'], 3)
            self._point_inputs('C', "Точка C:", pr['C'], 3)
            self._point_inputs('D', "Точка D:", pr['D'], 3)
            for key, ttl in (('P1', "Прямая l, плоскость 1:  A₁x + B₁y + C₁z + D₁ = 0"),
                             ('P2', "Прямая l, плоскость 2:  A₂x + B₂y + C₂z + D₂ = 0")):
                self._title(ttl)
                self.inputs[key] = [self._row(n, pr[key][i]) for i, n in enumerate(["A:", "B:", "C:", "D:"])]

        ctk.CTkButton(
            self.input_frame, text="⚡ Решить задачу", font=("Segoe UI", 13, "bold"), height=36,
            fg_color="#10B981", hover_color="#059669", command=self._calc
        ).pack(fill=tk.X, pady=(15, 6))

    def _next_preset(self):
        mode = self.mode_cb.get()
        self.preset_idx[mode] = (self.preset_idx[mode] + 1) % len(PRESETS[mode])
        self._on_mode_changed(mode, self.preset_idx[mode])
        self._calc()

    def _vals(self, key):
        return tuple(e.get() for e in self.inputs[key])

    # ------------------------------------------------------------------ вычисление
    def _calc(self):
        app = self.app
        try:
            app.current_calc_tab = TAB_NAME
            mode = self.mode_cb.get()
            show3d = False

            if mode == MODE_SEGMENT:
                res = SegmentSolver.solve(self._vals('A'), self._vals('B'), self._vals('K'),
                                          self.inputs['m'].get(), self.inputs['n'].get())
            elif mode == MODE_TRIANGLE:
                res = TriangleSolver.solve(self._vals('A'), self._vals('B'), self._vals('C'),
                                           self.inputs['med'].get(), self.inputs['alt'].get(), self.inputs['ang'].get())
            elif mode == MODE_LINE2D:
                res = PlaneLineSolver.solve(self.inputs['a'].get(), self.inputs['b'].get(), self.inputs['c'].get(),
                                            self._vals('M'))
            elif mode == MODE_CONIC:
                res = ConicSolver.solve(*[e.get() for e in self.inputs['coef']])
            else:
                res = SpaceTaskSolver.solve(self._vals('A'), self._vals('B'), self._vals('C'), self._vals('D'),
                                            self._vals('P1'), self._vals('P2'))
                self._fill_3d(res)
                show3d = True

            self.sol_box.set_solution(res['steps'])
            self.btn_copy.configure(state="normal")
            self.btn_3d.configure(state="normal" if show3d else "disabled")
            if 'plot2d' in res:
                self.last_plot = res['plot2d']
                self._draw_plot(self.last_plot)
            else:
                self.last_plot = None
                self._draw_plot(None)
            app.set_status("✓ Задача решена! Чертёж — на вкладке «Чертёж (2D)»." if not show3d
                           else "✓ Задача решена! Нажмите «Показать в 3D» для пространственной картины.")
        except Exception as ex:
            app.set_status(f"Ошибка вычисления: {str(ex)}", is_error=True)
            messagebox.showerror("Ошибка", f"Проверьте правильность введенных данных:\n{str(ex)}")

    def _fill_3d(self, res):
        v = self.app.viz_panel
        v.clear_objects()
        a, b, c, d = [float(x) for x in res['plane']]
        v.add_plane(a, b, c, d, "Плоскость ABC", color="#3B82F6")
        pa, pb, pc, pd = [float(x) for x in res['parallel_plane']]
        v.add_plane(pa, pb, pc, pd, "Параллельная через D", color="#10B981")
        for nm, p in res['points'].items():
            v.add_point(float(p[0]), float(p[1]), float(p[2]), nm, color="#EF4444" if nm == 'D' else "#F59E0B")
        H = [float(x) for x in res['H']]
        v.add_point(H[0], H[1], H[2], "H", color="#10B981")
        D = res['points']['D']
        v.add_segment((float(D[0]), float(D[1]), float(D[2])), (H[0], H[1], H[2]), "DH", color="#EF4444")
        A, s = res['line_AD']
        v.add_line(float(A[0]), float(A[1]), float(A[2]), float(s[0]), float(s[1]), float(s[2]), "Прямая AD", color="#F59E0B")
        M0, s2 = res['line_l']
        v.add_line(float(M0[0]), float(M0[1]), float(M0[2]), float(s2[0]), float(s2[1]), float(s2[2]), "Прямая l", color="#EC4899")
        v.redraw()

    # ------------------------------------------------------------------ 2D-чертёж
    def redraw_theme(self):
        self._draw_plot(self.last_plot)

    def _draw_plot(self, plot):
        dark = self.app.is_dark
        bg, fg, grid = ('#1A1B26', '#C0CAF5', '#414868') if dark else ('#F8FAFC', '#1E293B', '#CBD5E1')
        ax = self.ax
        ax.clear()
        self.fig.patch.set_facecolor(bg)
        ax.set_facecolor(bg)
        ax.tick_params(colors=fg, labelsize=8)
        for sp_ in ax.spines.values():
            sp_.set_color(grid)
        ax.grid(True, linestyle='--', alpha=0.4, color=grid)
        ax.axhline(0, color=fg, linewidth=0.8, alpha=0.6)
        ax.axvline(0, color=fg, linewidth=0.8, alpha=0.6)

        if not plot:
            ax.text(0.5, 0.5, "Чертёж появится после решения задачи", transform=ax.transAxes,
                    ha='center', va='center', color=fg, fontsize=11)
            self.canvas.draw_idle()
            return

        xs, ys = [], []
        for (x, y, _n, _c) in plot['points']:
            xs.append(x); ys.append(y)
        for (p1, p2, *_r) in plot['segments']:
            xs += [p1[0], p2[0]]; ys += [p1[1], p2[1]]
        for (px, py, *_r) in plot['lines']:
            xs.append(px); ys.append(py)
        for (cx, cy, *_r) in plot['curves']:
            closed = abs(cx[0] - cx[-1]) < 1e-9 and abs(cy[0] - cy[-1]) < 1e-9
            n = len(cx)
            sl = slice(None) if closed else slice(int(n * 0.2), int(n * 0.8))
            xs += list(cx[sl]); ys += list(cy[sl])
        if not xs:
            xs, ys = [-5, 5], [-5, 5]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        span = max(x1 - x0, y1 - y0, 2.0)
        pad = span * 0.18
        cxm, cym = (x0 + x1) / 2, (y0 + y1) / 2
        half = span / 2 + pad
        xlim, ylim = (cxm - half, cxm + half), (cym - half, cym + half)

        for (px, py, dx, dy, label, col) in plot['lines']:
            nrm = float(np.hypot(dx, dy)) or 1.0
            t = np.array([-1.0, 1.0]) * span * 20 / nrm
            ax.plot(px + dx * t, py + dy * t, color=col, linewidth=1.4, alpha=0.85,
                    linestyle='--' if label.startswith('асимптот') else '-',
                    label=label or None)
        for (cx, cy, label, col) in plot['curves']:
            ax.plot(cx, cy, color=col, linewidth=2.2, label=label or None)
        for (p1, p2, label, col, style) in plot['segments']:
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=col, linewidth=1.8, linestyle=style, label=label or None)
        for (x, y, name, col) in plot['points']:
            ax.scatter([x], [y], color=col, s=42, zorder=5, edgecolors='white', linewidths=0.8)
            ax.annotate(name, (x, y), textcoords="offset points", xytext=(6, 6), color=col, fontsize=10, fontweight='bold')

        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_aspect('equal', adjustable='box')
        ax.set_title(plot.get('title', ''), color=fg, fontsize=11)
        handles, labels = ax.get_legend_handles_labels()
        if labels:
            leg = ax.legend(loc='best', fontsize=8, facecolor=bg, edgecolor=grid)
            for t in leg.get_texts():
                t.set_color(fg)
        self.canvas.draw_idle()
