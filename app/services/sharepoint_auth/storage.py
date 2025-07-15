from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select, delete
from app.services.sharepoint_auth.schemas import SharePointItem, SharePointReassignmentsItem
from app.services.sharepoint_auth.utils import parse_fecha


async def _save_sharepoint_data_to_db(items: list[dict], db: AsyncSession, model):
    # Obtener todos los IDs del API (convertidos a enteros)
    api_ids = {int(item["id"]) for item in items}

    # Guardar o actualizar cada item
    for item in items:
        fields = item.get("fields", {})
        item_id = int(item["id"])

        created = parse_fecha(item.get("createdDateTime"))
        modified = parse_fecha(item.get("lastModifiedDateTime"))

        if created:
            created = created.replace(tzinfo=None)
        if modified:
            modified = modified.replace(tzinfo=None)

        stmt = insert(model).values(
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

    # Obtener todos los IDs existentes en la base de datos
    result = await db.execute(select(model.id))
    db_ids = {row[0] for row in result.fetchall()}

    # Determinar qué IDs eliminar
    ids_to_delete = db_ids - api_ids

    if ids_to_delete:
        stmt = delete(model).where(model.id.in_(ids_to_delete))
        await db.execute(stmt)

    await db.commit()


async def save_items_to_db(items: list[dict], db: AsyncSession):
    await _save_sharepoint_data_to_db(items, db, SharePointItem)


async def save_reassignments_to_db(items: list[dict], db: AsyncSession):
    await _save_sharepoint_data_to_db(items, db, SharePointReassignmentsItem)
