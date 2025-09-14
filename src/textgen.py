from __future__ import annotations
from typing import List, Optional, Dict, Any
import unicodedata, hashlib, random
from .llm import rewrite_push_tov, rewrite_why_tov

def nfc(s:str)->str: return unicodedata.normalize("NFC", s or "")

EXCEPT_FEMALE = {"Айгерим","Камилла","Сабина","Карина","Жанар","Алина","Нурия","Жанель","Маржан",
                 "Аяжан","Аружан","Гульмира","Марина","Ольга","Ирина","Юлия","Дарья","Елена",
                 "Виктория","Жания","Алия","Диана","Надежда","Оксана","Лаура","Дильназ","Айша"}

def infer_gender(name: str) -> str:
    n = nfc(name)
    if n in EXCEPT_FEMALE or n.endswith(("а","я")): return "F"
    return "M"

def salutation(name:str, gender:Optional[str]=None)->str:
    g = (gender or "").upper() or infer_gender(name)
    return f"Уважаемая {name}" if g == "F" else f"Уважаемый {name}"

def fmt_kzt(v:int)->str:
    s = f"{int(max(0,v)):,}".replace(",", " ")
    return f"{s} ₸"

TEMPLATES = {
    "Карта для путешествий": [
        "{who}, по вашим поездкам и такси — {diag}. Вернётся до {b} ежемесячно{emo}. Оформите карту.",
        "{who}, часто в дороге: {diag}. До {b} кешбэка в месяц{emo}. Оформить карту за пару минут.",
        "{who}, путешествия и такси активны — {diag}. До {b} в месяц{emo}. Подключите карту.",
    ],
    "Премиальная карта": [
        "{who}, крупный остаток и частые рестораны {city}. Премиальная даст до {b} в месяц и бесплатные снятия. Оформите сейчас.",
        "{who}, ваш уровень расходов и остаток подходят под премиум. До {b} ежемесячно + привилегии. Оформите карту.",
    ],
    "Кредитная карта": [
        "{who}, топ-категории — {cats}. Карта вернёт до {b} ежемесячно и даст рассрочку. Откройте карту.",
        "{who}, вы чаще тратите на {cats}. До {b} кешбэка в месяц + рассрочка. Откройте карту.",
        "{who}, любимые покупки: {cats}. До {b} в месяц и удобная рассрочка. Оформите карту.",
    ],
    "Обмен валют": [
        "{who}, часто платите в валюте. Выгодный курс и авто-покупка по целевому — удобно. Настройте обмен.",
        "{who}, валютных операций много. Зафиксируйте целевой курс, меняйте без лишних комиссий. Включите обмен.",
    ],
    "Инвестиции": [
        "{who}, попробуйте инвестиции без комиссий на старте — потенциал до {b} в месяц{emo}. Откройте счёт.",
        "{who}, свободные средства можно вложить — до {b} ежемесячно{emo}. Откройте брокерский счёт.",
    ],
    "Кредит наличными": [
        "{who}, если нужен запас на крупные траты — кредит с гибкими выплатами. Узнайте доступный лимит.",
        "{who}, планируете покупку? Подойдёт кредит наличными с прозрачными условиями. Узнайте лимит.",
    ],
    "Депозит": [
        "{who}, свободные средства ≈ {diag}. Вклад принесёт до {b} в месяц. Откройте вклад.",
        "{who}, держите подушку на вкладе — до {b} ежемесячно. Откройте вклад.",
    ],
}

def choose_template(product: str, seed: int) -> str:
    key = product if product in TEMPLATES else ("Депозит" if product.startswith("Депозит") else "Кредитная карта")
    arr = TEMPLATES[key][:]
    random.Random(seed).shuffle(arr)
    return arr[0]

def pick_emoji(age:int, status:str) -> str:
    if age and age < 25: return random.choice([" 🙂", " 🎉", " 📱"])
    if "Студент" in (status or ""): return " 📚"
    return ""

def make_push_and_why(product:str, name:str, gender:Optional[str], age:int, status:str, city:str,
                      topcats:List[str], benefit:int, reasons:List[str]) -> Dict[str, Any]:
    product = nfc(product); name = nfc(name); status = nfc(status); city = nfc(city)
    who = salutation(name, gender)
    b = fmt_kzt(benefit)
    cats = ", ".join([nfc(c) for c in topcats[:3]]) or "ваши категории"
    diag = "; ".join(reasons[:2]) if reasons else "по вашим тратам"
    emo = pick_emoji(age, status)

    seed = int(hashlib.md5(f"{name}{age}{product}{benefit}".encode("utf-8")).hexdigest(), 16)
    tpl = choose_template(product, seed)
    draft = tpl.format(who=who, b=b, cats=cats, diag=diag, emo=emo, city=city)

    profile = {
        "name": name,
        "gender": (gender or "").upper() or ("F" if who.startswith("Уважаемая") else "M"),
        "age": int(age or 0),
        "status": status,
        "city": city,
        "topcats": topcats,
        "benefit_kzt": benefit,
        "reasons": reasons,
        "product": product,
        "emoji_in_draft": bool(emo),
    }
    variant = seed % 7

    push_ai, tok1 = rewrite_push_tov(draft, profile, variant)
    why_ai,  tok2 = rewrite_why_tov(
        "Аналитика: " + " • ".join(reasons[:3]) if reasons else "Подходит по структуре трат.", profile, variant
    )

    return {
        "push_before_ai": draft,
        "push_after_ai": push_ai,
        "why_after_ai": why_ai,
        "llm_tokens": tok1 + tok2,
    }
