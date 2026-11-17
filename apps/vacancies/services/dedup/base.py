from abc import ABC, abstractmethod
from typing import Any, Sequence


class Matcher(ABC):
    """Метод оценки похожести двух вакансий.

    Работа разбита на два шага. ``prepare`` один раз превращает каждую вакансию
    в представление, удобное методу (строку, множество, сигнатуру, вектор).
    ``similarity`` сравнивает два представления и возвращает число от 0 до 1,
    где 1 — полное совпадение.
    """

    name: str

    @abstractmethod
    def prepare(self, records: Sequence[Any]) -> list[Any]:
        """Строит представления для всех вакансий сразу."""

    @abstractmethod
    def similarity(self, a: Any, b: Any) -> float:
        """Похожесть двух представлений, от 0 до 1."""
