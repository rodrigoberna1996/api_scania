import httpx

from app.db.session import AsyncSessionLocal
from app.services.sharepoint_auth.client import SharePointClient
from app.services.sharepoint_auth.storage import save_items_to_db, save_reassignments_to_db


async def refresh_sharepoint_token():
    client = SharePointClient()
    token_data = await client.get_token_from_api()
    token = token_data.get("access_token")
    expires_in = int(token_data.get("expires_in", 3590))
    await client.store_token(token, expires_in)


async def fetch_sharepoint_list_items(token: str, url: str) -> list:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as http_client:
        items = []
        next_url = url
        while next_url:
            resp = await http_client.get(next_url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            items.extend(data.get("value", []))
            next_url = data.get("@odata.nextLink")
        return items


async def update_sharepoint_items():
    client = SharePointClient()
    token = await client.get_access_token()

    url = (
        "https://graph.microsoft.com/v1.0/sites/truiz.sharepoint.com,"
        "a0d38210-52a9-4619-a001-fdde7017c0cc,"
        "7cbea3f9-6e3a-44fc-8af8-ac97fc715b40/"
        "lists/bdb21716-0291-4959-afb7-f801ac9983c5/items?$expand=fields"
    )

    items = await fetch_sharepoint_list_items(token, url)

    async with AsyncSessionLocal() as session:
        await save_items_to_db(items, session)


async def update_sharepoint_reassignments():
    client = SharePointClient()
    token = await client.get_access_token()

    url = (
        "https://graph.microsoft.com/v1.0/sites/truiz.sharepoint.com,"
        "a0d38210-52a9-4619-a001-fdde7017c0cc,"
        "7cbea3f9-6e3a-44fc-8af8-ac97fc715b40/"
        "lists/b135641e-4e6d-4178-9f37-7c68c27f7558/items?$expand=fields"
    )

    items = await fetch_sharepoint_list_items(token, url)

    async with AsyncSessionLocal() as session:
        await save_reassignments_to_db(items, session)
