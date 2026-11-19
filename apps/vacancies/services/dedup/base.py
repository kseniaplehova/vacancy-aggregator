from abc import ABC, abstractmethod
from typing import Any, Sequence


class Matcher(ABC):
    name: str

    @abstractmethod
    def prepare(self, records: Sequence[Any]) -> list[Any]:
        pass

    @abstractmethod
    def similarity(self, a: Any, b: Any) -> float:
        pass
