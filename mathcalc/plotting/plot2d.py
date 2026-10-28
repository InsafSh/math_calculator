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


def _finite(a) -> np.ndarray:
    a = np.asarray(a, dtype=float).ravel()
    return a[np.isfinite(a)]


def _robust_range(vals: np.ndarray):
    """Диапазон без выбросов (вертикальные асимптоты дают огромные значения у кривых)."""
    if vals.size == 0:
        return None
    if vals.size < 20:
        return float(vals.min()), float(vals.max())
    lo, hi = np.percentile(vals, [2, 98])
    full_lo, full_hi = float(vals.min()), float(vals.max())
    span = hi - lo
    # если «хвосты» не слишком далеко — показываем всё
    if full_hi - full_lo <= 3 * max(span, 1e-12):
        return full_lo, full_hi
    return float(lo - 0.25 * span), float(hi + 0.25 * span)


def _collect(scene: Dict[str, Any]):
    xs, ys = [], []
    for (x, y, *_r) in scene['points']:
        xs.append(x); ys.append(y)
    for (p1, p2, *_r) in scene['segments']:
        xs += [p1[0], p2[0]]; ys += [p1[1], p2[1]]
    for (px, py, *_r) in scene['lines']:
        xs.append(px); ys.append(py)
    for (sx, sy, *_r) in scene.get('scatter', []):
        xs += list(_finite(sx)); ys += list(_finite(sy))
    for (ex, ey, yerr, xerr, *_r) in scene.get('errorbars', []):
        ex, ey = np.asarray(ex, float), np.asarray(ey, float)
        ye = np.zeros_like(ey) if yerr is None else np.asarray(yerr, float)
        xe = np.zeros_like(ex) if xerr is None else np.asarray(xerr, float)
        xs += list(_finite(ex - xe)) + list(_finite(ex + xe)); ys += list(_finite(ey - ye)) + list(_finite(ey + ye))
    for (bx, lo, hi, *_r) in scene.get('bands', []):
        xs += list(_finite(bx)); ys += list(_finite(lo)) + list(_finite(hi))
    for (X, Y, *_r) in scene.get('contours', []):
        xs += [float(np.nanmin(X)), float(np.nanmax(X))]; ys += [float(np.nanmin(Y)), float(np.nanmax(Y))]
    return xs, ys


def _view_box_equal(scene: Dict[str, Any]):
    """Квадратная область просмотра, охватывающая все объекты сцены (геометрические чертежи)."""
    xs, ys = _collect(scene)
    for (cx, cy, *_r) in scene['curves']:
        cx, cy = np.asarray(cx, float), np.asarray(cy, float)
        closed = abs(cx[0] - cx[-1]) < 1e-9 and abs(cy[0] - cy[-1]) < 1e-9
        n = len(cx)
        # у незамкнутых кривых (ветви гиперболы, параболы) хвосты не расширяют область просмотра
        sl = slice(None) if closed else slice(int(n * 0.2), int(n * 0.8))
        xs += list(_finite(cx[sl])); ys += list(_finite(cy[sl]))
    if not xs:
        xs, ys = [-5, 5], [-5, 5]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    span = max(x1 - x0, y1 - y0, 2.0)
    half = span / 2 + span * 0.18
    cx_, cy_ = (x0 + x1) / 2, (y0 + y1) / 2
    return (cx_ - half, cx_ + half), (cy_ - half, cy_ + half), span


def _view_box_free(scene: Dict[str, Any]):
    """Независимые диапазоны по осям (графики функций, данные эксперимента)."""
    xs, ys = _collect(scene)
    cxs, cys = [], []
    for (cx, cy, *_r) in scene['curves']:
        cxs += list(_finite(cx)); cys += list(_finite(cy))
    xs_all = np.array(xs + cxs, dtype=float)
    xr = (float(xs_all.min()), float(xs_all.max())) if xs_all.size else (-5.0, 5.0)
    yr_c = _robust_range(np.array(cys, dtype=float))
    ys_arr = np.array(ys, dtype=float)
    lo_candidates = [v for v in ([yr_c[0]] if yr_c else []) + ([float(ys_arr.min())] if ys_arr.size else [])]
    hi_candidates = [v for v in ([yr_c[1]] if yr_c else []) + ([float(ys_arr.max())] if ys_arr.size else [])]
    yr = (min(lo_candidates), max(hi_candidates)) if lo_candidates else (-5.0, 5.0)

    def pad(r):
        a, b = r
        if b - a < 1e-12:
            d = abs(a) * 0.1 or 1.0
            return a - d, b + d
        d = (b - a) * 0.06
        return a - d, b + d

    xr, yr = pad(xr), pad(yr)
    return xr, yr, max(xr[1] - xr[0], yr[1] - yr[0])


def render_scene2d(ax, scene: Optional[Dict[str, Any]], theme: PlotTheme = DARK):
    """Рисует сцену на осях ax (очищая их)."""
    ax.clear()
    _style_axes(ax, theme)
    if not scene:
        ax.text(0.5, 0.5, "Чертёж появится после решения задачи", transform=ax.transAxes,
                ha='center', va='center', color=theme.text, fontsize=11)
        return

    if scene.get('bars'):
        for ln in list(ax.lines):  # линии осей x = 0, y = 0 на столбчатой диаграмме не нужны
            ln.remove()
        labels, values, col = scene['bars']
        ax.bar(range(len(values)), values, color=col, alpha=0.85)
        ax.set_xticks(range(len(values)), labels, color=theme.text)
        for i, v in enumerate(values):
            ax.annotate(f"{v:.3g}", (i, v), textcoords="offset points", xytext=(0, 3), ha='center',
                        color=theme.text, fontsize=8)
        ax.set_title(scene.get('title', ''), color=theme.text, fontsize=11)
        if scene.get('ylabel'):
            ax.set_ylabel(scene['ylabel'], color=theme.text)
        return

    equal = scene.get('equal', True)
    xlim, ylim, span = (_view_box_equal if equal else _view_box_free)(scene)
    xlim = scene.get('xlim') or xlim
    ylim = scene.get('ylim') or ylim
    span = max(span, xlim[1] - xlim[0], ylim[1] - ylim[0])

    for (bx, lo, hi, label, col) in scene.get('bands', []):
        ax.fill_between(bx, lo, hi, color=col, alpha=0.22, linewidth=0, label=label or None)
    for (X, Y, Z, levels, label, col) in scene.get('contours', []):
        cs = ax.contour(X, Y, Z, levels=levels, colors=None if col is None else [col],
                        cmap='viridis' if col is None else None, linewidths=1.6)
        if col is None and len(np.atleast_1d(levels)) > 1:
            ax.clabel(cs, fontsize=7, inline=True, fmt='%.3g')
        if label:
            ax.plot([], [], color=col or theme.palette[0], label=label)
    for line in scene['lines']:
        px, py, dx, dy, label, col = line[:6]
        style = line[6] if len(line) > 6 else ('--' if label.startswith('асимптот') else '-')
        nrm = float(np.hypot(dx, dy)) or 1.0
        t = np.array([-1.0, 1.0]) * span * 20 / nrm
        ax.plot(px + dx * t, py + dy * t, color=col, linewidth=1.4, alpha=0.85, linestyle=style, label=label or None)
    for curve in scene['curves']:
        cx, cy, label, col = curve[:4]
        style = curve[4] if len(curve) > 4 else '-'
        ax.plot(cx, cy, color=col, linewidth=2.2, linestyle=style, label=label or None)
    for (p1, p2, label, col, style) in scene['segments']:
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=col, linewidth=1.8, linestyle=style, label=label or None)
    for (sx, sy, label, col) in scene.get('scatter', []):
        ax.scatter(sx, sy, color=col, s=22, zorder=4, label=label or None)
    for (ex, ey, yerr, xerr, label, col) in scene.get('errorbars', []):
        ax.errorbar(ex, ey, yerr=yerr, xerr=xerr, fmt='o', color=col, ms=4, capsize=3, elinewidth=1, zorder=5,
                    label=label or None)
    for (x, y, name, col) in scene['points']:
        ax.scatter([x], [y], color=col, s=42, zorder=6, edgecolors='white', linewidths=0.8)
        if name:
            ax.annotate(name, (x, y), textcoords="offset points", xytext=(6, 6), color=col, fontsize=10, fontweight='bold')

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    if equal:
        ax.set_aspect('equal', adjustable='box')
    if scene.get('xlabel'):
        ax.set_xlabel(scene['xlabel'], color=theme.text)
    if scene.get('ylabel'):
        ax.set_ylabel(scene['ylabel'], color=theme.text)
    ax.set_title(scene.get('title', ''), color=theme.text, fontsize=11)
    _, labels = ax.get_legend_handles_labels()
    if labels:
        leg = ax.legend(loc='best', fontsize=8, facecolor=theme.background, edgecolor=theme.grid)
        for txt in leg.get_texts():
            txt.set_color(theme.text)
