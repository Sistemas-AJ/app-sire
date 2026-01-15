import os
from typing import Dict, Any, List, Optional

import pandas as pd
from sqlalchemy.orm import Session

from core.database import Empresa, RCEPropuestaItem, CPEDetalle
from rce.xml_service.config import REGISTROS_DIR


def _report_path(ruc: str, periodo: str) -> str:
    base_dir = os.path.join(REGISTROS_DIR, "periodos", periodo, ruc, f"reporte_{periodo}")
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, f"reporte_{periodo}.xlsx")


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
        db.query(RCEPropuestaItem, CPEDetalle, Empresa)
        .join(CPEDetalle, CPEDetalle.propuesta_item_id == RCEPropuestaItem.id)
        .join(Empresa, Empresa.ruc == RCEPropuestaItem.ruc_empresa)
        .filter(RCEPropuestaItem.ruc_empresa == ruc, RCEPropuestaItem.periodo == periodo)
        .order_by(RCEPropuestaItem.id.asc())
    )

    rows: List[Dict[str, Any]] = []
    for item, det, emp in q.all():
        rows.extend(_flatten_item(item, emp, det.detalle_json or {}))

    path = _report_path(ruc, periodo)
    df = pd.DataFrame(
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
    df.to_excel(path, index=False)

    return {"path": path, "rows": len(rows)}
