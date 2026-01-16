import os
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
from sqlalchemy.orm import Session

from core.database import Empresa, RCEPropuestaItem, CPEDetalle, CPEEvidencia
from rce.xml_service.config import REGISTROS_DIR


def _report_path(ruc: str, periodo: str) -> str:
    base_dir = os.path.join(REGISTROS_DIR, "periodos", periodo, ruc, f"reporte_{periodo}")
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, f"reporte_{periodo}.xlsx")

def _text(elem: Optional[ET.Element]) -> str:
    if elem is None or elem.text is None:
        return ""
    return elem.text.strip()

def _dec(val: str) -> Decimal:
    if not val:
        return Decimal("0")
    try:
        return Decimal(val)
    except InvalidOperation:
        return Decimal("0")

def _split_id(doc_id: str) -> Tuple[str, str]:
    if "-" not in doc_id:
        return doc_id, ""
    parts = doc_id.split("-", 1)
    return parts[0], parts[1]

def _sum_tax_subtotals(root: ET.Element) -> Dict[str, Decimal]:
    totals = {
        "nbase1": Decimal("0"),
        "nigv1": Decimal("0"),
        "nina": Decimal("0"),
        "nexo": Decimal("0"),
        "nisc": Decimal("0"),
        "nicbper": Decimal("0"),
    }

    for sub in root.findall(".//{*}TaxSubtotal"):
        scheme_id = _text(sub.find(".//{*}TaxScheme/{*}ID"))
        reason = _text(sub.find(".//{*}TaxCategory/{*}TaxExemptionReasonCode"))
        base = _dec(_text(sub.find("./{*}TaxableAmount")))
        tax = _dec(_text(sub.find("./{*}TaxAmount")))

        if scheme_id == "1000":
            if reason == "10":
                totals["nbase1"] += base
                totals["nigv1"] += tax
            elif reason.startswith("30"):
                totals["nina"] += base
            elif reason.startswith("20"):
                totals["nexo"] += base
        elif scheme_id == "2000":
            totals["nisc"] += tax
        elif scheme_id == "7152":
            totals["nicbper"] += tax

    return totals

def _modo_from_xml(root: ET.Element) -> str:
    # Anticipo si hay PrepaidPayment
    if root.find(".//{*}PrepaidPayment/{*}PaidAmount") is not None:
        return "A"
    # No forzar modo si hay mezcla (default vacío)
    return ""

def _has_detraccion(root: ET.Element) -> bool:
    for pt in root.findall(".//{*}PaymentTerms"):
        if _text(pt.find("./{*}ID")).strip().lower() == "detraccion":
            amt = _text(pt.find("./{*}Amount"))
            pct = _text(pt.find("./{*}PaymentPercent"))
            means = _text(pt.find("./{*}PaymentMeansID"))
            if amt or pct or means:
                return True
            return True
    for pm in root.findall(".//{*}PaymentMeans"):
        if _text(pm.find("./{*}ID")).strip().lower() == "detraccion":
            acct = _text(pm.find(".//{*}PayeeFinancialAccount/{*}ID"))
            if acct:
                return True
    return False

def _extract_summary(xml_path: str, ruc_empresa: str, razon_social: Optional[str]) -> Dict[str, Any]:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    issue_date = _text(root.find(".//{*}IssueDate"))
    due_date = _text(root.find(".//{*}DueDate"))
    doc_id = _text(root.find(".//{*}ID"))
    serie, numero = _split_id(doc_id)
    doc_type = _text(root.find(".//{*}InvoiceTypeCode"))
    currency = _text(root.find(".//{*}DocumentCurrencyCode"))

    supplier_id = _text(root.find(".//{*}AccountingSupplierParty//{*}ID"))
    supplier_name = _text(root.find(".//{*}AccountingSupplierParty//{*}RegistrationName"))

    customer_id = _text(root.find(".//{*}AccountingCustomerParty//{*}ID"))
    customer_name = _text(root.find(".//{*}AccountingCustomerParty//{*}RegistrationName"))

    ntots = _dec(_text(root.find(".//{*}LegalMonetaryTotal/{*}PayableAmount")))
    totals = _sum_tax_subtotals(root)

    modo = _modo_from_xml(root)
    ffechaven2 = due_date or issue_date
    detraccion = _has_detraccion(root)
    detrac_flag = "D" if detraccion else ""

    return {
        "ffechadoc": issue_date,
        "ffechaven": due_date,
        "ccoddoc": doc_type,
        "ccoddas": "",
        "cyeardas": "",
        "cserie": serie,
        "cnumero": numero,
        "ccodenti": doc_type,
        "cdesenti": "Mi Organizacion",
        "ctipdoc": "6",
        "ccodruc": supplier_id,
        "crazsoc": supplier_name,
        "ccodclas": modo,
        "nbase1": totals["nbase1"],
        "nigv1": totals["nigv1"],
        "nbase2": Decimal("0"),
        "nigv2": Decimal("0"),
        "nbase3": Decimal("0"),
        "nigv3": Decimal("0"),
        "nina": totals["nina"],
        "nisc": totals["nisc"],
        "nicbper": totals["nicbper"],
        "nexo": totals["nexo"],
        "ntots": ntots,
        "cdocnodom": "",
        "cnumdere": detrac_flag,
        "ffecre": detrac_flag,
        "ntc": Decimal("0"),
        "freffec": "",
        "crefdoc": "",
        "crefser": "",
        "crefnum": "",
        "cmreg": "S",
        "ndolar": Decimal("0"),
        "ffechaven2": ffechaven2,
        "moneda": currency,
    }


def _flatten_item(
    item: RCEPropuestaItem,
    empresa: Optional[Empresa],
    detalle_json: Dict[str, Any],
) -> List[Dict[str, Any]]:
    lines = detalle_json.get("lines") or []
    rows = []

    base = {
        "ruc": item.ruc_empresa,
        "razon_social": empresa.razon_social if empresa else None,
        "fecha_emision": item.fecha_emision,
        "tipo_cpe": item.tipo_cp,
        "serie": item.serie,
        "correlativo": item.numero,
        "ruc_emisor": item.ruc_emisor,
        "razon_social_emisor": item.razon_emisor,
    }

    if not lines:
        row = dict(base)
        row.update(
            {
                "detalle": None,
                "cantidad": None,
                "valor_unitario_sin_igv": None,
                "precio_unitario_con_igv": None,
                "neto_linea_sin_igv": None,
                "igv_linea": None,
                "total_linea_con_igv": None,
            }
        )
        rows.append(row)
        return rows

    for idx, ln in enumerate(lines):
        row = dict(base) if idx == 0 else {k: None for k in base.keys()}
        row.update(
            {
                "detalle": ln.get("description"),
                "cantidad": ln.get("quantity"),
                "valor_unitario_sin_igv": ln.get("unit_value"),
                "precio_unitario_con_igv": ln.get("unit_price_igv"),
                "neto_linea_sin_igv": ln.get("line_net"),
                "igv_linea": ln.get("line_igv"),
                "total_linea_con_igv": ln.get("line_total"),
            }
        )
        rows.append(row)

    return rows


def build_reporte_detalle(
    db: Session,
    ruc: str,
    periodo: str,
) -> Dict[str, Any]:
    """
    Genera (o sobreescribe) el Excel consolidado por empresa/periodo.
    Solo incluye comprobantes con detalle (CPEDetalle).
    """
    q = (
        db.query(RCEPropuestaItem, CPEDetalle, Empresa, CPEEvidencia)
        .join(CPEDetalle, CPEDetalle.propuesta_item_id == RCEPropuestaItem.id)
        .join(Empresa, Empresa.ruc == RCEPropuestaItem.ruc_empresa)
        .outerjoin(CPEEvidencia, CPEEvidencia.propuesta_item_id == RCEPropuestaItem.id)
        .filter(RCEPropuestaItem.ruc_empresa == ruc, RCEPropuestaItem.periodo == periodo)
        .filter(CPEEvidencia.tipo == "XML")
        .order_by(RCEPropuestaItem.id.asc())
    )

    rows: List[Dict[str, Any]] = []
    resumen_rows: List[Dict[str, Any]] = []
    for item, det, emp, ev in q.all():
        rows.extend(_flatten_item(item, emp, det.detalle_json or {}))
        if ev and ev.storage_path and os.path.exists(ev.storage_path):
            resumen_rows.append(_extract_summary(ev.storage_path, item.ruc_empresa, emp.razon_social if emp else None))

    path = _report_path(ruc, periodo)
    df_detalle = pd.DataFrame(
        rows,
        columns=[
            "ruc",
            "razon_social",
            "fecha_emision",
            "tipo_cpe",
            "serie",
            "correlativo",
            "ruc_emisor",
            "razon_social_emisor",
            "detalle",
            "cantidad",
            "valor_unitario_sin_igv",
            "precio_unitario_con_igv",
            "neto_linea_sin_igv",
            "igv_linea",
            "total_linea_con_igv",
        ],
    )
    df_resumen = pd.DataFrame(
        resumen_rows,
        columns=[
            "ffechadoc",
            "ffechaven",
            "ccoddoc",
            "ccoddas",
            "cyeardas",
            "cserie",
            "cnumero",
            "ccodenti",
            "cdesenti",
            "ctipdoc",
            "ccodruc",
            "crazsoc",
            "ccodclas",
            "nbase1",
            "nigv1",
            "nbase2",
            "nigv2",
            "nbase3",
            "nigv3",
            "nina",
            "nisc",
            "nicbper",
            "nexo",
            "ntots",
            "cdocnodom",
            "cnumdere",
            "ffecre",
            "ntc",
            "freffec",
            "crefdoc",
            "crefser",
            "crefnum",
            "cmreg",
            "ndolar",
            "ffechaven2",
        ],
    )

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df_detalle.to_excel(writer, sheet_name="Detalle", index=False)
        df_resumen.to_excel(writer, sheet_name="Resumen", index=False)

    return {"path": path, "rows": len(rows)}
