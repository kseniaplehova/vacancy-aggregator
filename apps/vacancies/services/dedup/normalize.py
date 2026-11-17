"""Приведение текста вакансии к виду, удобному для сравнения."""
import re

NOT_WORD = re.compile(r"[^0-9a-zа-я+#]+")
#: организационно-правовые формы: «ООО Авансум» и «Авансум» — одна компания
LEGAL_FORMS = re.compile(r"\b(ооо|оао|зао|одо|чуп|чтуп|уп|ип|ао|llc|ltd|inc|gmbh)\b")


def normalize(text: str | None) -> str:
    """Нижний регистр, «ё» → «е», всё кроме букв, цифр, «+» и «#» заменяется пробелом."""
    text = (text or "").lower().replace("ё", "е")
    return " ".join(NOT_WORD.sub(" ", text).split())


def normalize_company(name: str | None) -> str:
    return " ".join(LEGAL_FORMS.sub(" ", normalize(name)).split())


def key_of(record) -> str:
    """Короткая строка «название + компания» — для методов, дорогих на длинных текстах."""
    return f"{normalize(record.title)} {normalize_company(record.company)}".strip()


def text_of(record) -> str:
    """Весь текст вакансии: название, компания и описание."""
    return f"{key_of(record)} {normalize(record.description)}".strip()


def word_shingles(text: str, size: int = 2) -> set[str]:
    """Множество цепочек из ``size`` соседних слов (шинглов)."""
    words = text.split()
    if len(words) <= size:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i : i + size]) for i in range(len(words) - size + 1)}


def char_shingles(text: str, size: int = 3) -> set[str]:
    """Множество подстрок длины ``size`` — устойчиво к опечаткам и окончаниям слов."""
    if len(text) <= size:
        return {text} if text else set()
    return {text[i : i + size] for i in range(len(text) - size + 1)}
