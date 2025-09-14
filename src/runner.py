from __future__ import annotations
import sys, time
import pandas as pd
from .io import load_clients, load_client_data, save_per_client
from .scoring import score_client
from .textgen import make_push_and_why
from dotenv import load_dotenv
load_dotenv()


def build_all() -> pd.DataFrame:
    clients = load_clients()
    total = len(clients)
    rows, top4_rows = [], []

    print(f"[RUN] старт генерации для {total} клиентов", flush=True)
    for i, (_, c) in enumerate(clients.iterrows(), start=1):
        cid = int(c["client_code"])
        name = str(c.get("name","Клиент"))
        print(f"[{i:03d}/{total}] клиент {cid} — {name}: агрегации…", flush=True)

        tx, tr = load_client_data(cid)
        top4, diag = score_client(c, tx, tr)
        best = top4[0]

        gender = c.get("gender", None)
        age    = int(c.get("age", 0))
        status = c.get("status","")
        city   = c.get("city","")

        print(f"[{i:03d}/{total}] → LLM push/why…", flush=True)
        texts = make_push_and_why(
            best.name, name, gender, age, status, city,
            diag.get("top3", []),
            best.benefit_month_kzt,
            best.reasons
        )
        print(f"[{i:03d}/{total}] ✓ LLM tokens: {texts['llm_tokens']}", flush=True)

        rows.append({
            "client_code": cid,
            "name": name,
            "age": age,
            "status": status,
            "city": city,
            "product": best.name,
            "benefit_kzt": best.benefit_month_kzt,
            "push_before_ai": texts["push_before_ai"],
            "push_notification": texts["push_after_ai"],   
            "why_after_ai": texts["why_after_ai"],   
        })

        for rank, s in enumerate(top4, start=1):
            top4_rows.append({"client_code": cid, "rank": rank, "product": s.name, "benefit_kzt": s.benefit_month_kzt})
            
        time.sleep(0.1)

    df = pd.DataFrame(rows).sort_values("client_code")
    df.to_csv("submission_full.csv", index=False)

    pd.DataFrame(top4_rows).to_csv("submission_top4.csv", index=False)
    df[["client_code","product","push_notification"]].to_csv("submission.csv", index=False)
    save_per_client(df[["client_code","product","push_notification"]])

    print(f"[RUN] готово: submission.csv, submission_top4.csv и папка ./submission/", flush=True)
    return df

if __name__ == "__main__":
    build_all()
