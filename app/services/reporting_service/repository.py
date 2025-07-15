from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def get_filtered_logs(session: AsyncSession):
    query = text("""
        SELECT * FROM travel_log
        WHERE fields::jsonb ? 'field_16'
          AND fields::jsonb ? 'field_17'
          AND (fields->>'F_CARGA_YEAR')::int = EXTRACT(YEAR FROM NOW())::int
        ORDER BY created_at DESC
    """)
    result = await session.execute(query)
    return result.fetchall()

async def get_reassignment_by_title(session: AsyncSession, title: str):
    query = text("""
        SELECT * FROM reassignments
        WHERE (fields->>'viaje_id') = :title
        LIMIT 1
    """)
    result = await session.execute(query, {"title": title})
    return result.fetchone()
