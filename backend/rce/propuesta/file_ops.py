import os, zipfile, hashlib
import pandas as pd

from .config import REGISTROS_DIR

def ensure_dirs(periodo: str, ruc: str) -> str:
    base = os.path.join(REGISTROS_DIR, "periodos", periodo, ruc)
    os.makedirs(base, exist_ok=True)
    return base

def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()

def save_zip_and_extract_csv(zip_bytes: bytes, out_dir: str, periodo: str) -> str:
    # Sobrescribir siempre por periodo (no acumular archivos)
    for name in os.listdir(out_dir):
        if name.endswith("-propuesta.csv") or name.endswith("-propuesta.zip"):
            try:
                os.remove(os.path.join(out_dir, name))
            except Exception:
                pass

    zip_path = os.path.join(out_dir, f"propuesta_{periodo}.zip")
    with open(zip_path, "wb") as f:
        f.write(zip_bytes)

    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        if not names:
            raise RuntimeError("ZIP vacío")
        csv_name = names[0]
        z.extract(csv_name, out_dir)

    # Renombrar a un nombre estable
    extracted_path = os.path.join(out_dir, csv_name)
    stable_csv = os.path.join(out_dir, f"propuesta_{periodo}.csv")
    if os.path.exists(stable_csv):
        os.remove(stable_csv)
    os.replace(extracted_path, stable_csv)

    return stable_csv

def csv_to_xlsx(csv_path: str, xlsx_path: str) -> None:
    df = pd.read_csv(csv_path, sep=",", dtype=str, engine="python")
    df.to_excel(xlsx_path, index=False)
