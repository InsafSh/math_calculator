"""
Реестр задач.

Каждая задача описывается один раз: раздел, группа, название, поля ввода, примеры и функция решения.
Меню и формы ввода в GUI строятся автоматически по этому описанию, поэтому новая задача
добавляется одним вызовом register() — без правок интерфейса.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from ..core.result import Result

# Порядок разделов в меню. Разделы, в которых пока нет задач, в меню не показываются.
SECTION_ORDER = [
    "Обработка эксперимента",
    "Статистика",
    "Функции и графики",
    "Математический анализ",
    "Дифференциальные уравнения",
    "Линейная алгебра",
    "Сигналы и спектры",
    "Уравнения и оптимизация",
    "Аналитическая геометрия",
]


@dataclass
class Field:
    """
    Поле ввода.
      kind = "expr"   — одно значение (число или выражение: 1/2, sqrt(3), pi)
      kind = "vector" — несколько значений в строку (точка, вектор, коэффициенты); components — подписи
      kind = "choice" — выбор из списка choices
      kind = "formula" — формула или произвольная строка (без разбора как числа)
      kind = "text"   — многострочные данные (таблица измерений); file_import — кнопка загрузки из файла
    """
    key: str
    label: str
    kind: str = "expr"
    default: Any = "0"
    components: Tuple[str, ...] = ()
    choices: Tuple[str, ...] = ()
    hint: str = ""
    rows: int = 0
    file_import: bool = False


@dataclass
class Preset:
    name: str
    values: Dict[str, Any]


@dataclass
class Task:
    id: str
    section: str
    group: str
    title: str
    fields: List[Field]
    solve: Callable[[Dict[str, Any]], Result]
    description: str = ""
    presets: List[Preset] = field(default_factory=list)

    def defaults(self) -> Dict[str, Any]:
        return {f.key: f.default for f in self.fields}

    def run(self, values: Optional[Dict[str, Any]] = None) -> Result:
        """Решение с подстановкой значений по умолчанию для отсутствующих полей."""
        data = self.defaults()
        if values:
            data.update(values)
        return self.solve(data)


_REGISTRY: Dict[str, Task] = {}


def register(task: Task) -> Task:
    if task.id in _REGISTRY:
        raise ValueError(f"Задача с id '{task.id}' уже зарегистрирована")
    keys = [f.key for f in task.fields]
    if len(keys) != len(set(keys)):
        raise ValueError(f"Повторяющиеся ключи полей в задаче '{task.id}'")
    _REGISTRY[task.id] = task
    return task


def get_task(task_id: str) -> Task:
    return _REGISTRY[task_id]


def all_tasks() -> List[Task]:
    return list(_REGISTRY.values())


def tree() -> Dict[str, Dict[str, List[Task]]]:
    """Задачи, сгруппированные для меню: раздел → группа → [задачи] (в порядке регистрации)."""
    out: Dict[str, Dict[str, List[Task]]] = {}
    order = {s: i for i, s in enumerate(SECTION_ORDER)}
    for t in sorted(_REGISTRY.values(), key=lambda t: order.get(t.section, len(order))):
        out.setdefault(t.section, {}).setdefault(t.group, []).append(t)
    return out


# --- короткие конструкторы полей -------------------------------------------------

def num(key: str, label: str, default: Any = "0", hint: str = "") -> Field:
    return Field(key, label, "expr", str(default), hint=hint)


def vec(key: str, label: str, default: Sequence[Any], components: Sequence[str] = ("x", "y", "z"), hint: str = "") -> Field:
    comps = tuple(components)[:len(default)]
    return Field(key, label, "vector", tuple(str(v) for v in default), components=comps, hint=hint)


def point2(key: str, label: str, default: Sequence[Any]) -> Field:
    return vec(key, label, default, ("x", "y"))


def point3(key: str, label: str, default: Sequence[Any]) -> Field:
    return vec(key, label, default, ("x", "y", "z"))


def plane(key: str, label: str, default: Sequence[Any]) -> Field:
    return vec(key, label, default, ("A", "B", "C", "D"), hint="A·x + B·y + C·z + D = 0")


def choice(key: str, label: str, choices: Sequence[str], default: Optional[str] = None) -> Field:
    return Field(key, label, "choice", default or choices[0], choices=tuple(choices))


def formula(key: str, label: str, default: str, hint: str = "") -> Field:
    return Field(key, label, "formula", default, hint=hint)


def text(key: str, label: str, default: str, hint: str = "", rows: int = 7, file_import: bool = True) -> Field:
    return Field(key, label, "text", default, hint=hint, rows=rows, file_import=file_import)
