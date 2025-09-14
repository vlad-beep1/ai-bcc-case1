from __future__ import annotations
import os, re, unicodedata, json, time
from typing import Dict, Any, Tuple
from dotenv import load_dotenv
load_dotenv()


BASE_SYS = (
    "Ты редактор банка. Требования: 180–220 символов; обращение «Уважаемый/Уважаемая {имя}»; "
    "одна мысль и один CTA; до 1 уместного эмодзи; числа с пробелами и знак «₸» только рядом с суммами; "
    "без CAPS и завышенных обещаний. Сохрани выгоду за месяц и короткое объяснение выбора. "
    "Подстрой стиль под профиль: молодым/студентам — дружелюбнее; 40+ и премиум — официальнее. "
    "Избегай повторов формулировок между клиентами."
)
WHY_SYS = (
    "Объясни выбор продукта для жюри. 180–220 символов, 1–2 тезиса, без воды. "
    "Учитывай возраст, статус, город, топ-категории и выгоду. Знак «₸» ставь только после сумм."
)

def _normalize_money(text: str) -> str:
    t = unicodedata.normalize("NFC", text)
    t = re.sub(r"[^\S\r\n]+", " ", t).strip()
    t = re.sub(r"\b\d{4,}\b", lambda m: f"{int(m.group(0)):,}".replace(",", " "), t) 
    t = re.sub(r"(?<=\d)\s*[тТ]\b", " ₸", t) 
    t = re.sub(r"\s*₸", " ₸", t)
    return t

def _fit_len(t: str, lo=180, hi=220) -> str:
    t = _normalize_money(t)
    if len(t) > hi:
        cut = t[:hi]
        for sep in [". ", " — ", "; "]:
            if sep in cut:
                cut = cut[:cut.rfind(sep)+1]; break
        t = cut.rstrip(" ,;—")
    while len(t) < lo:
        extra = " Подробности в приложении."
        if t.endswith(extra): break
        t += extra
    return t

def _openai_call(sys_prompt: str, payload: Dict[str, Any], temperature: float) -> Tuple[str,int]:
    """Всегда обращаемся к OpenAI. 5 ретраев с экспоненциальной паузой."""
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY отсутствует. Добавь ключ в .env")

    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    content = json.dumps(payload, ensure_ascii=False)

    last_err = None
    for attempt in range(1, 6):
        try:
            r = client.chat.completions.create(
                model=model,
                messages=[{"role":"system","content":sys_prompt},
                          {"role":"user","content":content}],
                temperature=temperature,
                max_tokens=360,
            )
            out = r.choices[0].message.content.strip()
            usage = getattr(r, "usage", None)
            tokens = (usage.total_tokens if usage and hasattr(usage, "total_tokens") else 0)
            return _fit_len(out), tokens
        except Exception as e:
            last_err = e
            sleep = 1.0 * (2 ** (attempt-1))
            print(f"[LLM] ошибка {attempt}/5: {e} — ждём {sleep:.1f}s", flush=True)
            time.sleep(sleep)
    raise RuntimeError(f"OpenAI не отвечает после ретраев: {last_err}")

def rewrite_push_tov(draft: str, profile: Dict[str, Any], variant: int) -> Tuple[str,int]:
    return _openai_call(BASE_SYS, {"profile": profile, "draft": draft, "variant": int(variant)}, temperature=0.80)

def rewrite_why_tov(reasons_text: str, profile: Dict[str, Any], variant: int) -> Tuple[str,int]:
    return _openai_call(WHY_SYS, {"profile": profile, "draft": reasons_text, "variant": int(variant)}, temperature=0.50)
