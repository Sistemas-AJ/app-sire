# Documentación API (EndPoints Nuevos)

Este documento describe solo los endpoints agregados recientemente para integrar **Propuestas SIRE** y **XML Scraping**, además del sub‑endpoint de credenciales de empresa.

---

## 1) Empresas – Credenciales SOL/SIRE

### POST `/empresas/{ruc}/credenciales`
Actualiza credenciales SOL y/o SIRE para una empresa existente.

**Body (JSON)**
```json
{
  "usuario_sol": "ONEVERRU",
  "clave_sol": "imcSAC2023",
  "sire_client_id": "client-id",
  "sire_client_secret": "client-secret",
  "activo": true
}
```

**Respuesta**
```json
{
  "ok": true,
  "ruc": "20601080428",
  "has_sol": true,
  "has_sire": true
}
```

**Notas**
- Si se envía `sire_client_id`, también debe enviarse `sire_client_secret`.
- Para SIRE se requiere `usuario_sol` (para construir username `ruc + usuario_sol`).

**Código relacionado**
- `backend/api/routers/empresas.py`
- `backend/api/schemas.py`
- `backend/core/database.py` (tabla `empresas_sire`)

---

## 2) Propuesta SIRE

### POST `/propuesta/run`
Genera y descarga la propuesta SIRE para un periodo. Permite una empresa (`ruc`) o un grupo (`rucs`).

**Body (JSON)**
```json
{
  "periodo": "202512",
  "fec_ini": "2025-01-01",
  "fec_fin": "2025-12-31",
  "ruc": "20601080428"
}
```

**Body para grupo**
```json
{
  "periodo": "202512",
  "fec_ini": "2025-01-01",
  "fec_fin": "2025-12-31",
  "rucs": ["20601080428", "20529929821"]
}
```

**Respuesta**
```json
{
  "ok": true,
  "results": [
    {
      "ruc": "20601080428",
      "periodo": "202512",
      "ticket": "20250300000106",
      "csv": "/app/registros/periodos/202512/20601080428/xxx.csv",
      "xlsx": "/app/registros/periodos/202512/20601080428/propuesta_202512.xlsx",
      "zip": "/app/registros/periodos/202512/20601080428/xxx.zip"
    }
  ],
  "errors": []
}
```

**Notas**
- La propuesta se descarga y guarda CSV/XLSX automáticamente.
- El proceso es idempotente: si ya existe, actualiza el registro de archivo.

**Código relacionado**
- `backend/api/routers/propuesta.py`
- `backend/rce/propuesta/run.py`
- `backend/rce/propuesta/file_ops.py`
- `backend/rce/propuesta/load_items.py`
- `backend/core/database.py` (`rce_propuesta_files`, `rce_propuesta_items`)

---

### GET `/propuesta/status`
Devuelve el estado del archivo de propuesta para una empresa/periodo.

**Query**
```
?ruc=20601080428&periodo=202512
```

**Respuesta**
```json
{
  "ruc_empresa": "20601080428",
  "periodo": "202512",
  "num_ticket": "20250300000106",
  "cod_proceso": "XXXX",
  "storage_path": "/app/registros/periodos/202512/20601080428",
  "filename": "xxx.zip",
  "sha256": "....",
  "created_at": "2025-01-14T00:00:00Z"
}
```

**Código relacionado**
- `backend/api/routers/propuesta.py`
- `backend/core/database.py` (`RCEPropuestaFile`)

---

### GET `/propuesta/items`
Lista comprobantes (items) de una propuesta.

**Query**
```
?ruc=20601080428&periodo=202512&limit=200&offset=0
```

**Respuesta**
```json
[
  {
    "id": 123,
    "ruc_empresa": "20601080428",
    "periodo": "202512",
    "tipo_cp": "01",
    "serie": "F001",
    "numero": "100286",
    "ruc_emisor": "20526422300",
    "razon_emisor": "EMPRESA SA",
    "fecha_emision": "2025-12-31",
    "total_cp": 15600.0,
    "moneda": "PEN"
  }
]
```

**Código relacionado**
- `backend/api/routers/propuesta.py`
- `backend/core/database.py` (`RCEPropuestaItem`)

---

## 3) XML Scraping

### POST `/xml/run`
Descarga XMLs para un periodo y empresa(s). Permite una empresa (`ruc`) o un grupo (`rucs`).  
Si `limit` es `null` u omitido, no hay límite.

**Body (JSON)**
```json
{
  "periodo": "202512",
  "ruc": "20529929821",
  "headless": true
}
```

**Body para grupo sin límite**
```json
{
  "periodo": "202512",
  "rucs": ["20529929821", "20601080428"],
  "limit": null,
  "headless": true
}
```

**Respuesta**
```json
{
  "ok": true,
  "processed_rucs": ["20529929821"],
  "errors": []
}
```

**Código relacionado**
- `backend/api/routers/xml_service.py`
- `backend/rce/xml_service/job.py`
- `backend/rce/xml_service/scraper.py`

---

### GET `/xml/pending`
Lista items pendientes de XML para una empresa y periodo.

**Query**
```
?ruc=20529929821&periodo=202512&limit=200
```

**Código relacionado**
- `backend/api/routers/xml_service.py`
- `backend/rce/xml_service/repository.py`

---

### GET `/xml/evidencias`
Lista evidencias XML (OK/ERROR/NOT_FOUND/AUTH) por empresa y periodo.

**Query**
```
?ruc=20529929821&periodo=202512&status=ERROR
```

**Código relacionado**
- `backend/api/routers/xml_service.py`
- `backend/core/database.py` (`CPEEvidencia`)

---

### GET `/xml/detalle`
Devuelve el detalle extraído (items y totales) para un comprobante.

**Query**
```
?item_id=123&extractor_version=v1
```

**Código relacionado**
- `backend/api/routers/xml_service.py`
- `backend/rce/xml_detail/extractor.py`
- `backend/core/database.py` (`CPEDetalle`)

---

### GET `/xml/progress`
Endpoint para progreso en tiempo real (polling).

**Query**
```
?ruc=20529929821&periodo=202512
```

**Respuesta**
```json
{
  "ruc": "20529929821",
  "periodo": "202512",
  "total_items": 120,
  "total_evidencias": 110,
  "ok": 90,
  "error": 5,
  "not_found": 10,
  "auth": 1,
  "pending": 4,
  "remaining": 20
}
```

**Código relacionado**
- `backend/api/routers/xml_service.py`
- `backend/core/database.py` (`RCEPropuestaItem`, `CPEEvidencia`)

