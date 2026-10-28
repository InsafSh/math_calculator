"""Страница справочника по разделу."""

import html

from PySide6.QtWidgets import QLabel, QTextBrowser, QVBoxLayout, QWidget

from ..core.common import to_pretty_math


class HandbookPage(QWidget):
    def __init__(self, title: str, sections, parent=None):
        super().__init__(parent)
        self.sections = sections
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        head = QLabel(title)
        head.setObjectName("taskTitle")
        lay.addWidget(head)
        self.view = QTextBrowser()
        lay.addWidget(self.view, 1)
        self.apply_theme(True, None)

    def apply_theme(self, dark: bool, _plot_theme):
        head = "#38BDF8" if dark else "#0369A1"
        parts = []
        for sec in self.sections:
            parts.append(f'<h3 style="color:{head};">{html.escape(sec["title"])}</h3>')
            parts.append(f'<pre style="font-family:Consolas,monospace; font-size:10.5pt; white-space:pre-wrap;">'
                         f'{html.escape(to_pretty_math(sec["content"]))}</pre>')
        self.view.setHtml("".join(parts))
