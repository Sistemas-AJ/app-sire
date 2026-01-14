import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from core.database import CPEDetalle


_LINE_TAGS = ("InvoiceLine", "CreditNoteLine", "DebitNoteLine")


def _text(elem: Optional[ET.Element]) -> Optional[str]:
    if elem is None or elem.text is None:
        return None
    t = elem.text.strip()
    return t if t else None


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
        price = _text(_find_first(ln, ".//{*}PriceAmount"))
        line_total = _text(_find_first(ln, ".//{*}LineExtensionAmount"))
        lines.append(
            {
                "description": desc,
                "quantity": qty,
                "price": price,
                "line_total": line_total,
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
