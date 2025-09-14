from __future__ import annotations
import pandas as pd
from typing import List, Set

ONLINE_CATS: Set[str] = {"Едим дома", "Смотрим дома", "Играем дома"}
TRAVEL_CATS: Set[str] = {"Путешествия", "Такси", "Отели"}
PREMIUM_BOOST_CATS: Set[str] = {"Ювелирные украшения", "Косметика и Парфюмерия", "Кафе и рестораны"}

def monthly_spend(tx: pd.DataFrame) -> float:
    """Средняя помесячная трата за 3 мес (строго по ТЗ: выгода — за месяц)."""
    if tx is None or tx.empty:
        return 0.0
    return float(tx["amount"].sum()) / 3.0

def category_spend(tx: pd.DataFrame) -> pd.Series:
    """Помесячные траты по категориям."""
    if tx is None or tx.empty:
        return pd.Series(dtype=float)
    return tx.groupby("category")["amount"].sum() / 3.0

def top_categories(cat_spend: pd.Series, k:int=3) -> List[str]:
    if cat_spend is None or cat_spend.empty:
        return []
    return list(cat_spend.sort_values(ascending=False).head(k).index)

def sums_in_set(cat_spend: pd.Series, cats:Set[str]) -> float:
    if cat_spend is None or cat_spend.empty:
        return 0.0
    return float(cat_spend[cat_spend.index.isin(cats)].sum())

def free_funds(avg_balance: float, monthly_total_spend: float) -> float:
    """Свободный остаток: берём «подушку» = 1 месяц трат."""
    return max(0.0, float(avg_balance) - float(monthly_total_spend))
