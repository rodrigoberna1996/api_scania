# app/services/sharepoint/jobs.py

from app.services.sharepoint.client import SharePointClient

async def refresh_sharepoint_token():
    client = SharePointClient()
    token_data = await client.get_token_from_api()
    token = token_data.get("access_token")
    expires_in = int(token_data.get("expires_in", 3590))
    await client.store_token(token, expires_in)
