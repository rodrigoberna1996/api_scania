import httpx
import pandas as pd
from io import BytesIO
from app.services.sharepoint_auth.client import SharePointClient

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
DRIVE_ID = "b!o7HBJ3ipyEKwjcpneGiAzvmjvnw6bvxEivisl_xxW0D4hiM1LaJ1R6_tdoRCxYUe"
PLANTILLA_COSTOS_FOLDER_ID = "01USEHRLUQN5OQ4PLCZFEZTMUB2DIWLQLG"  # Carpeta Plantilla Costos

sharepoint_client = SharePointClient()

async def leer_excel_desde_onedrive(nombre_archivo: str) -> pd.DataFrame:
    token = await sharepoint_client.get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        url_list = f"{GRAPH_BASE_URL}/drives/{DRIVE_ID}/items/{PLANTILLA_COSTOS_FOLDER_ID}/children"
        res = await client.get(url_list, headers=headers)
        res.raise_for_status()
        archivos = res.json().get("value", [])

        archivo = next((a for a in archivos if a["name"] == nombre_archivo), None)
        if not archivo:
            raise FileNotFoundError(f"No se encontró el archivo: {nombre_archivo}")

        file_id = archivo["id"]
        url_download = f"{GRAPH_BASE_URL}/drives/{DRIVE_ID}/items/{file_id}/content"
        res = await client.get(url_download, headers=headers, follow_redirects=True)
        res.raise_for_status()

        df = pd.read_excel(BytesIO(res.content), header=8)
        df.columns = df.columns.str.strip()  # limpia espacios

        print("Columnas en Excel:", df.columns.tolist())  # Debug columnas

        return df
