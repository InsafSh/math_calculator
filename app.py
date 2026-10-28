"""
Главное приложение: Калькулятор аналитической геометрии в пространстве (Глава 4: Плоскости и прямые)
Современный интерфейс на CustomTkinter с интерактивной 3D визуализацией,
красивым математическим выводом (знаки корня √, степени ², индексы ₀) и навигацией возврата.
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from geometry_core import (
    PlaneSolver, LineSolver, RelationsSolver,
    DistancesAndProjections, PlanePencilSolver,
    fmt_num, fmt_point, fmt_vector, to_pretty_math
)
from visualizer3d import Visualizer3DPanel
from kr_tab import KRBlock2Tab, TAB_NAME as KR_TAB_NAME
from theory_handbook import HANDBOOK_SECTIONS

# Настройка темы CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class RichSolutionBox(ctk.CTkTextbox):
    """Виджет для красивого отображения математических решений со стилями и цветами."""

    def __init__(self, master, **kwargs):
        super().__init__(master, font=("Consolas", 12), wrap="word", **kwargs)
        self.raw_text = ""
        self.is_dark = True
        self._configure_tags()

    def _configure_tags(self):
        tw = self._textbox
        if self.is_dark:
            tw.tag_config('header', font=('Segoe UI', 12, 'bold'), foreground='#38BDF8', spacing1=10, spacing3=4)
            tw.tag_config('formula', font=('Consolas', 11, 'bold'), foreground='#FBBF24', background='#1E293B', lmargin1=14, lmargin2=14, spacing1=3, spacing3=3)
            tw.tag_config('answer', font=('Consolas', 12, 'bold'), foreground='#34D399', background='#064E3B', lmargin1=14, lmargin2=14, spacing1=5, spacing3=5)
            tw.tag_config('bullet', font=('Segoe UI', 11, 'bold'), foreground='#67E8F9', lmargin1=10, lmargin2=20, spacing1=2, spacing3=2)
            tw.tag_config('body', font=('Segoe UI', 11), foreground='#E2E8F0', lmargin1=10, lmargin2=10, spacing1=2, spacing3=2)
            tw.tag_config('subtext', font=('Segoe UI', 10), foreground='#94A3B8', lmargin1=10, lmargin2=10)
        else:
            tw.tag_config('header', font=('Segoe UI', 12, 'bold'), foreground='#0284C7', spacing1=10, spacing3=4)
            tw.tag_config('formula', font=('Consolas', 11, 'bold'), foreground='#B45309', background='#FEF3C7', lmargin1=14, lmargin2=14, spacing1=3, spacing3=3)
            tw.tag_config('answer', font=('Consolas', 12, 'bold'), foreground='#047857', background='#D1FAE5', lmargin1=14, lmargin2=14, spacing1=5, spacing3=5)
            tw.tag_config('bullet', font=('Segoe UI', 11, 'bold'), foreground='#0891B2', lmargin1=10, lmargin2=20, spacing1=2, spacing3=2)
            tw.tag_config('body', font=('Segoe UI', 11), foreground='#1E293B', lmargin1=10, lmargin2=10, spacing1=2, spacing3=2)
            tw.tag_config('subtext', font=('Segoe UI', 10), foreground='#64748B', lmargin1=10, lmargin2=10)

    def set_theme(self, is_dark: bool):
        self.is_dark = is_dark
        self._configure_tags()
        if self.raw_text:
            self.set_solution(self.raw_text)

    def set_solution(self, text: str):
        self.raw_text = text
        tw = self._textbox
        tw.delete('1.0', tk.END)

        for line in text.split('\n'):
            line_str = line.rstrip()
            if not line_str:
                tw.insert(tk.END, '\n')
                continue

            # Заголовки этапов
            if line_str.startswith(('📌', '📝', '⚙️', '📍', '🔄', '📐', '📏')):
                tw.insert(tk.END, line_str + '\n', 'header')
            # Карточки формул
            elif line_str.startswith(('   ┌', '   │', '   └')):
                tw.insert(tk.END, line_str + '\n', 'formula')
            # Итоговый ответ / акцентные карточки
            elif line_str.startswith(('   ╔', '   ║', '   ╚', '🎯', 'ИТОГ')):
                tw.insert(tk.END, line_str + '\n', 'answer')
            # Пункты и подстановки
            elif '▸' in line_str or '•' in line_str:
                tw.insert(tk.END, line_str + '\n', 'bullet')
            elif line_str.startswith('   where') or line_str.startswith('   где'):
                tw.insert(tk.END, line_str + '\n', 'subtext')
            else:
                tw.insert(tk.END, line_str + '\n', 'body')


class GeoCalculatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Калькулятор аналитической геометрии в пространстве (Глава 4: Плоскости и прямые)")
        self.geometry("1200x840")
        self.minsize(1000, 720)

        self.current_calc_tab = "📐 Плоскость"
        self.is_dark = True
        self.solution_boxes: list[RichSolutionBox] = []

        # Верхняя панель заголовка
        self._build_header()

        # Главный TabView
        self.tabview = ctk.CTkTabview(self, corner_radius=10, command=self._on_tab_changed)
        self.tabview.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))

        # Создаем вкладки
        self.tab_plane = self.tabview.add("📐 Плоскость")
        self.tab_line = self.tabview.add("📏 Прямая")
        self.tab_relations = self.tabview.add("⚖️ Взаимное расположение")
        self.tab_distances = self.tabview.add("🎯 Расстояния и проекции")
        self.tab_pencil = self.tabview.add("🌀 Пучок плоскостей")
        self.tab_kr = self.tabview.add(KR_TAB_NAME)
        self.tab_3d = self.tabview.add("🔮 3D Визуализатор")
        self.tab_handbook = self.tabview.add("📖 Справочник Главы 4")

        # Встраиваем 3D панель с кнопкой возврата назад
        self.viz_panel = Visualizer3DPanel(
            self.tab_3d, bg_dark=True,
            on_back=self.return_to_last_tab,
            on_navigate=self.navigate_to_tab
        )
        self.viz_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Инициализируем содержимое каждой вкладки
        self._setup_plane_tab()
        self._setup_line_tab()
        self._setup_relations_tab()
        self._setup_distances_tab()
        self._setup_pencil_tab()
        self.kr_tab = KRBlock2Tab(self, self.tab_kr, RichSolutionBox)
        self._setup_handbook_tab()

        # Статус-бар внизу
        self.status_bar = ctk.CTkLabel(
            self, text="Готово к вычислениям. Выберите раздел и введите данные.",
            anchor="w", font=("Segoe UI", 11), text_color="#94A3B8"
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=(0, 5))

    def _build_header(self):
        """Верхний заголовок с переключателем темы и описанием."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill=tk.X, padx=16, pady=(10, 4))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="📐 Калькулятор аналитической геометрии в пространстве",
            font=("Segoe UI", 18, "bold")
        )
        title_lbl.pack(side=tk.LEFT)

        theme_btn = ctk.CTkSegmentedButton(
            header_frame, values=["Dark", "Light"],
            command=self._change_theme, width=130
        )
        theme_btn.set("Dark")
        theme_btn.pack(side=tk.RIGHT)

        theme_lbl = ctk.CTkLabel(header_frame, text="Тема: ", font=("Segoe UI", 12))
        theme_lbl.pack(side=tk.RIGHT, padx=4)

    def _change_theme(self, mode: str):
        ctk.set_appearance_mode(mode)
        self.is_dark = (mode == "Dark")
        self.viz_panel.bg_dark = self.is_dark
        self.viz_panel.redraw()
        for sbox in self.solution_boxes:
            sbox.set_theme(self.is_dark)
        self.kr_tab.redraw_theme()

    def _on_tab_changed(self):
        cur = self.tabview.get()
        if cur not in ("🔮 3D Визуализатор", "📖 Справочник Главы 4"):
            self.current_calc_tab = cur
            self.viz_panel.set_last_tab(cur)

    def return_to_last_tab(self, target_tab: str = None):
        """Возврат в меню ввода из 3D режима."""
        target = target_tab or self.current_calc_tab or "📐 Плоскость"
        self.tabview.set(target)
        self.set_status(f"✓ Возврат к расчетам: {target}")

    def navigate_to_tab(self, tab_name: str):
        """Быстрый переход к конкретному калькулятору."""
        self.tabview.set(tab_name)
        self.current_calc_tab = tab_name
        self.viz_panel.set_last_tab(tab_name)
        self.set_status(f"Переход в раздел: {tab_name}")

    def set_status(self, text: str, is_error: bool = False):
        self.status_bar.configure(
            text=text,
            text_color="#EF4444" if is_error else "#10B981"
        )

    def copy_to_clipboard(self, sbox: RichSolutionBox):
        """Копирование решения в буфер обмена."""
        text = sbox.raw_text or sbox.get("1.0", tk.END)
        self.clipboard_clear()
        self.clipboard_append(text)
        self.set_status("✓ Пошаговое решение скопировано в буфер обмена!")

    def show_in_3d(self):
        """Переключение на вкладку 3D визуализации с обновлением кнопки возврата."""
        self.viz_panel.set_last_tab(self.current_calc_tab)
        self.tabview.set("🔮 3D Визуализатор")
        self.set_status(f"Отображено в 3D. Нажмите кнопку '⬅ ВЕРНУТЬСЯ К ВВОДУ' для возврата к {self.current_calc_tab}")

    def _clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

    def _create_entry_row(self, parent, label_text: str, default_val: str = "0"):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill=tk.X, pady=3)
        lbl = ctk.CTkLabel(row, text=label_text, width=160, anchor="w", font=("Segoe UI", 12))
        lbl.pack(side=tk.LEFT)
        ent = ctk.CTkEntry(row, width=180, font=("Segoe UI", 12))
        ent.insert(0, default_val)
        ent.pack(side=tk.LEFT, fill=tk.X, expand=True)
        return ent

    # =========================================================================
    # 1. ВКЛАДКА: ПЛОСКОСТЬ
    # =========================================================================
    def _setup_plane_tab(self):
        tab = self.tab_plane

        top_bar = ctk.CTkFrame(tab, fg_color="transparent")
        top_bar.pack(fill=tk.X, padx=10, pady=(6, 10))

        ctk.CTkLabel(top_bar, text="Способ построения плоскости:", font=("Segoe UI", 13, "bold")).pack(side=tk.LEFT, padx=(0, 10))

        self.plane_modes = [
            "1. По точке M₀ и нормальному вектору n",
            "2. Через 3 точки M₁, M₂, M₃",
            "3. В отрезках на осях (a, b, c)",
            "4. Через точку M₀ параллельно векторам u, v",
            "5. Через точку M₀ параллельно другой плоскости",
            "6. Через точку M₀ перпендикулярно 2 плоскостям",
            "7. Через прямую L и точку M₁ вне её",
            "8. Нормальное уравнение плоскости (μ, p, cos)"
        ]

        self.plane_mode_cb = ctk.CTkOptionMenu(
            top_bar, values=self.plane_modes, width=380,
            command=self._on_plane_mode_changed
        )
        self.plane_mode_cb.pack(side=tk.LEFT, padx=5)

        preset_btn = ctk.CTkButton(top_bar, text="📋 Пример задачи", width=130, command=self._load_plane_preset)
        preset_btn.pack(side=tk.RIGHT, padx=5)

        panes = ctk.CTkFrame(tab, fg_color="transparent")
        panes.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        self.plane_input_frame = ctk.CTkScrollableFrame(panes, width=420, label_text="Входные параметры")
        self.plane_input_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 8), pady=2)

        sol_frame = ctk.CTkFrame(panes)
        sol_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=2)

        sol_header = ctk.CTkFrame(sol_frame, fg_color="transparent")
        sol_header.pack(fill=tk.X, padx=8, pady=6)

        ctk.CTkLabel(sol_header, text="📝 Пошаговое аналитическое решение", font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT)

        self.plane_btn_3d = ctk.CTkButton(
            sol_header, text="🔮 Показать в 3D", width=120, fg_color="#3B82F6",
            command=self.show_in_3d, state="disabled"
        )
        self.plane_btn_3d.pack(side=tk.RIGHT, padx=5)

        self.plane_btn_copy = ctk.CTkButton(
            sol_header, text="📄 Копировать", width=110,
            command=lambda: self.copy_to_clipboard(self.plane_sol_box),
            state="disabled"
        )
        self.plane_btn_copy.pack(side=tk.RIGHT, padx=5)

        self.plane_sol_box = RichSolutionBox(sol_frame)
        self.plane_sol_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.solution_boxes.append(self.plane_sol_box)

        self._on_plane_mode_changed(self.plane_modes[0])

    def _on_plane_mode_changed(self, mode: str):
        self._clear_frame(self.plane_input_frame)
        self.plane_inputs = {}

        if "1. По точке M₀ и нормальному вектору" in mode:
            ctk.CTkLabel(self.plane_input_frame, text="Координаты точки M₀:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4, 2))
            self.plane_inputs['x0'] = self._create_entry_row(self.plane_input_frame, "x₀:", "1")
            self.plane_inputs['y0'] = self._create_entry_row(self.plane_input_frame, "y₀:", "-2")
            self.plane_inputs['z0'] = self._create_entry_row(self.plane_input_frame, "z₀:", "3")

            ctk.CTkLabel(self.plane_input_frame, text="Координаты нормального вектора n⃗:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(10, 2))
            self.plane_inputs['A'] = self._create_entry_row(self.plane_input_frame, "A:", "2")
            self.plane_inputs['B'] = self._create_entry_row(self.plane_input_frame, "B:", "-1")
            self.plane_inputs['C'] = self._create_entry_row(self.plane_input_frame, "C:", "4")

        elif "2. Через 3 точки" in mode:
            ctk.CTkLabel(self.plane_input_frame, text="Точка M₁ (x₁, y₁, z₁):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4, 2))
            self.plane_inputs['x1'] = self._create_entry_row(self.plane_input_frame, "x₁:", "1")
            self.plane_inputs['y1'] = self._create_entry_row(self.plane_input_frame, "y₁:", "2")
            self.plane_inputs['z1'] = self._create_entry_row(self.plane_input_frame, "z₁:", "0")

            ctk.CTkLabel(self.plane_input_frame, text="Точка M₂ (x₂, y₂, z₂):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(8, 2))
            self.plane_inputs['x2'] = self._create_entry_row(self.plane_input_frame, "x₂:", "2")
            self.plane_inputs['y2'] = self._create_entry_row(self.plane_input_frame, "y₂:", "1")
            self.plane_inputs['z2'] = self._create_entry_row(self.plane_input_frame, "z₂:", "1")

            ctk.CTkLabel(self.plane_input_frame, text="Точка M₃ (x₃, y₃, z₃):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(8, 2))
            self.plane_inputs['x3'] = self._create_entry_row(self.plane_input_frame, "x₃:", "0")
            self.plane_inputs['y3'] = self._create_entry_row(self.plane_input_frame, "y₃:", "3")
            self.plane_inputs['z3'] = self._create_entry_row(self.plane_input_frame, "z₃:", "2")

        elif "3. В отрезках на осях" in mode:
            ctk.CTkLabel(self.plane_input_frame, text="Отрезки на координатных осях:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4, 2))
            self.plane_inputs['a'] = self._create_entry_row(self.plane_input_frame, "a (по оси Ox):", "2")
            self.plane_inputs['b'] = self._create_entry_row(self.plane_input_frame, "b (по оси Oy):", "-3")
            self.plane_inputs['c'] = self._create_entry_row(self.plane_input_frame, "c (по оси Oz):", "4")

        elif "4. Через точку M₀ параллельно векторам" in mode:
            ctk.CTkLabel(self.plane_input_frame, text="Точка M₀:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4, 2))
            self.plane_inputs['x0'] = self._create_entry_row(self.plane_input_frame, "x₀:", "2")
            self.plane_inputs['y0'] = self._create_entry_row(self.plane_input_frame, "y₀:", "-1")
            self.plane_inputs['z0'] = self._create_entry_row(self.plane_input_frame, "z₀:", "1")

            ctk.CTkLabel(self.plane_input_frame, text="Вектор u⃗ = (u₁, u₂, u₃):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(8, 2))
            self.plane_inputs['u1'] = self._create_entry_row(self.plane_input_frame, "u₁:", "1")
            self.plane_inputs['u2'] = self._create_entry_row(self.plane_input_frame, "u₂:", "2")
            self.plane_inputs['u3'] = self._create_entry_row(self.plane_input_frame, "u₃:", "-1")

            ctk.CTkLabel(self.plane_input_frame, text="Вектор v⃗ = (v₁, v₂, v₃):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(8, 2))
            self.plane_inputs['v1'] = self._create_entry_row(self.plane_input_frame, "v₁:", "-2")
            self.plane_inputs['v2'] = self._create_entry_row(self.plane_input_frame, "v₂:", "0")
            self.plane_inputs['v3'] = self._create_entry_row(self.plane_input_frame, "v₃:", "3")

        elif "5. Через точку M₀ параллельно другой плоскости" in mode:
            ctk.CTkLabel(self.plane_input_frame, text="Точка M₀:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4, 2))
            self.plane_inputs['x0'] = self._create_entry_row(self.plane_input_frame, "x₀:", "3")
            self.plane_inputs['y0'] = self._create_entry_row(self.plane_input_frame, "y₀:", "4")
            self.plane_inputs['z0'] = self._create_entry_row(self.plane_input_frame, "z₀:", "-2")

            ctk.CTkLabel(self.plane_input_frame, text="Исходная плоскость A₁x + B₁y + C₁z + D₁ = 0:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(8, 2))
            self.plane_inputs['A1'] = self._create_entry_row(self.plane_input_frame, "A₁:", "3")
            self.plane_inputs['B1'] = self._create_entry_row(self.plane_input_frame, "B₁:", "-2")
            self.plane_inputs['C1'] = self._create_entry_row(self.plane_input_frame, "C₁:", "5")
            self.plane_inputs['D1'] = self._create_entry_row(self.plane_input_frame, "D₁:", "-14")

        elif "6. Через точку M₀ перпендикулярно 2 плоскостям" in mode:
            ctk.CTkLabel(self.plane_input_frame, text="Точка M₀:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4, 2))
            self.plane_inputs['x0'] = self._create_entry_row(self.plane_input_frame, "x₀:", "1")
            self.plane_inputs['y0'] = self._create_entry_row(self.plane_input_frame, "y₀:", "-1")
            self.plane_inputs['z0'] = self._create_entry_row(self.plane_input_frame, "z₀:", "2")

            ctk.CTkLabel(self.plane_input_frame, text="Плоскость P₁ (A₁x + B₁y + C₁z + D₁ = 0):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(8, 2))
            self.plane_inputs['A1'] = self._create_entry_row(self.plane_input_frame, "A₁:", "2")
            self.plane_inputs['B1'] = self._create_entry_row(self.plane_input_frame, "B₁:", "-3")
            self.plane_inputs['C1'] = self._create_entry_row(self.plane_input_frame, "C₁:", "1")
            self.plane_inputs['D1'] = self._create_entry_row(self.plane_input_frame, "D₁:", "5")

            ctk.CTkLabel(self.plane_input_frame, text="Плоскость P₂ (A₂x + B₂y + C₂z + D₂ = 0):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(8, 2))
            self.plane_inputs['A2'] = self._create_entry_row(self.plane_input_frame, "A₂:", "1")
            self.plane_inputs['B2'] = self._create_entry_row(self.plane_input_frame, "B₂:", "4")
            self.plane_inputs['C2'] = self._create_entry_row(self.plane_input_frame, "C₂:", "-2")
            self.plane_inputs['D2'] = self._create_entry_row(self.plane_input_frame, "D₂:", "-1")

        elif "7. Через прямую L и точку" in mode:
            ctk.CTkLabel(self.plane_input_frame, text="Точка на прямой M_L:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4, 2))
            self.plane_inputs['lx0'] = self._create_entry_row(self.plane_input_frame, "x_L:", "1")
            self.plane_inputs['ly0'] = self._create_entry_row(self.plane_input_frame, "y_L:", "0")
            self.plane_inputs['lz0'] = self._create_entry_row(self.plane_input_frame, "z_L:", "-1")

            ctk.CTkLabel(self.plane_input_frame, text="Направляющий вектор прямой s⃗ = (m, p, q):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(8, 2))
            self.plane_inputs['lm'] = self._create_entry_row(self.plane_input_frame, "m:", "2")
            self.plane_inputs['lp'] = self._create_entry_row(self.plane_input_frame, "p:", "-1")
            self.plane_inputs['lq'] = self._create_entry_row(self.plane_input_frame, "q:", "3")

            ctk.CTkLabel(self.plane_input_frame, text="Точка вне прямой M₁:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(8, 2))
            self.plane_inputs['x1'] = self._create_entry_row(self.plane_input_frame, "x₁:", "3")
            self.plane_inputs['y1'] = self._create_entry_row(self.plane_input_frame, "y₁:", "2")
            self.plane_inputs['z1'] = self._create_entry_row(self.plane_input_frame, "z₁:", "1")

        elif "8. Нормальное уравнение" in mode:
            ctk.CTkLabel(self.plane_input_frame, text="Коэффициенты плоскости Ax + By + Cz + D = 0:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4, 2))
            self.plane_inputs['A'] = self._create_entry_row(self.plane_input_frame, "A:", "2")
            self.plane_inputs['B'] = self._create_entry_row(self.plane_input_frame, "B:", "-2")
            self.plane_inputs['C'] = self._create_entry_row(self.plane_input_frame, "C:", "1")
            self.plane_inputs['D'] = self._create_entry_row(self.plane_input_frame, "D:", "-12")

        btn_calc = ctk.CTkButton(
            self.plane_input_frame, text="⚡ Рассчитать уравнение",
            font=("Segoe UI", 13, "bold"), height=36,
            fg_color="#10B981", hover_color="#059669",
            command=self._calc_plane
        )
        btn_calc.pack(fill=tk.X, pady=(15, 6))

    def _load_plane_preset(self):
        mode = self.plane_mode_cb.get()
        if "1." in mode:
            self.plane_inputs['x0'].delete(0, tk.END); self.plane_inputs['x0'].insert(0, "2")
            self.plane_inputs['y0'].delete(0, tk.END); self.plane_inputs['y0'].insert(0, "-1")
            self.plane_inputs['z0'].delete(0, tk.END); self.plane_inputs['z0'].insert(0, "5")
            self.plane_inputs['A'].delete(0, tk.END); self.plane_inputs['A'].insert(0, "3")
            self.plane_inputs['B'].delete(0, tk.END); self.plane_inputs['B'].insert(0, "4")
            self.plane_inputs['C'].delete(0, tk.END); self.plane_inputs['C'].insert(0, "-1")
        elif "2." in mode:
            self.plane_inputs['x1'].delete(0, tk.END); self.plane_inputs['x1'].insert(0, "1")
            self.plane_inputs['y1'].delete(0, tk.END); self.plane_inputs['y1'].insert(0, "2")
            self.plane_inputs['z1'].delete(0, tk.END); self.plane_inputs['z1'].insert(0, "-1")
            self.plane_inputs['x2'].delete(0, tk.END); self.plane_inputs['x2'].insert(0, "0")
            self.plane_inputs['y2'].delete(0, tk.END); self.plane_inputs['y2'].insert(0, "1")
            self.plane_inputs['z2'].delete(0, tk.END); self.plane_inputs['z2'].insert(0, "2")
            self.plane_inputs['x3'].delete(0, tk.END); self.plane_inputs['x3'].insert(0, "-2")
            self.plane_inputs['y3'].delete(0, tk.END); self.plane_inputs['y3'].insert(0, "3")
            self.plane_inputs['z3'].delete(0, tk.END); self.plane_inputs['z3'].insert(0, "0")
        self._calc_plane()

    def _calc_plane(self):
        try:
            self.current_calc_tab = "📐 Плоскость"
            mode = self.plane_mode_cb.get()
            res = None

            if "1. По точке M₀ и нормальному вектору" in mode:
                res = PlaneSolver.by_point_and_normal(
                    self.plane_inputs['x0'].get(), self.plane_inputs['y0'].get(), self.plane_inputs['z0'].get(),
                    self.plane_inputs['A'].get(), self.plane_inputs['B'].get(), self.plane_inputs['C'].get()
                )
                self.viz_panel.clear_objects()
                self.viz_panel.add_plane(res['A'], res['B'], res['C'], res['D'], "Плоскость P")
                pt = [float(c) for c in res['point']]
                n = [float(c) for c in res['normal']]
                self.viz_panel.add_point(pt[0], pt[1], pt[2], "M₀")
                self.viz_panel.add_vector(pt[0], pt[1], pt[2], n[0], n[1], n[2], "n⃗", color="#EF4444")
                self.viz_panel.redraw()

            elif "2. Через 3 точки" in mode:
                p1 = (self.plane_inputs['x1'].get(), self.plane_inputs['y1'].get(), self.plane_inputs['z1'].get())
                p2 = (self.plane_inputs['x2'].get(), self.plane_inputs['y2'].get(), self.plane_inputs['z2'].get())
                p3 = (self.plane_inputs['x3'].get(), self.plane_inputs['y3'].get(), self.plane_inputs['z3'].get())
                res = PlaneSolver.by_three_points(p1, p2, p3)
                self.viz_panel.clear_objects()
                self.viz_panel.add_plane(res['A'], res['B'], res['C'], res['D'], "Плоскость P")
                for i, p in enumerate(res['points'], 1):
                    pf = [float(c) for c in p]
                    self.viz_panel.add_point(pf[0], pf[1], pf[2], f"M{i}")
                self.viz_panel.redraw()

            elif "3. В отрезках на осях" in mode:
                res = PlaneSolver.in_intercepts(
                    self.plane_inputs['a'].get(), self.plane_inputs['b'].get(), self.plane_inputs['c'].get()
                )
                self.viz_panel.clear_objects()
                self.viz_panel.add_plane(res['A'], res['B'], res['C'], res['D'], "Плоскость P")
                a, b, c = [float(v) for v in res['intercepts']]
                self.viz_panel.add_point(a, 0, 0, f"A({a})")
                self.viz_panel.add_point(0, b, 0, f"B({b})")
                self.viz_panel.add_point(0, 0, c, f"C({c})")
                self.viz_panel.redraw()

            elif "4. Через точку M₀ параллельно векторам" in mode:
                p0 = (self.plane_inputs['x0'].get(), self.plane_inputs['y0'].get(), self.plane_inputs['z0'].get())
                vu = (self.plane_inputs['u1'].get(), self.plane_inputs['u2'].get(), self.plane_inputs['u3'].get())
                vv = (self.plane_inputs['v1'].get(), self.plane_inputs['v2'].get(), self.plane_inputs['v3'].get())
                res = PlaneSolver.by_point_and_two_vectors(p0, vu, vv)
                self.viz_panel.clear_objects()
                self.viz_panel.add_plane(res['A'], res['B'], res['C'], res['D'], "Плоскость P")
                p0f = [float(c) for c in res['point']]
                self.viz_panel.add_point(p0f[0], p0f[1], p0f[2], "M₀")
                uf = [float(c) for c in vu]
                vf = [float(c) for c in vv]
                self.viz_panel.add_vector(p0f[0], p0f[1], p0f[2], uf[0], uf[1], uf[2], "u⃗", color="#10B981")
                self.viz_panel.add_vector(p0f[0], p0f[1], p0f[2], vf[0], vf[1], vf[2], "v⃗", color="#F59E0B")
                self.viz_panel.redraw()

            elif "5. Через точку M₀ параллельно другой плоскости" in mode:
                p0 = (self.plane_inputs['x0'].get(), self.plane_inputs['y0'].get(), self.plane_inputs['z0'].get())
                res = PlaneSolver.by_point_parallel_to_plane(
                    p0, self.plane_inputs['A1'].get(), self.plane_inputs['B1'].get(),
                    self.plane_inputs['C1'].get(), self.plane_inputs['D1'].get()
                )
                self.viz_panel.clear_objects()
                self.viz_panel.add_plane(
                    float(self.plane_inputs['A1'].get()), float(self.plane_inputs['B1'].get()),
                    float(self.plane_inputs['C1'].get()), float(self.plane_inputs['D1'].get()),
                    "P₁ (исходная)", color="#64748B"
                )
                self.viz_panel.add_plane(res['A'], res['B'], res['C'], res['D'], "P₂ (параллельная)", color="#3B82F6")
                p0f = [float(c) for c in res['point']]
                self.viz_panel.add_point(p0f[0], p0f[1], p0f[2], "M₀")
                self.viz_panel.redraw()

            elif "6. Через точку M₀ перпендикулярно 2 плоскостям" in mode:
                p0 = (self.plane_inputs['x0'].get(), self.plane_inputs['y0'].get(), self.plane_inputs['z0'].get())
                pl1 = (self.plane_inputs['A1'].get(), self.plane_inputs['B1'].get(), self.plane_inputs['C1'].get(), self.plane_inputs['D1'].get())
                pl2 = (self.plane_inputs['A2'].get(), self.plane_inputs['B2'].get(), self.plane_inputs['C2'].get(), self.plane_inputs['D2'].get())
                res = PlaneSolver.by_point_perp_two_planes(p0, pl1, pl2)
                self.viz_panel.clear_objects()
                self.viz_panel.add_plane(float(pl1[0]), float(pl1[1]), float(pl1[2]), float(pl1[3]), "P₁", color="#64748B")
                self.viz_panel.add_plane(float(pl2[0]), float(pl2[1]), float(pl2[2]), float(pl2[3]), "P₂", color="#F59E0B")
                self.viz_panel.add_plane(res['A'], res['B'], res['C'], res['D'], "P (искомая)", color="#EF4444")
                p0f = [float(c) for c in res['point']]
                self.viz_panel.add_point(p0f[0], p0f[1], p0f[2], "M₀")
                self.viz_panel.redraw()

            elif "7. Через прямую L и точку" in mode:
                line_m0 = (self.plane_inputs['lx0'].get(), self.plane_inputs['ly0'].get(), self.plane_inputs['lz0'].get())
                line_s = (self.plane_inputs['lm'].get(), self.plane_inputs['lp'].get(), self.plane_inputs['lq'].get())
                p_ext = (self.plane_inputs['x1'].get(), self.plane_inputs['y1'].get(), self.plane_inputs['z1'].get())
                res = PlaneSolver.by_line_and_point(line_m0, line_s, p_ext)
                self.viz_panel.clear_objects()
                self.viz_panel.add_plane(res['A'], res['B'], res['C'], res['D'], "Плоскость P")
                lm = [float(c) for c in line_m0]
                ls = [float(c) for c in line_s]
                pe = [float(c) for c in p_ext]
                self.viz_panel.add_line(lm[0], lm[1], lm[2], ls[0], ls[1], ls[2], "Прямая L", color="#10B981")
                self.viz_panel.add_point(pe[0], pe[1], pe[2], "M₁")
                self.viz_panel.redraw()

            elif "8. Нормальное уравнение" in mode:
                res = PlaneSolver.normal_form(
                    self.plane_inputs['A'].get(), self.plane_inputs['B'].get(),
                    self.plane_inputs['C'].get(), self.plane_inputs['D'].get()
                )
                self.viz_panel.clear_objects()
                self.viz_panel.add_plane(
                    float(self.plane_inputs['A'].get()), float(self.plane_inputs['B'].get()),
                    float(self.plane_inputs['C'].get()), float(self.plane_inputs['D'].get()), "Плоскость"
                )
                self.viz_panel.redraw()

            self.plane_sol_box.set_solution(res['steps'])
            self.plane_btn_3d.configure(state="normal")
            self.plane_btn_copy.configure(state="normal")
            self.set_status("✓ Уравнение плоскости рассчитано! Для просмотра нажмите 'Показать в 3D'.")

        except Exception as ex:
            self.set_status(f"Ошибка вычисления: {str(ex)}", is_error=True)
            messagebox.showerror("Ошибка", f"Проверьте правильность введенных чисел:\n{str(ex)}")

    # =========================================================================
    # 2. ВКЛАДКА: ПРЯМАЯ В ПРОСТРАНСТВЕ
    # =========================================================================
    def _setup_line_tab(self):
        tab = self.tab_line

        top_bar = ctk.CTkFrame(tab, fg_color="transparent")
        top_bar.pack(fill=tk.X, padx=10, pady=(6, 10))

        ctk.CTkLabel(top_bar, text="Способ задания прямой:", font=("Segoe UI", 13, "bold")).pack(side=tk.LEFT, padx=(0, 10))

        self.line_modes = [
            "1. По точке M₀ и направляющему вектору s",
            "2. Через две точки M₁ и M₂",
            "3. Из общих уравнений (пересечение двух плоскостей)"
        ]

        self.line_mode_cb = ctk.CTkOptionMenu(
            top_bar, values=self.line_modes, width=380,
            command=self._on_line_mode_changed
        )
        self.line_mode_cb.pack(side=tk.LEFT, padx=5)

        preset_btn = ctk.CTkButton(top_bar, text="📋 Пример задачи", width=130, command=self._load_line_preset)
        preset_btn.pack(side=tk.RIGHT, padx=5)

        panes = ctk.CTkFrame(tab, fg_color="transparent")
        panes.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        self.line_input_frame = ctk.CTkScrollableFrame(panes, width=420, label_text="Входные параметры")
        self.line_input_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 8), pady=2)

        sol_frame = ctk.CTkFrame(panes)
        sol_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=2)

        sol_header = ctk.CTkFrame(sol_frame, fg_color="transparent")
        sol_header.pack(fill=tk.X, padx=8, pady=6)

        ctk.CTkLabel(sol_header, text="📝 Канонические и параметрические уравнения", font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT)

        self.line_btn_3d = ctk.CTkButton(sol_header, text="🔮 Показать в 3D", width=120, fg_color="#3B82F6", command=self.show_in_3d, state="disabled")
        self.line_btn_3d.pack(side=tk.RIGHT, padx=5)

        self.line_btn_copy = ctk.CTkButton(
            sol_header, text="📄 Копировать", width=110,
            command=lambda: self.copy_to_clipboard(self.line_sol_box),
            state="disabled"
        )
        self.line_btn_copy.pack(side=tk.RIGHT, padx=5)

        self.line_sol_box = RichSolutionBox(sol_frame)
        self.line_sol_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.solution_boxes.append(self.line_sol_box)

        self._on_line_mode_changed(self.line_modes[0])

    def _on_line_mode_changed(self, mode: str):
        self._clear_frame(self.line_input_frame)
        self.line_inputs = {}

        if "1. По точке M₀" in mode:
            ctk.CTkLabel(self.line_input_frame, text="Точка M₀ (x₀, y₀, z₀):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4, 2))
            self.line_inputs['x0'] = self._create_entry_row(self.line_input_frame, "x₀:", "2")
            self.line_inputs['y0'] = self._create_entry_row(self.line_input_frame, "y₀:", "-3")
            self.line_inputs['z0'] = self._create_entry_row(self.line_input_frame, "z₀:", "1")

            ctk.CTkLabel(self.line_input_frame, text="Направляющий вектор s⃗ = (m, p, q):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(10, 2))
            self.line_inputs['m'] = self._create_entry_row(self.line_input_frame, "m:", "3")
            self.line_inputs['p'] = self._create_entry_row(self.line_input_frame, "p:", "4")
            self.line_inputs['q'] = self._create_entry_row(self.line_input_frame, "q:", "-2")

        elif "2. Через две точки" in mode:
            ctk.CTkLabel(self.line_input_frame, text="Точка M₁ (x₁, y₁, z₁):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4, 2))
            self.line_inputs['x1'] = self._create_entry_row(self.line_input_frame, "x₁:", "1")
            self.line_inputs['y1'] = self._create_entry_row(self.line_input_frame, "y₁:", "-2")
            self.line_inputs['z1'] = self._create_entry_row(self.line_input_frame, "z₁:", "4")

            ctk.CTkLabel(self.line_input_frame, text="Точка M₂ (x₂, y₂, z₂):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(8, 2))
            self.line_inputs['x2'] = self._create_entry_row(self.line_input_frame, "x₂:", "3")
            self.line_inputs['y2'] = self._create_entry_row(self.line_input_frame, "y₂:", "1")
            self.line_inputs['z2'] = self._create_entry_row(self.line_input_frame, "z₂:", "2")

        elif "3. Из общих уравнений" in mode:
            ctk.CTkLabel(self.line_input_frame, text="Плоскость P₁ (A₁x + B₁y + C₁z + D₁ = 0):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4, 2))
            self.line_inputs['A1'] = self._create_entry_row(self.line_input_frame, "A₁:", "2")
            self.line_inputs['B1'] = self._create_entry_row(self.line_input_frame, "B₁:", "-1")
            self.line_inputs['C1'] = self._create_entry_row(self.line_input_frame, "C₁:", "3")
            self.line_inputs['D1'] = self._create_entry_row(self.line_input_frame, "D₁:", "-4")

            ctk.CTkLabel(self.line_input_frame, text="Плоскость P₂ (A₂x + B₂y + C₂z + D₂ = 0):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(8, 2))
            self.line_inputs['A2'] = self._create_entry_row(self.line_input_frame, "A₂:", "1")
            self.line_inputs['B2'] = self._create_entry_row(self.line_input_frame, "B₂:", "2")
            self.line_inputs['C2'] = self._create_entry_row(self.line_input_frame, "C₂:", "-1")
            self.line_inputs['D2'] = self._create_entry_row(self.line_input_frame, "D₂:", "3")

        btn_calc = ctk.CTkButton(
            self.line_input_frame, text="⚡ Найти уравнения прямой",
            font=("Segoe UI", 13, "bold"), height=36,
            fg_color="#10B981", hover_color="#059669",
            command=self._calc_line
        )
        btn_calc.pack(fill=tk.X, pady=(15, 6))

    def _load_line_preset(self):
        mode = self.line_mode_cb.get()
        if "1." in mode:
            self.line_inputs['x0'].delete(0, tk.END); self.line_inputs['x0'].insert(0, "-1")
            self.line_inputs['y0'].delete(0, tk.END); self.line_inputs['y0'].insert(0, "4")
            self.line_inputs['z0'].delete(0, tk.END); self.line_inputs['z0'].insert(0, "2")
            self.line_inputs['m'].delete(0, tk.END); self.line_inputs['m'].insert(0, "2")
            self.line_inputs['p'].delete(0, tk.END); self.line_inputs['p'].insert(0, "-3")
            self.line_inputs['q'].delete(0, tk.END); self.line_inputs['q'].insert(0, "5")
        self._calc_line()

    def _calc_line(self):
        try:
            self.current_calc_tab = "📏 Прямая"
            mode = self.line_mode_cb.get()
            res = None

            if "1. По точке M₀" in mode:
                res = LineSolver.by_point_and_vector(
                    self.line_inputs['x0'].get(), self.line_inputs['y0'].get(), self.line_inputs['z0'].get(),
                    self.line_inputs['m'].get(), self.line_inputs['p'].get(), self.line_inputs['q'].get()
                )
                self.viz_panel.clear_objects()
                m0 = [float(c) for c in res['M0']]
                s = [float(c) for c in res['s']]
                self.viz_panel.add_line(m0[0], m0[1], m0[2], s[0], s[1], s[2], "Прямая L")
                self.viz_panel.add_point(m0[0], m0[1], m0[2], "M₀")
                self.viz_panel.add_vector(m0[0], m0[1], m0[2], s[0], s[1], s[2], "s⃗", color="#10B981")
                self.viz_panel.redraw()

            elif "2. Через две точки" in mode:
                p1 = (self.line_inputs['x1'].get(), self.line_inputs['y1'].get(), self.line_inputs['z1'].get())
                p2 = (self.line_inputs['x2'].get(), self.line_inputs['y2'].get(), self.line_inputs['z2'].get())
                res = LineSolver.by_two_points(p1, p2)
                self.viz_panel.clear_objects()
                p1f = [float(c) for c in p1]
                p2f = [float(c) for c in p2]
                s = [float(c) for c in res['s']]
                self.viz_panel.add_line(p1f[0], p1f[1], p1f[2], s[0], s[1], s[2], "Прямая L")
                self.viz_panel.add_point(p1f[0], p1f[1], p1f[2], "M₁")
                self.viz_panel.add_point(p2f[0], p2f[1], p2f[2], "M₂")
                self.viz_panel.redraw()

            elif "3. Из общих уравнений" in mode:
                pl1 = (self.line_inputs['A1'].get(), self.line_inputs['B1'].get(), self.line_inputs['C1'].get(), self.line_inputs['D1'].get())
                pl2 = (self.line_inputs['A2'].get(), self.line_inputs['B2'].get(), self.line_inputs['C2'].get(), self.line_inputs['D2'].get())
                res = LineSolver.from_general_to_canonical(pl1, pl2)
                self.viz_panel.clear_objects()
                self.viz_panel.add_plane(float(pl1[0]), float(pl1[1]), float(pl1[2]), float(pl1[3]), "P₁", color="#64748B")
                self.viz_panel.add_plane(float(pl2[0]), float(pl2[1]), float(pl2[2]), float(pl2[3]), "P₂", color="#F59E0B")
                m0 = [float(c) for c in res['M0']]
                s = [float(c) for c in res['s']]
                self.viz_panel.add_line(m0[0], m0[1], m0[2], s[0], s[1], s[2], "Прямая пересечения", color="#10B981")
                self.viz_panel.redraw()

            self.line_sol_box.set_solution(res['steps'])
            self.line_btn_3d.configure(state="normal")
            self.line_btn_copy.configure(state="normal")
            self.set_status("✓ Уравнения прямой успешно найдены!")

        except Exception as ex:
            self.set_status(f"Ошибка вычисления: {str(ex)}", is_error=True)
            messagebox.showerror("Ошибка", f"Проверьте правильность введенных чисел:\n{str(ex)}")

    # =========================================================================
    # 3. ВКЛАДКА: ВЗАИМНОЕ РАСПОЛОЖЕНИЕ
    # =========================================================================
    def _setup_relations_tab(self):
        tab = self.tab_relations

        top_bar = ctk.CTkFrame(tab, fg_color="transparent")
        top_bar.pack(fill=tk.X, padx=10, pady=(6, 10))

        ctk.CTkLabel(top_bar, text="Исследуемые объекты:", font=("Segoe UI", 13, "bold")).pack(side=tk.LEFT, padx=(0, 10))

        self.rel_modes = [
            "1. Две плоскости (угол, пересечение, параллельность)",
            "2. Прямая и плоскость (угол, точка пересечения)",
            "3. Две прямые (скрещивание, пересечение, угол)"
        ]

        self.rel_mode_cb = ctk.CTkOptionMenu(
            top_bar, values=self.rel_modes, width=420,
            command=self._on_rel_mode_changed
        )
        self.rel_mode_cb.pack(side=tk.LEFT, padx=5)

        preset_btn = ctk.CTkButton(top_bar, text="📋 Пример задачи", width=130, command=self._load_rel_preset)
        preset_btn.pack(side=tk.RIGHT, padx=5)

        panes = ctk.CTkFrame(tab, fg_color="transparent")
        panes.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        self.rel_input_frame = ctk.CTkScrollableFrame(panes, width=420, label_text="Входные параметры")
        self.rel_input_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 8), pady=2)

        sol_frame = ctk.CTkFrame(panes)
        sol_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=2)

        sol_header = ctk.CTkFrame(sol_frame, fg_color="transparent")
        sol_header.pack(fill=tk.X, padx=8, pady=6)

        ctk.CTkLabel(sol_header, text="📝 Анализ взаимного расположения", font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT)

        self.rel_btn_3d = ctk.CTkButton(sol_header, text="🔮 Показать в 3D", width=120, fg_color="#3B82F6", command=self.show_in_3d, state="disabled")
        self.rel_btn_3d.pack(side=tk.RIGHT, padx=5)

        self.rel_btn_copy = ctk.CTkButton(
            sol_header, text="📄 Копировать", width=110,
            command=lambda: self.copy_to_clipboard(self.rel_sol_box),
            state="disabled"
        )
        self.rel_btn_copy.pack(side=tk.RIGHT, padx=5)

        self.rel_sol_box = RichSolutionBox(sol_frame)
        self.rel_sol_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.solution_boxes.append(self.rel_sol_box)

        self._on_rel_mode_changed(self.rel_modes[0])

    def _on_rel_mode_changed(self, mode: str):
        self._clear_frame(self.rel_input_frame)
        self.rel_inputs = {}

        if "1. Две плоскости" in mode:
            ctk.CTkLabel(self.rel_input_frame, text="Плоскость P₁ (A₁x + B₁y + C₁z + D₁ = 0):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4, 2))
            self.rel_inputs['A1'] = self._create_entry_row(self.rel_input_frame, "A₁:", "2")
            self.rel_inputs['B1'] = self._create_entry_row(self.rel_input_frame, "B₁:", "-1")
            self.rel_inputs['C1'] = self._create_entry_row(self.rel_input_frame, "C₁:", "3")
            self.rel_inputs['D1'] = self._create_entry_row(self.rel_input_frame, "D₁:", "-5")

            ctk.CTkLabel(self.rel_input_frame, text="Плоскость P₂ (A₂x + B₂y + C₂z + D₂ = 0):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(10, 2))
            self.rel_inputs['A2'] = self._create_entry_row(self.rel_input_frame, "A₂:", "1")
            self.rel_inputs['B2'] = self._create_entry_row(self.rel_input_frame, "B₂:", "4")
            self.rel_inputs['C2'] = self._create_entry_row(self.rel_input_frame, "C₂:", "-1")
            self.rel_inputs['D2'] = self._create_entry_row(self.rel_input_frame, "D₂:", "2")

        elif "2. Прямая и плоскость" in mode:
            ctk.CTkLabel(self.rel_input_frame, text="Прямая L: точка M₀(x₀, y₀, z₀):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4, 2))
            self.rel_inputs['lx0'] = self._create_entry_row(self.rel_input_frame, "x₀:", "1")
            self.rel_inputs['ly0'] = self._create_entry_row(self.rel_input_frame, "y₀:", "2")
            self.rel_inputs['lz0'] = self._create_entry_row(self.rel_input_frame, "z₀:", "3")

            ctk.CTkLabel(self.rel_input_frame, text="Вектор s⃗ = (m, p, q):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(8, 2))
            self.rel_inputs['lm'] = self._create_entry_row(self.rel_input_frame, "m:", "2")
            self.rel_inputs['lp'] = self._create_entry_row(self.rel_input_frame, "p:", "-1")
            self.rel_inputs['lq'] = self._create_entry_row(self.rel_input_frame, "q:", "1")

            ctk.CTkLabel(self.rel_input_frame, text="Плоскость P (Ax + By + Cz + D = 0):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(8, 2))
            self.rel_inputs['A'] = self._create_entry_row(self.rel_input_frame, "A:", "1")
            self.rel_inputs['B'] = self._create_entry_row(self.rel_input_frame, "B:", "1")
            self.rel_inputs['C'] = self._create_entry_row(self.rel_input_frame, "C:", "-1")
            self.rel_inputs['D'] = self._create_entry_row(self.rel_input_frame, "D:", "-5")

        elif "3. Две прямые" in mode:
            ctk.CTkLabel(self.rel_input_frame, text="Прямая L₁: M₁(x₁, y₁, z₁) и s⃗₁ = (m₁, p₁, q₁):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4, 2))
            self.rel_inputs['l1_x'] = self._create_entry_row(self.rel_input_frame, "x₁:", "1")
            self.rel_inputs['l1_y'] = self._create_entry_row(self.rel_input_frame, "y₁:", "0")
            self.rel_inputs['l1_z'] = self._create_entry_row(self.rel_input_frame, "z₁:", "-2")
            self.rel_inputs['l1_m'] = self._create_entry_row(self.rel_input_frame, "m₁:", "2")
            self.rel_inputs['l1_p'] = self._create_entry_row(self.rel_input_frame, "p₁:", "-1")
            self.rel_inputs['l1_q'] = self._create_entry_row(self.rel_input_frame, "q₁:", "4")

            ctk.CTkLabel(self.rel_input_frame, text="Прямая L₂: M₂(x₂, y₂, z₂) и s⃗₂ = (m₂, p₂, q₂):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(8, 2))
            self.rel_inputs['l2_x'] = self._create_entry_row(self.rel_input_frame, "x₂:", "3")
            self.rel_inputs['l2_y'] = self._create_entry_row(self.rel_input_frame, "y₂:", "-1")
            self.rel_inputs['l2_z'] = self._create_entry_row(self.rel_input_frame, "z₂:", "2")
            self.rel_inputs['l2_m'] = self._create_entry_row(self.rel_input_frame, "m₂:", "1")
            self.rel_inputs['l2_p'] = self._create_entry_row(self.rel_input_frame, "p₂:", "2")
            self.rel_inputs['l2_q'] = self._create_entry_row(self.rel_input_frame, "q₂:", "-3")

        btn_calc = ctk.CTkButton(
            self.rel_input_frame, text="⚡ Исследовать взаимное расположение",
            font=("Segoe UI", 13, "bold"), height=36,
            fg_color="#10B981", hover_color="#059669",
            command=self._calc_relations
        )
        btn_calc.pack(fill=tk.X, pady=(15, 6))

    def _load_rel_preset(self):
        self._calc_relations()

    def _calc_relations(self):
        try:
            self.current_calc_tab = "⚖️ Взаимное расположение"
            mode = self.rel_mode_cb.get()
            res = None

            if "1. Две плоскости" in mode:
                pl1 = (self.rel_inputs['A1'].get(), self.rel_inputs['B1'].get(), self.rel_inputs['C1'].get(), self.rel_inputs['D1'].get())
                pl2 = (self.rel_inputs['A2'].get(), self.rel_inputs['B2'].get(), self.rel_inputs['C2'].get(), self.rel_inputs['D2'].get())
                res = RelationsSolver.two_planes(pl1, pl2)
                self.viz_panel.clear_objects()
                self.viz_panel.add_plane(float(pl1[0]), float(pl1[1]), float(pl1[2]), float(pl1[3]), "P₁", color="#3B82F6")
                self.viz_panel.add_plane(float(pl2[0]), float(pl2[1]), float(pl2[2]), float(pl2[3]), "P₂", color="#F59E0B")
                if not res['is_parallel'] and 'intersection_line' in res:
                    m0 = [float(c) for c in res['intersection_line']['M0']]
                    s = [float(c) for c in res['intersection_line']['s']]
                    self.viz_panel.add_line(m0[0], m0[1], m0[2], s[0], s[1], s[2], "Линия пересечения", color="#10B981")
                self.viz_panel.redraw()

            elif "2. Прямая и плоскость" in mode:
                lm = (self.rel_inputs['lx0'].get(), self.rel_inputs['ly0'].get(), self.rel_inputs['lz0'].get())
                ls = (self.rel_inputs['lm'].get(), self.rel_inputs['lp'].get(), self.rel_inputs['lq'].get())
                pl = (self.rel_inputs['A'].get(), self.rel_inputs['B'].get(), self.rel_inputs['C'].get(), self.rel_inputs['D'].get())
                res = RelationsSolver.line_and_plane(lm, ls, pl)
                self.viz_panel.clear_objects()
                self.viz_panel.add_plane(float(pl[0]), float(pl[1]), float(pl[2]), float(pl[3]), "Плоскость P", color="#3B82F6")
                lmf = [float(c) for c in lm]
                lsf = [float(c) for c in ls]
                self.viz_panel.add_line(lmf[0], lmf[1], lmf[2], lsf[0], lsf[1], lsf[2], "Прямая L", color="#EF4444")
                if 'intersection_point' in res:
                    pi = [float(c) for c in res['intersection_point']]
                    self.viz_panel.add_point(pi[0], pi[1], pi[2], "Точка K (пересечение)", color="#10B981")
                self.viz_panel.redraw()

            elif "3. Две прямые" in mode:
                l1_m = (self.rel_inputs['l1_x'].get(), self.rel_inputs['l1_y'].get(), self.rel_inputs['l1_z'].get())
                l1_s = (self.rel_inputs['l1_m'].get(), self.rel_inputs['l1_p'].get(), self.rel_inputs['l1_q'].get())
                l2_m = (self.rel_inputs['l2_x'].get(), self.rel_inputs['l2_y'].get(), self.rel_inputs['l2_z'].get())
                l2_s = (self.rel_inputs['l2_m'].get(), self.rel_inputs['l2_p'].get(), self.rel_inputs['l2_q'].get())
                res = RelationsSolver.two_lines(l1_m, l1_s, l2_m, l2_s)
                self.viz_panel.clear_objects()
                p1 = [float(c) for c in l1_m]; s1 = [float(c) for c in l1_s]
                p2 = [float(c) for c in l2_m]; s2 = [float(c) for c in l2_s]
                self.viz_panel.add_line(p1[0], p1[1], p1[2], s1[0], s1[1], s1[2], "Прямая L₁", color="#3B82F6")
                self.viz_panel.add_line(p2[0], p2[1], p2[2], s2[0], s2[1], s2[2], "Прямая L₂", color="#EF4444")
                if res.get('is_intersecting') and 'intersection_point' in res:
                    pi = [float(c) for c in res['intersection_point']]
                    self.viz_panel.add_point(pi[0], pi[1], pi[2], "Точка пересечения", color="#10B981")
                self.viz_panel.redraw()

            self.rel_sol_box.set_solution(res['steps'])
            self.rel_btn_3d.configure(state="normal")
            self.rel_btn_copy.configure(state="normal")
            self.set_status(f"✓ Взаимное расположение: {res['status']}")

        except Exception as ex:
            self.set_status(f"Ошибка вычисления: {str(ex)}", is_error=True)
            messagebox.showerror("Ошибка", f"Проверьте правильность введенных чисел:\n{str(ex)}")

    # =========================================================================
    # 4. ВКЛАДКА: РАССТОЯНИЯ И ПРОЕКЦИИ
    # =========================================================================
    def _setup_distances_tab(self):
        tab = self.tab_distances

        top_bar = ctk.CTkFrame(tab, fg_color="transparent")
        top_bar.pack(fill=tk.X, padx=10, pady=(6, 10))

        ctk.CTkLabel(top_bar, text="Задача на расстояние и проекцию:", font=("Segoe UI", 13, "bold")).pack(side=tk.LEFT, padx=(0, 10))

        self.dist_modes = [
            "1. Расстояние от точки M₀ до плоскости (проекция H, симметрия M')",
            "2. Расстояние от точки M₀ до прямой (проекция H, симметрия M')",
            "3. Расстояние между параллельными плоскостями",
            "4. Расстояние между скрещивающимися прямыми"
        ]

        self.dist_mode_cb = ctk.CTkOptionMenu(
            top_bar, values=self.dist_modes, width=440,
            command=self._on_dist_mode_changed
        )
        self.dist_mode_cb.pack(side=tk.LEFT, padx=5)

        preset_btn = ctk.CTkButton(top_bar, text="📋 Пример задачи", width=130, command=self._load_dist_preset)
        preset_btn.pack(side=tk.RIGHT, padx=5)

        panes = ctk.CTkFrame(tab, fg_color="transparent")
        panes.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        self.dist_input_frame = ctk.CTkScrollableFrame(panes, width=420, label_text="Входные параметры")
        self.dist_input_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 8), pady=2)

        sol_frame = ctk.CTkFrame(panes)
        sol_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=2)

        sol_header = ctk.CTkFrame(sol_frame, fg_color="transparent")
        sol_header.pack(fill=tk.X, padx=8, pady=6)

        ctk.CTkLabel(sol_header, text="📝 Решение задачи о расстояниях", font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT)

        self.dist_btn_3d = ctk.CTkButton(sol_header, text="🔮 Показать в 3D", width=120, fg_color="#3B82F6", command=self.show_in_3d, state="disabled")
        self.dist_btn_3d.pack(side=tk.RIGHT, padx=5)

        self.dist_btn_copy = ctk.CTkButton(
            sol_header, text="📄 Копировать", width=110,
            command=lambda: self.copy_to_clipboard(self.dist_sol_box),
            state="disabled"
        )
        self.dist_btn_copy.pack(side=tk.RIGHT, padx=5)

        self.dist_sol_box = RichSolutionBox(sol_frame)
        self.dist_sol_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.solution_boxes.append(self.dist_sol_box)

        self._on_dist_mode_changed(self.dist_modes[0])

    def _on_dist_mode_changed(self, mode: str):
        self._clear_frame(self.dist_input_frame)
        self.dist_inputs = {}

        if "1. Расстояние от точки M₀ до плоскости" in mode:
            ctk.CTkLabel(self.dist_input_frame, text="Координаты точки M₀:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4, 2))
            self.dist_inputs['x0'] = self._create_entry_row(self.dist_input_frame, "x₀:", "1")
            self.dist_inputs['y0'] = self._create_entry_row(self.dist_input_frame, "y₀:", "2")
            self.dist_inputs['z0'] = self._create_entry_row(self.dist_input_frame, "z₀:", "3")

            ctk.CTkLabel(self.dist_input_frame, text="Плоскость Ax + By + Cz + D = 0:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(10, 2))
            self.dist_inputs['A'] = self._create_entry_row(self.dist_input_frame, "A:", "2")
            self.dist_inputs['B'] = self._create_entry_row(self.dist_input_frame, "B:", "-2")
            self.dist_inputs['C'] = self._create_entry_row(self.dist_input_frame, "C:", "1")
            self.dist_inputs['D'] = self._create_entry_row(self.dist_input_frame, "D:", "-5")

        elif "2. Расстояние от точки M₀ до прямой" in mode:
            ctk.CTkLabel(self.dist_input_frame, text="Координаты точки M₀:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4, 2))
            self.dist_inputs['x0'] = self._create_entry_row(self.dist_input_frame, "x₀:", "3")
            self.dist_inputs['y0'] = self._create_entry_row(self.dist_input_frame, "y₀:", "-1")
            self.dist_inputs['z0'] = self._create_entry_row(self.dist_input_frame, "z₀:", "2")

            ctk.CTkLabel(self.dist_input_frame, text="Прямая: точка M₁(x₁, y₁, z₁) и вектор s⃗(m, p, q):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(10, 2))
            self.dist_inputs['x1'] = self._create_entry_row(self.dist_input_frame, "x₁:", "1")
            self.dist_inputs['y1'] = self._create_entry_row(self.dist_input_frame, "y₁:", "2")
            self.dist_inputs['z1'] = self._create_entry_row(self.dist_input_frame, "z₁:", "-1")
            self.dist_inputs['m'] = self._create_entry_row(self.dist_input_frame, "m:", "2")
            self.dist_inputs['p'] = self._create_entry_row(self.dist_input_frame, "p:", "1")
            self.dist_inputs['q'] = self._create_entry_row(self.dist_input_frame, "q:", "-2")

        elif "3. Расстояние между параллельными плоскостями" in mode:
            ctk.CTkLabel(self.dist_input_frame, text="Плоскость P₁: A₁x + B₁y + C₁z + D₁ = 0", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4, 2))
            self.dist_inputs['A1'] = self._create_entry_row(self.dist_input_frame, "A₁:", "2")
            self.dist_inputs['B1'] = self._create_entry_row(self.dist_input_frame, "B₁:", "-1")
            self.dist_inputs['C1'] = self._create_entry_row(self.dist_input_frame, "C₁:", "2")
            self.dist_inputs['D1'] = self._create_entry_row(self.dist_input_frame, "D₁:", "-4")

            ctk.CTkLabel(self.dist_input_frame, text="Плоскость P₂: A₂x + B₂y + C₂z + D₂ = 0", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(10, 2))
            self.dist_inputs['A2'] = self._create_entry_row(self.dist_input_frame, "A₂:", "4")
            self.dist_inputs['B2'] = self._create_entry_row(self.dist_input_frame, "B₂:", "-2")
            self.dist_inputs['C2'] = self._create_entry_row(self.dist_input_frame, "C₂:", "4")
            self.dist_inputs['D2'] = self._create_entry_row(self.dist_input_frame, "D₂:", "10")

        elif "4. Расстояние между скрещивающимися прямыми" in mode:
            ctk.CTkLabel(self.dist_input_frame, text="Прямая L₁: M₁(x₁, y₁, z₁), s⃗₁(m₁, p₁, q₁)", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4, 2))
            self.dist_inputs['l1_x'] = self._create_entry_row(self.dist_input_frame, "x₁:", "1")
            self.dist_inputs['l1_y'] = self._create_entry_row(self.dist_input_frame, "y₁:", "-2")
            self.dist_inputs['l1_z'] = self._create_entry_row(self.dist_input_frame, "z₁:", "1")
            self.dist_inputs['l1_m'] = self._create_entry_row(self.dist_input_frame, "m₁:", "2")
            self.dist_inputs['l1_p'] = self._create_entry_row(self.dist_input_frame, "p₁:", "3")
            self.dist_inputs['l1_q'] = self._create_entry_row(self.dist_input_frame, "q₁:", "1")

            ctk.CTkLabel(self.dist_input_frame, text="Прямая L₂: M₂(x₂, y₂, z₂), s⃗₂(m₂, p₂, q₂)", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(10, 2))
            self.dist_inputs['l2_x'] = self._create_entry_row(self.dist_input_frame, "x₂:", "0")
            self.dist_inputs['l2_y'] = self._create_entry_row(self.dist_input_frame, "y₂:", "1")
            self.dist_inputs['l2_z'] = self._create_entry_row(self.dist_input_frame, "z₂:", "-3")
            self.dist_inputs['l2_m'] = self._create_entry_row(self.dist_input_frame, "m₂:", "1")
            self.dist_inputs['l2_p'] = self._create_entry_row(self.dist_input_frame, "p₂:", "-2")
            self.dist_inputs['l2_q'] = self._create_entry_row(self.dist_input_frame, "q₂:", "2")

        btn_calc = ctk.CTkButton(
            self.dist_input_frame, text="⚡ Вычислить расстояние и проекцию",
            font=("Segoe UI", 13, "bold"), height=36,
            fg_color="#10B981", hover_color="#059669",
            command=self._calc_distance
        )
        btn_calc.pack(fill=tk.X, pady=(15, 6))

    def _load_dist_preset(self):
        self._calc_distance()

    def _calc_distance(self):
        try:
            self.current_calc_tab = "🎯 Расстояния и проекции"
            mode = self.dist_mode_cb.get()
            res = None

            if "1. Расстояние от точки M₀ до плоскости" in mode:
                pt = (self.dist_inputs['x0'].get(), self.dist_inputs['y0'].get(), self.dist_inputs['z0'].get())
                pl = (self.dist_inputs['A'].get(), self.dist_inputs['B'].get(), self.dist_inputs['C'].get(), self.dist_inputs['D'].get())
                res = DistancesAndProjections.point_to_plane(pt, pl)

                self.viz_panel.clear_objects()
                self.viz_panel.add_plane(float(pl[0]), float(pl[1]), float(pl[2]), float(pl[3]), "Плоскость P", color="#3B82F6")
                p0 = [float(c) for c in pt]
                h = [float(c) for c in res['projection']]
                sym = [float(c) for c in res['symmetric']]

                self.viz_panel.add_point(p0[0], p0[1], p0[2], "M₀", color="#EF4444")
                self.viz_panel.add_point(h[0], h[1], h[2], "H (проекция)", color="#10B981")
                self.viz_panel.add_point(sym[0], sym[1], sym[2], "M' (симметрия)", color="#F59E0B")
                self.viz_panel.add_segment((p0[0], p0[1], p0[2]), (h[0], h[1], h[2]), "d", color="#EF4444")
                self.viz_panel.add_segment((h[0], h[1], h[2]), (sym[0], sym[1], sym[2]), "", color="#F59E0B")
                self.viz_panel.redraw()

            elif "2. Расстояние от точки M₀ до прямой" in mode:
                pt = (self.dist_inputs['x0'].get(), self.dist_inputs['y0'].get(), self.dist_inputs['z0'].get())
                line_m = (self.dist_inputs['x1'].get(), self.dist_inputs['y1'].get(), self.dist_inputs['z1'].get())
                line_s = (self.dist_inputs['m'].get(), self.dist_inputs['p'].get(), self.dist_inputs['q'].get())
                res = DistancesAndProjections.point_to_line(pt, line_m, line_s)

                self.viz_panel.clear_objects()
                p0 = [float(c) for c in pt]
                lm = [float(c) for c in line_m]
                ls = [float(c) for c in line_s]
                h = [float(c) for c in res['projection']]
                sym = [float(c) for c in res['symmetric']]

                self.viz_panel.add_line(lm[0], lm[1], lm[2], ls[0], ls[1], ls[2], "Прямая L", color="#3B82F6")
                self.viz_panel.add_point(p0[0], p0[1], p0[2], "M₀", color="#EF4444")
                self.viz_panel.add_point(h[0], h[1], h[2], "H (проекция)", color="#10B981")
                self.viz_panel.add_point(sym[0], sym[1], sym[2], "M' (симметрия)", color="#F59E0B")
                self.viz_panel.add_segment((p0[0], p0[1], p0[2]), (h[0], h[1], h[2]), "d", color="#EF4444")
                self.viz_panel.redraw()

            elif "3. Расстояние между параллельными плоскостями" in mode:
                pl1 = (self.dist_inputs['A1'].get(), self.dist_inputs['B1'].get(), self.dist_inputs['C1'].get(), self.dist_inputs['D1'].get())
                pl2 = (self.dist_inputs['A2'].get(), self.dist_inputs['B2'].get(), self.dist_inputs['C2'].get(), self.dist_inputs['D2'].get())
                res = RelationsSolver.two_planes(pl1, pl2)
                self.viz_panel.clear_objects()
                self.viz_panel.add_plane(float(pl1[0]), float(pl1[1]), float(pl1[2]), float(pl1[3]), "P₁", color="#3B82F6")
                self.viz_panel.add_plane(float(pl2[0]), float(pl2[1]), float(pl2[2]), float(pl2[3]), "P₂", color="#10B981")
                self.viz_panel.redraw()

            elif "4. Расстояние между скрещивающимися прямыми" in mode:
                l1_m = (self.dist_inputs['l1_x'].get(), self.dist_inputs['l1_y'].get(), self.dist_inputs['l1_z'].get())
                l1_s = (self.dist_inputs['l1_m'].get(), self.dist_inputs['l1_p'].get(), self.dist_inputs['l1_q'].get())
                l2_m = (self.dist_inputs['l2_x'].get(), self.dist_inputs['l2_y'].get(), self.dist_inputs['l2_z'].get())
                l2_s = (self.dist_inputs['l2_m'].get(), self.dist_inputs['l2_p'].get(), self.dist_inputs['l2_q'].get())
                res = RelationsSolver.two_lines(l1_m, l1_s, l2_m, l2_s)
                self.viz_panel.clear_objects()
                p1 = [float(c) for c in l1_m]; s1 = [float(c) for c in l1_s]
                p2 = [float(c) for c in l2_m]; s2 = [float(c) for c in l2_s]
                self.viz_panel.add_line(p1[0], p1[1], p1[2], s1[0], s1[1], s1[2], "L₁", color="#3B82F6")
                self.viz_panel.add_line(p2[0], p2[1], p2[2], s2[0], s2[1], s2[2], "L₂", color="#EF4444")
                self.viz_panel.redraw()

            self.dist_sol_box.set_solution(res['steps'])
            self.dist_btn_3d.configure(state="normal")
            self.dist_btn_copy.configure(state="normal")
            self.set_status("✓ Расстояние и проекции успешно рассчитаны!")

        except Exception as ex:
            self.set_status(f"Ошибка вычисления: {str(ex)}", is_error=True)
            messagebox.showerror("Ошибка", f"Проверьте правильность введенных чисел:\n{str(ex)}")

    # =========================================================================
    # 5. ВКЛАДКА: ПУЧОК ПЛОСКОСТЕЙ
    # =========================================================================
    def _setup_pencil_tab(self):
        tab = self.tab_pencil

        top_bar = ctk.CTkFrame(tab, fg_color="transparent")
        top_bar.pack(fill=tk.X, padx=10, pady=(6, 10))

        ctk.CTkLabel(top_bar, text="Задача: Плоскость из пучка α·P₁ + β·P₂ = 0, проходящая через точку M₀", font=("Segoe UI", 13, "bold")).pack(side=tk.LEFT)

        preset_btn = ctk.CTkButton(top_bar, text="📋 Пример задачи", width=130, command=self._load_pencil_preset)
        preset_btn.pack(side=tk.RIGHT, padx=5)

        panes = ctk.CTkFrame(tab, fg_color="transparent")
        panes.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        self.pencil_input_frame = ctk.CTkScrollableFrame(panes, width=420, label_text="Базовые плоскости и точка")
        self.pencil_input_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 8), pady=2)

        sol_frame = ctk.CTkFrame(panes)
        sol_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=2)

        sol_header = ctk.CTkFrame(sol_frame, fg_color="transparent")
        sol_header.pack(fill=tk.X, padx=8, pady=6)

        ctk.CTkLabel(sol_header, text="📝 Решение уравнения пучка", font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT)

        self.pencil_btn_3d = ctk.CTkButton(sol_header, text="🔮 Показать в 3D", width=120, fg_color="#3B82F6", command=self.show_in_3d, state="disabled")
        self.pencil_btn_3d.pack(side=tk.RIGHT, padx=5)

        self.pencil_btn_copy = ctk.CTkButton(
            sol_header, text="📄 Копировать", width=110,
            command=lambda: self.copy_to_clipboard(self.pencil_sol_box),
            state="disabled"
        )
        self.pencil_btn_copy.pack(side=tk.RIGHT, padx=5)

        self.pencil_sol_box = RichSolutionBox(sol_frame)
        self.pencil_sol_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.solution_boxes.append(self.pencil_sol_box)

        self.pencil_inputs = {}
        ctk.CTkLabel(self.pencil_input_frame, text="Плоскость P₁ (A₁x + B₁y + C₁z + D₁ = 0):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4, 2))
        self.pencil_inputs['A1'] = self._create_entry_row(self.pencil_input_frame, "A₁:", "1")
        self.pencil_inputs['B1'] = self._create_entry_row(self.pencil_input_frame, "B₁:", "2")
        self.pencil_inputs['C1'] = self._create_entry_row(self.pencil_input_frame, "C₁:", "-1")
        self.pencil_inputs['D1'] = self._create_entry_row(self.pencil_input_frame, "D₁:", "3")

        ctk.CTkLabel(self.pencil_input_frame, text="Плоскость P₂ (A₂x + B₂y + C₂z + D₂ = 0):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(8, 2))
        self.pencil_inputs['A2'] = self._create_entry_row(self.pencil_input_frame, "A₂:", "2")
        self.pencil_inputs['B2'] = self._create_entry_row(self.pencil_input_frame, "B₂:", "-1")
        self.pencil_inputs['C2'] = self._create_entry_row(self.pencil_input_frame, "C₂:", "1")
        self.pencil_inputs['D2'] = self._create_entry_row(self.pencil_input_frame, "D₂:", "-4")

        ctk.CTkLabel(self.pencil_input_frame, text="Точка M₀ (через которую проходит плоскость):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(8, 2))
        self.pencil_inputs['x0'] = self._create_entry_row(self.pencil_input_frame, "x₀:", "1")
        self.pencil_inputs['y0'] = self._create_entry_row(self.pencil_input_frame, "y₀:", "1")
        self.pencil_inputs['z0'] = self._create_entry_row(self.pencil_input_frame, "z₀:", "1")

        btn_calc = ctk.CTkButton(
            self.pencil_input_frame, text="⚡ Найти плоскость из пучка",
            font=("Segoe UI", 13, "bold"), height=36,
            fg_color="#10B981", hover_color="#059669",
            command=self._calc_pencil
        )
        btn_calc.pack(fill=tk.X, pady=(15, 6))

    def _load_pencil_preset(self):
        self._calc_pencil()

    def _calc_pencil(self):
        try:
            self.current_calc_tab = "🌀 Пучок плоскостей"
            pl1 = (self.pencil_inputs['A1'].get(), self.pencil_inputs['B1'].get(), self.pencil_inputs['C1'].get(), self.pencil_inputs['D1'].get())
            pl2 = (self.pencil_inputs['A2'].get(), self.pencil_inputs['B2'].get(), self.pencil_inputs['C2'].get(), self.pencil_inputs['D2'].get())
            pt = (self.pencil_inputs['x0'].get(), self.pencil_inputs['y0'].get(), self.pencil_inputs['z0'].get())

            res = PlanePencilSolver.pencil_through_point(pl1, pl2, pt)

            self.viz_panel.clear_objects()
            self.viz_panel.add_plane(float(pl1[0]), float(pl1[1]), float(pl1[2]), float(pl1[3]), "P₁ (база)", color="#64748B")
            self.viz_panel.add_plane(float(pl2[0]), float(pl2[1]), float(pl2[2]), float(pl2[3]), "P₂ (база)", color="#F59E0B")
            self.viz_panel.add_plane(res['A'], res['B'], res['C'], res['D'], "Искомая плоскость из пучка", color="#10B981")
            p0 = [float(c) for c in pt]
            self.viz_panel.add_point(p0[0], p0[1], p0[2], "M₀")
            self.viz_panel.redraw()

            self.pencil_sol_box.set_solution(res['steps'])
            self.pencil_btn_3d.configure(state="normal")
            self.pencil_btn_copy.configure(state="normal")
            self.set_status("✓ Плоскость из пучка успешно найдена!")

        except Exception as ex:
            self.set_status(f"Ошибка вычисления: {str(ex)}", is_error=True)
            messagebox.showerror("Ошибка", f"Проверьте правильность введенных чисел:\n{str(ex)}")

    # =========================================================================
    # 6. ВКЛАДКА: СПРАВОЧНИК ГЛАВЫ 4
    # =========================================================================
    def _setup_handbook_tab(self):
        tab = self.tab_handbook

        hb_container = ctk.CTkScrollableFrame(tab)
        hb_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        for sec in HANDBOOK_SECTIONS:
            sec_card = ctk.CTkFrame(hb_container, corner_radius=8)
            sec_card.pack(fill=tk.X, pady=6, padx=4)

            title_lbl = ctk.CTkLabel(
                sec_card, text=sec['title'],
                font=("Segoe UI", 14, "bold"), text_color="#38BDF8", anchor="w"
            )
            title_lbl.pack(fill=tk.X, padx=12, pady=(10, 4))

            content_lbl = ctk.CTkLabel(
                sec_card, text=to_pretty_math(sec['content']),
                font=("Consolas", 12), justify="left", anchor="w"
            )
            content_lbl.pack(fill=tk.X, padx=12, pady=(0, 10))


def main():
    app = GeoCalculatorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
