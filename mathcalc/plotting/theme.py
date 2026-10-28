"""Цветовые темы графиков."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlotTheme:
    background: str
    pane: str
    text: str
    grid: str
    palette: tuple = ("#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899")


DARK = PlotTheme(background="#1A1B26", pane="#24283B", text="#C0CAF5", grid="#414868")
LIGHT = PlotTheme(background="#FFFFFF", pane="#F1F5F9", text="#1E293B", grid="#CBD5E1")
