import os
import zipfile
import xml.etree.ElementTree as ET


_LINE_TAGS = (
    "InvoiceLine",
    "CreditNoteLine",
    "DebitNoteLine",
)


def _score_xml(xml_bytes: bytes) -> int:
    """
    Puntaje simple para elegir el XML con detalle.
    +2 si hay líneas (Invoice/Credit/Debit)
    +1 si hay descripciones dentro de ítems
    """
    try:
        root = ET.fromstring(xml_bytes)
    except Exception:
        return -1

    score = 0
    lines = []
    for tag in _LINE_TAGS:
        lines.extend(root.findall(f".//{{*}}{tag}"))
    if lines:
        score += 2
        for ln in lines:
            if ln.findall(".//{*}Item") and ln.findall(".//{*}Description"):
                score += 1
                break

    return score


def select_xml_from_zip(zip_path: str, out_dir: str, final_xml_name: str) -> str:
    """
    Selecciona el XML correcto del ZIP (el que contiene detalle) y lo guarda en out_dir.
    Retorna el path final del XML guardado.
    """
    os.makedirs(out_dir, exist_ok=True)
    final_xml_path = os.path.join(out_dir, final_xml_name)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        names = zip_ref.namelist()
        if not names:
            raise RuntimeError("ZIP vacío")

        xml_names = [n for n in names if n.lower().endswith(".xml")]
        if not xml_names:
            # fallback: primer archivo
            xml_names = [names[0]]

        best_name = xml_names[0]
        best_score = -1
        for name in xml_names:
            try:
                score = _score_xml(zip_ref.read(name))
            except Exception:
                score = -1
            if score > best_score:
                best_score = score
                best_name = name

        xml_bytes = zip_ref.read(best_name)
        with open(final_xml_path, "wb") as f:
            f.write(xml_bytes)

    return final_xml_path
