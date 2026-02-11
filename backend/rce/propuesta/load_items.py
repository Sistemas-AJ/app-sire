import csv
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Tuple, Optional

from sqlalchemy.orm import Session
from core.database import RCEPropuestaItem

# RUCs con CSV SUNAT "especial": la razón social del comprador puede venir con
# comas sin comillas, desplazando columnas.
SPECIAL_FULL_ROW_RUCS = {
    "10411619830",
}


def _parse_date(d: str) -> Optional[date]:
    d = (d or "").strip()
    if not d:
        return None
    # Formato típico del CSV: 1/12/2025
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(d, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Fecha inválida: {d}")


def _parse_decimal(x: str) -> Optional[Decimal]:
    x = (x or "").strip()
    if x == "" or x.lower() == "null":
        return None
    try:
        # CSV suele venir con punto decimal.
        return Decimal(x)
    except InvalidOperation:
        raise ValueError(f"Decimal inválido: {x}")


def _norm_str(x: str) -> Optional[str]:
    x = (x or "").strip()
    return x if x != "" else None


def _item_key(row: Dict[str, Any]) -> Tuple[str, str, str, str, str, str, date]:
    return (
        row["ruc_empresa"],
        row["periodo"],
        row["ruc_emisor"],
        row["tipo_cp"],
        row["serie"],
        row["numero"],
        row["fecha_emision"],
    )


def load_rce_items_from_csv(
    db: Session,
    ruc_empresa: str,
    periodo: str,
    csv_path: str,
    delimiter: str = ",", # CORRECCIÓN: Default a coma según tu data
    update_on_conflict: bool = True,
) -> dict:
    inserted = 0
    updated = 0
    skipped = 0
    errors = 0
    seen_keys = set()

    def _iter_rows():
        # Caso normal
        if ruc_empresa not in SPECIAL_FULL_ROW_RUCS:
            with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                if not reader.fieldnames:
                    raise ValueError("CSV vacío o sin encabezados (sin compras en el periodo).")
                reader.fieldnames = [name.strip() for name in reader.fieldnames]
                for i, r in enumerate(reader, start=2):
                    yield i, r
            return

        # Caso especial: parseo por filas completo y recomposición de columnas.
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
            raw = csv.reader(f, delimiter=delimiter, quoting=csv.QUOTE_NONE)
            try:
                headers = [h.strip() for h in next(raw)]
            except StopIteration:
                raise ValueError("CSV vacío o sin encabezados (sin compras en el periodo).")

            hlen = len(headers)
            for i, cols in enumerate(raw, start=2):
                if not cols:
                    continue
                if len(cols) > hlen:
                    # Junta el exceso dentro de la columna 2 (razón social comprador).
                    extra = len(cols) - hlen
                    merged = ", ".join([c.strip() for c in cols[1 : 2 + extra] if c is not None and c.strip() != ""])
                    cols = [cols[0], merged] + cols[2 + extra :]
                if len(cols) < hlen:
                    cols = cols + [""] * (hlen - len(cols))
                elif len(cols) > hlen:
                    cols = cols[:hlen]
                yield i, dict(zip(headers, cols))

    for i, r in _iter_rows():
            try:
                # Mapeo usando los nombres EXACTOS de tu CSV de muestra
                fecha_emision = _parse_date(r.get("Fecha de emisión"))
                
                # Validación crítica antes de procesar
                if not fecha_emision:
                    # Si no hay fecha, es una fila corrupta o vacía
                    raise ValueError("Fecha de emisión vacía o inválida")

                # NOTA: En r.get usa el string exacto. Si limpiamos fieldnames arriba, 
                # asegúrate que aquí no tengan espacios extra al inicio/final.
                item_data = dict(
                    ruc_empresa=ruc_empresa,
                    periodo=periodo,
                    vigente=True,
                    car_sunat=_norm_str(r.get("CAR SUNAT")),
                    fecha_emision=fecha_emision,
                    fecha_vcto_pago=_parse_date(r.get("Fecha Vcto/Pago")),
                    
                    # Cuidado con los nombres exactos:
                    tipo_cp=_norm_str(r.get("Tipo CP/Doc.")) or "",
                    serie=_norm_str(r.get("Serie del CDP")) or "",
                    numero=_norm_str(r.get("Nro CP o Doc. Nro Inicial (Rango)")) or "",
                    
                    tipo_doc_identidad=_norm_str(r.get("Tipo Doc Identidad")),
                    ruc_emisor=_norm_str(r.get("Nro Doc Identidad")) or "",
                    
                    # Aquí el CSV original tenía un doble espacio posible. 
                    # Al usar reader.fieldnames = [x.strip()...] se arreglan los bordes, 
                    # pero el doble espacio interno se mantiene. Copia exacta:
                    razon_emisor=_norm_str(r.get("Apellidos Nombres/ Razón  Social") or r.get("Apellidos Nombres/ Razón Social")), 

                    bi_gravado_dg=_parse_decimal(r.get("BI Gravado DG")),
                    igv_dg=_parse_decimal(r.get("IGV / IPM DG")),
                    bi_gravado_dgng=_parse_decimal(r.get("BI Gravado DGNG")),
                    igv_dgng=_parse_decimal(r.get("IGV / IPM DGNG")),
                    bi_gravado_dng=_parse_decimal(r.get("BI Gravado DNG")),
                    igv_dng=_parse_decimal(r.get("IGV / IPM DNG")),
                    valor_adq_ng=_parse_decimal(r.get("Valor Adq. NG")),
                    isc=_parse_decimal(r.get("ISC")),
                    icbper=_parse_decimal(r.get("ICBPER")),
                    otros_trib=_parse_decimal(r.get("Otros Trib/ Cargos")),
                    total_cp=_parse_decimal(r.get("Total CP")),

                    moneda=_norm_str(r.get("Moneda")) or "PEN",
                    tipo_cambio=_parse_decimal(r.get("Tipo de Cambio")),

                    detraccion=_norm_str(r.get("Detracción")),
                    est_comp=_norm_str(r.get("Est. Comp.")),
                    incal=_norm_str(r.get("Incal")),
                    # clasif_bss_sss=_norm_str(r.get("Clasif de Bss y Sss")), # A veces no viene

                    raw_json=dict(r), 
                )

                # Validaciones mínimas de integridad
                if not item_data["ruc_emisor"] or not item_data["serie"]:
                     # A veces SUNAT manda filas de resumen o vacías al final
                     continue 

                # --- Lógica de Base de Datos (Idéntica a la tuya) ---
                # NOTA DE RENDIMIENTO: Si cargas 10,000 filas, hacer query().first() por cada una es LENTO.
                # Para archivos grandes se recomienda "Bulk Upsert". Para < 2000 filas, esto está bien.
                existing = (
                    db.query(RCEPropuestaItem)
                    .filter(
                        RCEPropuestaItem.ruc_empresa == item_data["ruc_empresa"],
                        RCEPropuestaItem.periodo == item_data["periodo"],
                        RCEPropuestaItem.ruc_emisor == item_data["ruc_emisor"],
                        RCEPropuestaItem.tipo_cp == item_data["tipo_cp"],
                        RCEPropuestaItem.serie == item_data["serie"],
                        RCEPropuestaItem.numero == item_data["numero"],
                    )
                    .first()
                )

                if existing is None:
                    db.add(RCEPropuestaItem(**item_data))
                    inserted += 1
                    seen_keys.add(_item_key(item_data))
                else:
                    if update_on_conflict:
                        for k, v in item_data.items():
                            setattr(existing, k, v)
                        existing.vigente = True
                        updated += 1
                        seen_keys.add(_item_key(item_data))
                    else:
                        skipped += 1

            except Exception as e:
                errors += 1
                print(f"⚠️ Error en fila CSV {i}: {e}")

    # Marcar como no vigentes los items que ya no están en el CSV
    if seen_keys:
        rows = (
            db.query(
                RCEPropuestaItem.id,
                RCEPropuestaItem.ruc_empresa,
                RCEPropuestaItem.periodo,
                RCEPropuestaItem.ruc_emisor,
                RCEPropuestaItem.tipo_cp,
                RCEPropuestaItem.serie,
                RCEPropuestaItem.numero,
                RCEPropuestaItem.fecha_emision,
            )
            .filter(RCEPropuestaItem.ruc_empresa == ruc_empresa, RCEPropuestaItem.periodo == periodo)
            .all()
        )
        for row in rows:
            key = (
                row.ruc_empresa,
                row.periodo,
                row.ruc_emisor,
                row.tipo_cp,
                row.serie,
                row.numero,
                row.fecha_emision,
            )
            if key not in seen_keys:
                db.query(RCEPropuestaItem).filter(RCEPropuestaItem.id == row.id).update(
                    {"vigente": False}, synchronize_session=False
                )

    db.commit()
    return {"inserted": inserted, "updated": updated, "skipped": skipped, "errors": errors}
