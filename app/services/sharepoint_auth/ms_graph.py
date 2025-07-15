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
async def leer_excel_desde_onedrive(nombre_archivo: str, *, header_row: int = 8) -> pd.DataFrame:
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

        df = pd.read_excel(BytesIO(res.content), header=header_row)
        df.columns = df.columns.str.strip()              # quita espacios
        return df
