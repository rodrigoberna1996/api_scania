from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from app.db.model_list import SharePointItem
from app.services.sharepoint_auth.utils import parse_fecha


async def save_items_to_db(items: list[dict], db: AsyncSession):
    for item in items:
        fields = item.get("fields", {})
        item_id = int(item["id"])

        # Convertimos fechas usando tu util
        created_str = item.get("createdDateTime")
        modified_str = item.get("lastModifiedDateTime")

        created = parse_fecha(created_str)
        modified = parse_fecha(modified_str)

        # Quitamos tzinfo si lo tienen, para que encaje con TIMESTAMP WITHOUT TIME ZONE
        if created:
            created = created.replace(tzinfo=None)
        if modified:
            modified = modified.replace(tzinfo=None)

        stmt = insert(SharePointItem).values(
            id=item_id,
            fields=fields,
            created_at=created,
            modified_at=modified,
        ).on_conflict_do_update(
            index_elements=["id"],
            set_={
                "fields": fields,
                "created_at": created,
                "modified_at": modified,
            }
        )
        await db.execute(stmt)
    await db.commit()