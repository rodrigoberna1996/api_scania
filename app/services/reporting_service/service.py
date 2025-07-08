import io
import pandas as pd
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.reporting_service.repository import get_filtered_logs
from app.services.sharepoint_auth.ms_graph import leer_excel_desde_onedrive
from openpyxl import load_workbook, Workbook
from openpyxl.styles import PatternFill

async def generate_excel_report(session: AsyncSession):
    # Paso 1: Obtener datos del viaje
    records = await get_filtered_logs(session)
    data = [row.fields for row in records]
    df = pd.DataFrame(data)

    # Paso 1.5: Eliminar columna innecesaria si existe
    if "@odata.etag" in df.columns:
        df = df.drop(columns=["@odata.etag"])

    # Paso 2: Renombrar columnas necesarias para unir
    df = df.rename(columns={
        "field_6": "fecha_carga",
        "field_16": "fecha_descarga",
        "field_1": "No. Económico",
        "field_7": "hora_carga",
        "field_17": "hora_descarga",
        "Title": "Title"
    })

    df["No. Económico"] = df["No. Económico"].apply(lambda x: f"ECO {x}")
    df["fecha_carga"] = pd.to_datetime(df["fecha_carga"], dayfirst=True, errors="coerce")
    df["fecha_descarga"] = pd.to_datetime(df["fecha_descarga"], dayfirst=True, errors="coerce")

    # Paso 3: Leer archivo de peajes desde OneDrive
    peajes_df = await leer_excel_desde_onedrive("Peajes.xlsx")
    peajes_df = peajes_df.iloc[8:]
    peajes_df["Fecha"] = pd.to_datetime(peajes_df["Fecha"], dayfirst=True, errors="coerce")
    peajes_df["No. Económico"] = peajes_df["No. Económico"].str.strip()
    peajes_df["Costo final"] = pd.to_numeric(peajes_df["Costo final"], errors="coerce")

    # Paso 4: Calcular el costo de peajes
    def calcular_costo_peajes(fila):
        eco = fila["No. Económico"]
        fecha_ini = fila["fecha_carga"]
        fecha_fin = fila["fecha_descarga"]
        hora_ini = fila["hora_carga"]
        hora_fin = fila["hora_descarga"]

        try:
            inicio_dt = pd.to_datetime(f"{fecha_ini.date()} {hora_ini}")
            fin_dt = pd.to_datetime(f"{fecha_fin.date()} {hora_fin}")
        except Exception:
            return 0

        peajes_filtrados = peajes_df[
            (peajes_df["No. Económico"] == eco) &
            (peajes_df["Fecha"] >= inicio_dt) &
            (peajes_df["Fecha"] <= fin_dt)
        ]
        return peajes_filtrados["Costo final"].sum()

    df["PEAJES VIAPASS"] = (df.apply(calcular_costo_peajes, axis=1) / 1.16).round(2)
    df["PEAJES EFECTIVO SIN IVA"] = (df["PEAJES_EFECTIVO"].fillna(0).astype(float) / 1.16).round(2)
    df["Costo Total Peajes"] = (df["PEAJES VIAPASS"] + df["PEAJES EFECTIVO SIN IVA"]).round(2)

    # Paso 4.5: Ordenar por ECO y fecha
    df["eco_num"] = df["No. Económico"].str.replace("ECO ", "").astype(int)
    df = df.sort_values(by=["eco_num", "fecha_carga"], ascending=[True, True])
    df = df.drop(columns=["eco_num"])

    # Paso 4.6: Renombrar columnas finales
    mapeo_columnas = {
        "Title": "TR_NO_VIAJE",
        "No. Económico": "NO_TRACTO",
        "field_2": "PLACAS_TRACTO",
        "NO_REMOLQUE": "NO_REMOLQUE",
        "field_3": "PLACAS_REMOLQUE",
        "field_4": "NOMBRE_OP",
        "ORIGEN_TAB": "ORIGEN",
        "DESTINO_TAB": "DESTINO",
        "field_8": "CLIENTE",
        "field_9": "EMPRESA",
        "CARGA_KILOS": "CARGA_KILOS",
        "field_22": "ADRH_OT",
        "fecha_carga": "FECHA_CARGA",
        "hora_carga": "HORA_CARGA",
        "fecha_descarga": "FECHA_DESCARGA",
        "hora_descarga": "HORA_DESCARGA",
        "REPARTOS1": "REPARTOS",
        "field_19": "MANIOBRAS",
        "field_20": "ESTADIAS",
        "field_15": "COSTO_VIAJE",
        "COMISION_CLIENTE": "COMISION_CLIENTE",
        "COMISION_OPERADOR": "COMISION_OPERADOR",
        "GASTOS_OPERADOR": "GASTOS_OPERADOR",
        "PEAJES EFECTIVO SIN IVA": "PEAJES_EFECTIVO",
        "PEAJES VIAPASS": "PEAJES_VIAPASS",
        "Costo Total Peajes": "TOTAL_PEAJES"
    }

    df = df.rename(columns=mapeo_columnas)

    # Paso 4.7: Reordenar columnas
    columnas_orden = [
        "TR_NO_VIAJE", "NO_TRACTO", "PLACAS_TRACTO", "NO_REMOLQUE", "PLACAS_REMOLQUE", "NOMBRE_OP",
        "ORIGEN", "DESTINO", "CLIENTE", "EMPRESA", "CARGA_KILOS", "ADRH_OT", "FECHA_CARGA", "HORA_CARGA",
        "FECHA_DESCARGA", "HORA_DESCARGA", "REPARTOS", "MANIOBRAS", "ESTADIAS", "FLETE_VACIO",
        "FLETE_FALSO", "RECHAZOS", "COSTO_VIAJE", "KM_RECORRIDOS", "CONSUMO_LTS_DIESEL", "RENDIMIENTO",
        "PRECIO_DIESEL", "COSTO_DIESEL", "LTS_ADBLUE_CONSUMIDOS", "PRECIO_ADBLUE", "COSTO_ADBLUE",
        "COMISION_CLIENTE", "COMISION_OPERADOR", "GASTOS_OPERADOR", "PEAJES_EFECTIVO", "PEAJES_VIAPASS",
        "TOTAL_PEAJES", "MANTTO_TRACTOS", "MANTTO_CAJAS", "RASTREO", "SEGURO", "LLANTAS",
        "ADMINISTRACION", "MARKETING", "COSTO_TOTAL", "UTILIDAD_BRUTA", "INGRESO_X_KM", "COSTO_X_KM", "UTILIDAD_X_KM"
    ]

    for col in columnas_orden:
        if col not in df.columns:
            df[col] = ""

    df = df[columnas_orden]

    # Paso 5: Exportar a Excel (sin formato aún)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Reporte")

    # Paso 6: Insertar fila vacía después de cada fila de datos
    output.seek(0)
    wb_original = load_workbook(output)
    ws_original = wb_original["Reporte"]

    wb_final = Workbook()
    ws_final = wb_final.active
    ws_final.title = "Reporte"

    # Copiar encabezados
    for col_idx, cell in enumerate(ws_original[1], start=1):
        ws_final.cell(row=1, column=col_idx, value=cell.value)

    gris_fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
    new_row_idx = 2

    for row in ws_original.iter_rows(min_row=2, max_row=ws_original.max_row):
        for col_idx, cell in enumerate(row, start=1):
            new_cell = ws_final.cell(row=new_row_idx, column=col_idx, value=cell.value)
            new_cell.fill = gris_fill
        new_row_idx += 1  # siguiente fila para vacío
        new_row_idx += 1

    # Paso 7: Guardar y responder
    final_output = io.BytesIO()
    wb_final.save(final_output)
    final_output.seek(0)

    return StreamingResponse(
        final_output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=report.xlsx"},
    )
