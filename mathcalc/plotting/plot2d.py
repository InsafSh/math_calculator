"""Отрисовка 2D-сцены (формат — mathcalc.core.result.new_scene2d)."""

from typing import Any, Dict, Optional

import numpy as np

from .theme import PlotTheme, DARK


def _style_axes(ax, theme: PlotTheme):
    ax.figure.patch.set_facecolor(theme.background)
    ax.set_facecolor(theme.background)
    ax.tick_params(colors=theme.text, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(theme.grid)
    ax.grid(True, linestyle='--', alpha=0.4, color=theme.grid)
    ax.axhline(0, color=theme.text, linewidth=0.8, alpha=0.6)
    ax.axvline(0, color=theme.text, linewidth=0.8, alpha=0.6)


def _view_box(scene: Dict[str, Any]):
    """Квадратная область просмотра, охватывающая все объекты сцены."""
    xs, ys = [], []
    for (x, y, *_r) in scene['points']:
        xs.append(x); ys.append(y)
    for (p1, p2, *_r) in scene['segments']:
        xs += [p1[0], p2[0]]; ys += [p1[1], p2[1]]
    for (px, py, *_r) in scene['lines']:
        xs.append(px); ys.append(py)
    for (cx, cy, *_r) in scene['curves']:
        cx, cy = np.asarray(cx), np.asarray(cy)
        closed = abs(cx[0] - cx[-1]) < 1e-9 and abs(cy[0] - cy[-1]) < 1e-9
        n = len(cx)
        # у незамкнутых кривых (ветви гиперболы, параболы) хвосты не расширяют область просмотра
        sl = slice(None) if closed else slice(int(n * 0.2), int(n * 0.8))
        xs += list(cx[sl]); ys += list(cy[sl])
    if not xs:
        xs, ys = [-5, 5], [-5, 5]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    span = max(x1 - x0, y1 - y0, 2.0)
    half = span / 2 + span * 0.18
    cx_, cy_ = (x0 + x1) / 2, (y0 + y1) / 2
    return (cx_ - half, cx_ + half), (cy_ - half, cy_ + half), span


def render_scene2d(ax, scene: Optional[Dict[str, Any]], theme: PlotTheme = DARK):
    """Рисует сцену на осях ax (очищая их)."""
    ax.clear()
    _style_axes(ax, theme)
    if not scene:
        ax.text(0.5, 0.5, "Чертёж появится после решения задачи", transform=ax.transAxes,
                ha='center', va='center', color=theme.text, fontsize=11)
        return

    xlim, ylim, span = _view_box(scene)

    for (px, py, dx, dy, label, col) in scene['lines']:
        nrm = float(np.hypot(dx, dy)) or 1.0
        t = np.array([-1.0, 1.0]) * span * 20 / nrm
        ax.plot(px + dx * t, py + dy * t, color=col, linewidth=1.4, alpha=0.85,
                linestyle='--' if label.startswith('асимптот') else '-', label=label or None)
    for (cx, cy, label, col) in scene['curves']:
        ax.plot(cx, cy, color=col, linewidth=2.2, label=label or None)
    for (p1, p2, label, col, style) in scene['segments']:
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=col, linewidth=1.8, linestyle=style, label=label or None)
    for (x, y, name, col) in scene['points']:
        ax.scatter([x], [y], color=col, s=42, zorder=5, edgecolors='white', linewidths=0.8)
        ax.annotate(name, (x, y), textcoords="offset points", xytext=(6, 6), color=col, fontsize=10, fontweight='bold')

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_aspect('equal', adjustable='box')
    ax.set_title(scene.get('title', ''), color=theme.text, fontsize=11)
    _, labels = ax.get_legend_handles_labels()
    if labels:
        leg = ax.legend(loc='best', fontsize=8, facecolor=theme.background, edgecolor=theme.grid)
        for txt in leg.get_texts():
            txt.set_color(theme.text)
