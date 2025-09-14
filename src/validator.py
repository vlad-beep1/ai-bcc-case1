import re

def check_length(text: str, lo: int = 180, hi: int = 220) -> bool:
    return lo <= len(text) <= hi

def check_currency(text: str) -> bool:
    return bool(re.search(r"\d[\d\s]* ₸", text))

def check_exclamations(text: str) -> bool:
    return text.count("!") <= 1

def check_caps(text: str) -> bool:
    return not bool(re.search(r"[А-Я]{4,}", text))

def validate_push(text: str) -> tuple[bool, list[str]]:
    """Проверяем пуш по правилам. Возвращает (OK?, список нарушений)."""
    errors = []
    if not check_length(text):
        errors.append("Длина не в 180–220 символов")
    if not check_currency(text):
        errors.append("Нет валюты в формате '27 400 ₸'")
    if not check_exclamations(text):
        errors.append("Слишком много '!'")
    if not check_caps(text):
        errors.append("Есть слова ВСЕМИ БУКВАМИ")
    return (len(errors) == 0, errors)
