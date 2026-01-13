import os, zipfile, hashlib
import pandas as pd

REGISTROS_DIR = "/app/registros"

def ensure_dirs(periodo: str, ruc: str) -> str:
    base = os.path.join(REGISTROS_DIR, "periodos", periodo, ruc)
    os.makedirs(base, exist_ok=True)
    return base

def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()

def save_zip_and_extract_csv(zip_bytes: bytes, out_dir: str, zip_name: str) -> str:
    zip_path = os.path.join(out_dir, zip_name)
    with open(zip_path, "wb") as f:
        f.write(zip_bytes)

    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        if not names:
            raise RuntimeError("ZIP vacío")
        csv_name = names[0]
        z.extract(csv_name, out_dir)

    return os.path.join(out_dir, csv_name)

def csv_to_xlsx(csv_path: str, xlsx_path: str) -> None:
    df = pd.read_csv(csv_path, sep=",", dtype=str, engine="python")
    df.to_excel(xlsx_path, index=False)
