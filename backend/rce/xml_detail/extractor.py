import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from core.database import CPEDetalle


_LINE_TAGS = ("InvoiceLine", "CreditNoteLine", "DebitNoteLine")


def _text(elem: Optional[ET.Element]) -> Optional[str]:
    if elem is None or elem.text is None:
        return None
    t = elem.text.strip()
    return t if t else None


def _dec(val: Optional[str]) -> Optional[str]:
    if val is None:
        return None
    try:
        return str(Decimal(val))
    except InvalidOperation:
        return val


def _find_first(root: ET.Element, path: str) -> Optional[ET.Element]:
    return root.find(path)


def _find_all(root: ET.Element, path: str) -> List[ET.Element]:
    return root.findall(path)


def parse_detalle(xml_path: str) -> Dict[str, Any]:
    """
    Extrae campos mínimos del XML: descripción, cantidad y precio por ítem,
    además de totales y moneda si existen.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    currency = _text(_find_first(root, ".//{*}DocumentCurrencyCode"))
    issue_date = _text(_find_first(root, ".//{*}IssueDate"))

    lines: List[Dict[str, Any]] = []
    line_nodes: List[ET.Element] = []
    for tag in _LINE_TAGS:
        line_nodes.extend(_find_all(root, f".//{{*}}{tag}"))

    for ln in line_nodes:
        desc = _text(_find_first(ln, ".//{*}Description"))
        qty = _text(_find_first(ln, ".//{*}InvoicedQuantity")) or _text(
            _find_first(ln, ".//{*}CreditedQuantity")
        ) or _text(_find_first(ln, ".//{*}DebitedQuantity"))
        unit_value = _text(_find_first(ln, ".//{*}Price/{*}PriceAmount"))
        line_net = _text(_find_first(ln, "./{*}LineExtensionAmount"))
        line_igv = _text(_find_first(ln, "./{*}TaxTotal/{*}TaxAmount"))

        unit_price_igv = None
        for alt in ln.findall(".//{*}PricingReference/{*}AlternativeConditionPrice"):
            code = _text(alt.find("./{*}PriceTypeCode"))
            if code == "01":
                unit_price_igv = _text(alt.find("./{*}PriceAmount"))
                break

        total_line = None
        if line_net and line_igv:
            try:
                total_line = str(Decimal(line_net) + Decimal(line_igv))
            except InvalidOperation:
                total_line = None

        lines.append(
            {
                "description": desc,
                "quantity": _dec(qty),
                "unit_value": _dec(unit_value),
                "unit_price_igv": _dec(unit_price_igv),
                "line_net": _dec(line_net),
                "line_igv": _dec(line_igv),
                "line_total": _dec(total_line),
            }
        )

    total_tax = _text(_find_first(root, ".//{*}TaxTotal/{*}TaxAmount"))
    payable = _text(_find_first(root, ".//{*}LegalMonetaryTotal/{*}PayableAmount"))

    return {
        "issue_date": issue_date,
        "currency": currency,
        "totals": {
            "tax_amount": total_tax,
            "payable_amount": payable,
        },
        "lines": lines,
    }


def save_detalle(
    db: Session,
    propuesta_item_id: int,
    detalle_json: Dict[str, Any],
    source_sha256: Optional[str],
    extractor_version: str = "v1",
) -> CPEDetalle:
    existing = (
        db.query(CPEDetalle)
        .filter(
            CPEDetalle.propuesta_item_id == propuesta_item_id,
            CPEDetalle.extractor_version == extractor_version,
        )
        .first()
    )
    if existing:
        existing.detalle_json = detalle_json
        existing.source_sha256 = source_sha256
        return existing

    row = CPEDetalle(
        propuesta_item_id=propuesta_item_id,
        extractor_version=extractor_version,
        detalle_json=detalle_json,
        source_sha256=source_sha256,
    )
    db.add(row)
    return row
