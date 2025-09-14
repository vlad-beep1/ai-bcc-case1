import os
import pandas as pd

DATA_DIR = os.environ.get("DATA_DIR", "data")
SUBMIT_DIR = os.environ.get("SUBMIT_DIR", "submission")

CLIENTS_CSV = os.path.join(DATA_DIR, "clients.csv")
os.makedirs(SUBMIT_DIR, exist_ok=True)

def load_clients():
    return pd.read_csv(CLIENTS_CSV)

def load_client_data(client_id:int):
    tx_path = os.path.join(DATA_DIR, f"client_{client_id}_transactions_3m.csv")
    tr_path = os.path.join(DATA_DIR, f"client_{client_id}_transfers_3m.csv")
    tx = pd.read_csv(tx_path, parse_dates=["date"]) if os.path.exists(tx_path) else pd.DataFrame()
    tr = pd.read_csv(tr_path, parse_dates=["date"]) if os.path.exists(tr_path) else pd.DataFrame()
 
    if not tx.empty and "client_code" not in tx.columns: tx["client_code"] = client_id
    if not tr.empty and "client_code" not in tr.columns: tr["client_code"] = client_id
    return tx, tr

def save_submission(df: pd.DataFrame):
    df[["client_code","product","push_notification"]].to_csv("submission.csv", index=False)

def save_per_client(df: pd.DataFrame):
    for cid, part in df.groupby("client_code"):
        part[["client_code","product","push_notification"]].to_csv(
            os.path.join(SUBMIT_DIR, f"client_{int(cid)}.csv"), index=False
        )
 # type: ignore