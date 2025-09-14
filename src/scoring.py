from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Dict
import pandas as pd

from .features import (
    category_spend, monthly_spend, top_categories, sums_in_set, free_funds,
    ONLINE_CATS, TRAVEL_CATS, PREMIUM_BOOST_CATS
)

def kzt_round_1000(x: float) -> int:
    return int(round(max(0.0, float(x)) / 1000.0) * 1000)

def clamp(v, lo, hi): 
    return max(lo, min(hi, v))

@dataclass
class ProductScore:
    name: str
    benefit_month_kzt: int
    reasons: List[str]  

def score_client(cl_row: pd.Series, tx: pd.DataFrame, tr: pd.DataFrame) -> Tuple[List[ProductScore], Dict]:
    """tx / tr — данные одного клиента за 3 месяца."""
    cid   = int(cl_row["client_code"])
    name  = str(cl_row.get("name", "Клиент")).strip()
    avg_bal = float(cl_row.get("avg_monthly_balance_KZT", 0))
    status  = str(cl_row.get("status","")).strip()
    city    = str(cl_row.get("city","")).strip()

    m_total = monthly_spend(tx)
    cat_sp  = category_spend(tx)
    top3    = top_categories(cat_sp, 3)
    online_sum  = sums_in_set(cat_sp, ONLINE_CATS)
    travel_sum  = sums_in_set(cat_sp, TRAVEL_CATS)
    premium_sum = sums_in_set(cat_sp, PREMIUM_BOOST_CATS)

    scores: List[ProductScore] = []

    travel_cashback = 0.04 * travel_sum
    scores.append(ProductScore(
        name="Карта для путешествий",
        benefit_month_kzt=kzt_round_1000(travel_cashback),
        reasons=[
            f"Поездки/такси ≈ {kzt_round_1000(travel_sum)} ₸/мес",
            "4% кешбэк на поездки и такси"
        ],
    ))

    tier = 0.02
    if 1_000_000 <= avg_bal < 6_000_000: tier = 0.03
    if avg_bal >= 6_000_000: tier = 0.04
    base_sum = float(cat_sp.sum() - premium_sum)
    premium_cashback = tier * base_sum + max(tier, 0.04) * premium_sum
    premium_cashback = clamp(premium_cashback, 0, 100_000)  # лимит
    scores.append(ProductScore(
        name="Премиальная карта",
        benefit_month_kzt=kzt_round_1000(premium_cashback),
        reasons=[
            f"Остаток ≈ {kzt_round_1000(avg_bal)} ₸ → кешбэк {int(tier*100)}%",
            "Повышенные категории 4% + бесплатные снятия/переводы"
        ],
    ))

    top_sum = float(cat_sp[cat_sp.index.isin(top3)].sum())
    cc_cashback = 0.10 * (top_sum + online_sum)
    scores.append(ProductScore(
        name="Кредитная карта",
        benefit_month_kzt=kzt_round_1000(cc_cashback),
        reasons=[
            f"Топ-категории: {', '.join(top3) or '—'}",
            "До 10% кешбэк на любимые категории и онлайн-сервисы",
            "Есть рассрочка без переплат"
        ],
    ))

    fx_ops = tr["type"].isin(["fx_buy","fx_sell"]).sum() if not tr.empty else 0
    fx_score = 3000 * fx_ops
    scores.append(ProductScore(
        name="Обмен валют",
        benefit_month_kzt=kzt_round_1000(fx_score),
        reasons=[f"FX-операции за 3 мес: {int(fx_ops)}", "Выгодный курс и авто-покупка по целевому курсу"],
    ))

    free = free_funds(avg_bal, m_total)
    for nm, rate in [("Депозит Сберегательный", 0.165),
                     ("Депозит Накопительный", 0.155),
                     ("Депозит Мультивалютный", 0.145)]:
        scores.append(ProductScore(
            name=nm,
            benefit_month_kzt=kzt_round_1000(free * rate / 12.0),
            reasons=[f"Свободный остаток ≈ {kzt_round_1000(free)} ₸", f"Ставка {rate*100:.2f}% годовых"],
        ))

    invest_hint = 2000 if free > 0 else 0
    scores.append(ProductScore(
        name="Инвестиции",
        benefit_month_kzt=kzt_round_1000(invest_hint),
        reasons=["0% комиссии на старте, низкий порог входа"],
    ))

    need_credit = (not tr.empty and tr["type"].isin(["loan_payment_out","installment_payment_out","cc_repayment_out"]).any() and avg_bal < 150_000)
    cash_score = 10_000 if need_credit else 0
    scores.append(ProductScore(
        name="Кредит наличными",
        benefit_month_kzt=kzt_round_1000(cash_score),
        reasons=["Гибкие выплаты; досрочное погашение без штрафов"] if need_credit else ["Показываем только при явной необходимости"],
    ))

    scores = sorted(scores, key=lambda s: s.benefit_month_kzt, reverse=True)
    diag = {
        "monthly_total_spend": round(m_total),
        "top3": top3,
        "travel_sum": round(travel_sum),
        "online_sum": round(online_sum),
        "avg_balance": round(avg_bal),
        "free_funds": round(free)
    }
    return scores[:4], diag
