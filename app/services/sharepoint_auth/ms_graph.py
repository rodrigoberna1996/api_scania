# app/services/sharepoint_auth/ms_graph.py
# ────────────────────────────────────────
import httpx, pandas as pd
from io import BytesIO
from app.services.sharepoint_auth.client import SharePointClient

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
DRIVE_ID      = "b!o7HBJ3ipyEKwjcpneGiAzvmjvnw6bvxEivisl_xxW0D4hiM1LaJ1R6_tdoRCxYUe"
PLANTILLA_COSTOS_FOLDER_ID = "01USEHRLUQN5OQ4PLCZFEZTMUB2DIWLQLG"

sharepoint_client = SharePointClient()

# ➊  NUEVO parámetro header_row  (por defecto = 8 para Peajes)
async def leer_excel_desde_onedrive(
    nombre_archivo: str,
    *,
    header_row: int = 8,
    sheet_name: str | int = 0,
) -> pd.DataFrame:
    """
    Descarga un Excel de la carpeta Plantilla Costos y lo devuelve como DataFrame.
    • header_row = número (0-based) de la fila que contiene los encabezados.
    """
    token   = await sharepoint_client.get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        url_list  = f"{GRAPH_BASE_URL}/drives/{DRIVE_ID}/items/{PLANTILLA_COSTOS_FOLDER_ID}/children"
        res       = await client.get(url_list, headers=headers)
        res.raise_for_status()

        archivo = next((a for a in res.json().get("value", []) if a["name"] == nombre_archivo), None)
        if not archivo:
            raise FileNotFoundError(f"No se encontró el archivo: {nombre_archivo}")

        url_download = f"{GRAPH_BASE_URL}/drives/{DRIVE_ID}/items/{archivo['id']}/content"
        res          = await client.get(url_download, headers=headers, follow_redirects=True)
        res.raise_for_status()

        df = pd.read_excel(
            BytesIO(res.content),
            header=header_row,
            sheet_name=sheet_name,
        )

        # pd.read_excel devuelve un dict si sheet_name=None; garantizamos
        # retornar siempre un DataFrame usando la primera hoja si es el caso
        if isinstance(df, dict):
            df = next(iter(df.values()))

        df.columns = df.columns.str.strip()  # quita espacios
        return df


# Helper específico para Diesel.xlsx
async def leer_diesel_desde_onedrive(nombre_archivo: str = "Diesel.xlsx") -> pd.DataFrame:
    """Descarga Diesel.xlsx y calcula PRECIO_DIESEL y COSTO_DIESEL."""
    df = await leer_excel_desde_onedrive(nombre_archivo, header_row=4)
    df.columns = df.columns.str.strip()

    # Normaliza nombres esperados
    if "Precio" not in df.columns or "Lts" not in df.columns:
        raise RuntimeError(f"Columnas Diesel inesperadas: {df.columns.tolist()}")

    df["Precio"] = pd.to_numeric(df["Precio"], errors="coerce")
    df["Lts"] = pd.to_numeric(df["Lts"], errors="coerce")

    df["PRECIO_DIESEL"] = (df["Precio"] / 1.16).round(2)
    df["COSTO_DIESEL"] = (df["PRECIO_DIESEL"] * df["Lts"]).round(2)
    return df


# Helper para obtener factores de mantenimiento
async def leer_factores_desde_onedrive(
    nombre_archivo: str = "Factores.xlsx",
    hoja: str = "Data1",
) -> pd.DataFrame:
    """Descarga Factores.xlsx y devuelve la hoja especificada como DataFrame."""
    df = await leer_excel_desde_onedrive(
        nombre_archivo,
        header_row=1,
        sheet_name=hoja,
    )
    df.columns = df.columns.str.strip()

    if not {"Rango1", "Rango2", "Factor"}.issubset(df.columns):
        raise RuntimeError(f"Columnas Factores inesperadas: {df.columns.tolist()}")

    df["Rango1"] = (
        df["Rango1"].replace("-", 0).astype(str).str.replace(",", "")
    )
    df["Rango2"] = df["Rango2"].astype(str).str.replace(",", "")
    for col in ["Rango1", "Rango2", "Factor"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Factor"]).reset_index(drop=True)
    return df
