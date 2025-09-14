import os, sys
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(FILE_DIR, ".."))
if PROJECT_ROOT not in sys.path: sys.path.insert(0, PROJECT_ROOT)

from src.runner import build_all

st.set_page_config(page_title="Персональные пуш-уведомления", layout="wide")
st.title("Персональные пуш-уведомления AI-BCC")

SUB_FULL = "submission_full.csv"
SUB_TOP4  = "submission_top4.csv"

def load_existing():
    if os.path.exists(SUB_FULL) and os.path.exists(SUB_TOP4):
        return pd.read_csv(SUB_FULL), pd.read_csv(SUB_TOP4)
    return None, None

rebuild = st.sidebar.button("Пересчитать заново (через OpenAI)")

if "submission" not in st.session_state or rebuild:
    if rebuild:
        with st.spinner("Пересчитываем заново через OpenAI…"):
            st.session_state["submission"] = build_all()
            st.session_state["top4"] = pd.read_csv(SUB_TOP4)
    else:
        df_full, df_top4 = load_existing()
        if df_full is not None:
            st.session_state["submission"] = df_full
            st.session_state["top4"] = df_top4
        else:
            with st.spinner("Готовим аналитику и тексты (первый запуск)…"):
                st.session_state["submission"] = build_all()
                st.session_state["top4"] = pd.read_csv(SUB_TOP4)

sub = st.session_state["submission"]
top4 = st.session_state["top4"]

opts = sub[["client_code","name","age"]].drop_duplicates().sort_values("client_code")
labels = [f"{int(r['client_code'])} — {r['name']} ({int(r['age']) if r['age']==r['age'] else '—'})" for _, r in opts.iterrows()]
choice = st.selectbox("Клиент", labels, index=0)
cid = int(choice.split(" — ")[0])

row = sub[sub.client_code==cid].iloc[0]

left, right = st.columns([1,2], gap="large")
with left:
    st.subheader("Профиль")
    st.write(f"Имя: **{row['name']}**")
    st.write(f"Возраст: **{int(row['age']) if row['age']==row['age'] else '—'}**")
    if 'status' in row and isinstance(row['status'], str) and row['status']:
        st.write(f"Статус: **{row['status']}**")
    if 'city' in row and isinstance(row['city'], str) and row['city']:
        st.write(f"Город: **{row['city']}**")
    st.write(f"Рекомендация: **{row['product']}**")
    st.write(f"Выгода за месяц: **{row['benefit_kzt']:,} ₸**".replace(","," "))

with right:
    st.subheader("Пуш")
    c1, c2 = st.columns(2)
    with c1:
        st.caption("До ИИ")
        st.write(row["push_before_ai"])
    with c2:
        st.caption("После ИИ (OpenAI)")
        st.write(row["push_notification"])

st.markdown("---")
st.subheader("Почему выбран продукт")
st.write("Аналитическое пояснение.")
st.info(row.get("why_after_ai",""))

st.markdown("---")
st.subheader("Top-4 продуктов (выгода/мес)")
t4 = (top4[top4.client_code==cid].sort_values("rank")[["rank","product","benefit_kzt"]])
t4["benefit_kzt"] = t4["benefit_kzt"].map(lambda v: f"{int(v):,} ₸".replace(",", " "))
st.dataframe(t4, use_container_width=True)
