import reflex as rx

from sqlalchemy.dialects.postgresql import insert

from thanksgiving_gathering_planner.models import RecommendedItem


async def seed_default_recommendations_once() -> int:
    """Orchestrator-only initial content setup; never call on load or startup."""
    names = (
        "Mashed potatoes",
        "Stuffing",
        "Cranberry sauce",
        "Green beans",
        "Veggies",
        "Dinner rolls & butter",
        "Pie",
        "Non-alcoholic drinks",
        "Beer",
        "Spirits",
    )
    async with rx.asession() as session:
        result = await session.execute(
            insert(RecommendedItem)
            .values(
                [
                    {
                        "name": name,
                        "normalized_name": name.casefold(),
                        "active": True,
                    }
                    for name in names
                ]
            )
            .on_conflict_do_nothing(
                index_elements=[RecommendedItem.normalized_name]
            )
            .returning(RecommendedItem.id)
        )
        inserted = len(result.scalars().all())
        await session.commit()
        return inserted
