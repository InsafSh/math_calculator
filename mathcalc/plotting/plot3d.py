"""Отрисовка 3D-сцены (mathcalc.core.result.Scene3D) на осях mplot3d."""

from typing import Optional

import numpy as np

from ..core.result import Scene3D
from .theme import PlotTheme, DARK


def _style_axes(ax, theme: PlotTheme, labels=("X", "Y", "Z")):
    ax.figure.patch.set_facecolor(theme.background)
    ax.set_facecolor(theme.background)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor(theme.pane)
        axis.pane.set_alpha(0.6)
        axis.pane.set_edgecolor(theme.grid)
        axis.line.set_color(theme.text)
    ax.tick_params(colors=theme.text, labelsize=8)
    for setter, name in zip((ax.set_xlabel, ax.set_ylabel, ax.set_zlabel), labels):
        setter(name, color=theme.text, labelpad=4, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.4, color=theme.grid)


def _finite(a) -> np.ndarray:
    a = np.asarray(a, dtype=float).ravel()
    return a[np.isfinite(a)]


def _robust(a) -> np.ndarray:
    """Значения без крайних выбросов (особые точки поверхности)."""
    v = _finite(a)
    if v.size < 50:
        return v
    lo, hi = np.percentile(v, [1, 99])
    span = hi - lo
    return v[(v >= lo - 0.5 * span) & (v <= hi + 0.5 * span)]


def _padded(vals):
    if not vals:
        return (-5.0, 5.0)
    a, b = float(min(vals)), float(max(vals))
    if b - a < 1e-12:
        d = abs(a) * 0.1 or 1.0
        return (a - d, b + d)
    d = (b - a) * 0.05
    return (a - d, b + d)


def render_scene3d(ax, scene: Optional[Scene3D], theme: PlotTheme = DARK):
    """Рисует сцену на 3D-осях ax (очищая их). Область просмотра — куб, охватывающий объекты."""
    ax.cla()
    scene = scene or Scene3D()
    _style_axes(ax, theme, scene.labels)
    palette = theme.palette

    xs, ys, zs = [], [], []
    for pt in scene.points:
        xs.append(pt['p'][0]); ys.append(pt['p'][1]); zs.append(pt['p'][2])
    for ln in scene.lines:
        (x0, y0, z0), (m, p, q) = ln['p'], ln['s']
        xs += [x0 - 2 * m, x0 + 2 * m]; ys += [y0 - 2 * p, y0 + 2 * p]; zs += [z0 - 2 * q, z0 + 2 * q]
    for seg in scene.segments:
        for key in ('p1', 'p2'):
            xs.append(seg[key][0]); ys.append(seg[key][1]); zs.append(seg[key][2])
    for vec in scene.vectors:
        xs += [vec['p'][0], vec['p'][0] + vec['v'][0]]
        ys += [vec['p'][1], vec['p'][1] + vec['v'][1]]
        zs += [vec['p'][2], vec['p'][2] + vec['v'][2]]

    if scene.surfaces or scene.curves:
        # графики функций: у каждой оси свой диапазон (масштабы величин обычно разные)
        for srf in scene.surfaces:
            xs += list(_finite(srf['X'])); ys += list(_finite(srf['Y'])); zs += list(_robust(srf['Z']))
        for crv in scene.curves:
            xs += list(_finite(crv['x'])); ys += list(_finite(crv['y'])); zs += list(_finite(crv['z']))
        rx, ry, rz = (_padded(xs), _padded(ys), _padded(zs))
        half = max(rx[1] - rx[0], ry[1] - ry[0]) / 2
    else:
        if xs:
            lo = np.array([min(xs), min(ys), min(zs)]) - 2.5
            hi = np.array([max(xs), max(ys), max(zs)]) + 2.5
        else:
            lo, hi = np.array([-5.0] * 3), np.array([5.0] * 3)
        half = max(float(np.max(hi - lo)), 6.0) / 2
        c = (lo + hi) / 2
        rx, ry, rz = [(c[i] - half, c[i] + half) for i in range(3)]

    for srf in scene.surfaces:
        Z = np.where((srf['Z'] >= rz[0]) & (srf['Z'] <= rz[1]), srf['Z'], np.nan)
        ax.plot_surface(srf['X'], srf['Y'], Z, cmap=srf['cmap'], alpha=0.88, linewidth=0.2,
                        edgecolor=theme.grid, rstride=1, cstride=1, antialiased=True)
        if srf['label']:
            ax.plot([], [], color=theme.palette[0], linewidth=6, alpha=0.6, label=srf['label'])
    for crv in scene.curves:
        ax.plot(crv['x'], crv['y'], crv['z'], color=crv['color'], linewidth=2.4, label=crv['label'] or None)

    grid_res = 12
    for i, pl in enumerate(scene.planes):
        A, B, C, D = pl['A'], pl['B'], pl['C'], pl['D']
        color = pl['color'] or palette[i % len(palette)]
        if abs(C) >= 1e-5:
            X, Y = np.meshgrid(np.linspace(*rx, grid_res), np.linspace(*ry, grid_res))
            Z = (-A * X - B * Y - D) / C
        elif abs(B) >= 1e-5:
            X, Z = np.meshgrid(np.linspace(*rx, grid_res), np.linspace(*rz, grid_res))
            Y = (-A * X - D) / B
        elif abs(A) >= 1e-5:
            Y, Z = np.meshgrid(np.linspace(*ry, grid_res), np.linspace(*rz, grid_res))
            X = np.full_like(Y, -D / A)
        else:
            continue
        ax.plot_surface(X, Y, Z, alpha=0.35, color=color, edgecolor=color, linewidth=0.4)
        # невидимая линия — чтобы плоскость попала в легенду
        ax.plot([], [], color=color, linewidth=6, alpha=0.5, label=pl['label'])

    t_span = np.linspace(-half * 1.5, half * 1.5, 40)
    for i, ln in enumerate(scene.lines):
        (x0, y0, z0), (m, p, q) = ln['p'], ln['s']
        norm_s = np.sqrt(m ** 2 + p ** 2 + q ** 2) or 1.0
        ax.plot(x0 + m / norm_s * t_span, y0 + p / norm_s * t_span, z0 + q / norm_s * t_span,
                color=ln['color'] or palette[(i + 2) % len(palette)], linewidth=2.5, label=ln['label'])

    for seg in scene.segments:
        p1, p2 = seg['p1'], seg['p2']
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]], linestyle='--', color=seg['color'], linewidth=1.8, alpha=0.9)

    for vec in scene.vectors:
        (x0, y0, z0), (vx, vy, vz) = vec['p'], vec['v']
        ax.quiver(x0, y0, z0, vx, vy, vz, color=vec['color'], linewidth=2.0, arrow_length_ratio=0.2)
        ax.text(x0 + vx, y0 + vy, z0 + vz, f" {vec['label']}", color=vec['color'], fontsize=9, fontweight='bold')

    for pt in scene.points:
        x, y, z = pt['p']
        ax.scatter([x], [y], [z], color=pt['color'], s=60, edgecolors='white', linewidth=1.2, zorder=10)
        ax.text(x + 0.15, y + 0.15, z + 0.15, f" {pt['label']}({x:.3g}; {y:.3g}; {z:.3g})",
                color=pt['color'], fontsize=9, fontweight='bold')

    ax.set_xlim(rx); ax.set_ylim(ry); ax.set_zlim(rz)
    _, labels = ax.get_legend_handles_labels()
    if labels:
        leg = ax.legend(loc='upper right', fontsize=8, facecolor=theme.pane)
        for txt in leg.get_texts():
            txt.set_color(theme.text)
