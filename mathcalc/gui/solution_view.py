"""Отображение пошагового решения: текст решателя → оформленный HTML."""

import html

from PySide6.QtWidgets import QTextBrowser

HEADER_MARKS = ('📌', '📝', '⚙️', '📍', '🔄', '📐', '📏', '🎯')
BORDER_CHARS = set("─═┌┐└┘╔╗╚╝ ")

_STYLES = {
    True: dict(text="#E2E8F0", header="#38BDF8", answer_head="#34D399", bullet="#67E8F9", muted="#94A3B8",
               formula_bg="#1E293B", formula_fg="#FBBF24", answer_bg="#064E3B", answer_fg="#6EE7B7"),
    False: dict(text="#1E293B", header="#0369A1", answer_head="#047857", bullet="#0E7490", muted="#64748B",
                formula_bg="#FEF3C7", formula_fg="#92400E", answer_bg="#D1FAE5", answer_fg="#065F46"),
}


def steps_to_html(text: str, dark: bool = True) -> str:
    """
    Преобразует текст решения в HTML.
    Блоки в рамках ┌─┐ (формулы) и ╔═╗ (ответы) становятся цветными карточками,
    строки с эмодзи-маркерами — заголовками этапов, строки с ▸ / • — пунктами.
    """
    st = _STYLES[dark]
    out = []
    buf, buf_kind = [], None
    in_box = False

    def flush():
        nonlocal buf, buf_kind
        if buf:
            bg, fg = (st['answer_bg'], st['answer_fg']) if buf_kind == 'answer' else (st['formula_bg'], st['formula_fg'])
            # без <table>: после таблицы Qt вставляет пустой блок, окрашенный её фоном
            body = "\n".join(" " + html.escape(l) for l in [""] + buf + [""])
            out.append(
                f'<pre style="background-color:{bg}; color:{fg}; font-family:Consolas,\'Cascadia Mono\',monospace;'
                f' font-size:10.5pt; font-weight:bold; margin:4px 0 6px 0;">{body}</pre>')
        buf, buf_kind = [], None

    for raw in text.split('\n'):
        line = raw.rstrip()
        s = line.strip()
        # рамка блока целиком из символов псевдографики
        if s and set(s) <= BORDER_CHARS:
            if s[0] in '┌╔':
                flush()
                in_box, buf_kind = True, ('answer' if s[0] == '╔' else 'formula')
            else:
                flush()
                in_box = False
            continue
        if in_box:
            c = s
            if c and c[0] in '│║':
                c = c[1:]
            if c and c[-1] in '│║':
                c = c[:-1]
            buf.append(c[1:] if c.startswith(' ') else c)
            buf[-1] = buf[-1].rstrip()
            continue
        # строки матриц/определителей (скобки ┌ │ └ без рамки) — тоже моноширинный блок
        if s and s[0] in '┌│└╔║╚':
            if buf_kind != 'formula':
                flush()
                buf_kind = 'formula'
            buf.append(s)
            continue
        flush()
        if not s:
            continue  # отступы между этапами задают margin заголовков и карточек
        esc = html.escape(line)
        if s.startswith(HEADER_MARKS):
            color = st['answer_head'] if s.startswith('🎯') else st['header']
            out.append(f'<p style="color:{color}; font-size:12pt; font-weight:bold; margin:12px 0 4px 0;">{html.escape(s)}</p>')
        elif '▸' in s or s.startswith('•'):
            out.append(f'<div style="color:{st["bullet"]}; font-weight:bold; white-space:pre-wrap; margin:1px 0;">{esc}</div>')
        elif s.startswith('где') or s.startswith('where'):
            out.append(f'<div style="color:{st["muted"]}; white-space:pre-wrap;">{esc}</div>')
        else:
            out.append(f'<div style="color:{st["text"]}; white-space:pre-wrap; margin:1px 0;">{esc}</div>')
    flush()
    return (f'<html><body style="font-family:\'Segoe UI\',\'Cambria Math\',sans-serif; font-size:10.5pt;'
            f' color:{st["text"]};">' + "".join(out) + '</body></html>')


class SolutionView(QTextBrowser):
    """Виджет решения. Хранит исходный текст, чтобы перерисовывать при смене темы и копировать."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOpenExternalLinks(True)
        self.raw_text = ""
        self.dark = True
        self.set_placeholder()

    def set_placeholder(self):
        self.raw_text = ""
        self.setHtml('<p style="color:#94A3B8; font-size:11pt;">Введите данные и нажмите «Решить» (Ctrl+Enter).</p>')

    def set_steps(self, text: str):
        self.raw_text = text
        self.setHtml(steps_to_html(text, self.dark))

    def set_dark(self, dark: bool):
        self.dark = dark
        if self.raw_text:
            self.set_steps(self.raw_text)
