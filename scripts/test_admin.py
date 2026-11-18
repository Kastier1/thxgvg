import reflex as rx

import asyncio
from uuid import uuid4

from sqlalchemy import delete, select

from thanksgiving_gathering_planner.models import AdminOwner, RecommendedItem, RSVP
from thanksgiving_gathering_planner.states.admin_state import AdminState
from scripts.test_rsvp import RunEvent


async def test_singleton_bootstrap_on_empty_test_database(run_event: RunEvent):
    """Explicit opt-in only: leaves a test owner; do not run on the deployed database."""
    async with rx.asession() as session:
        assert await session.scalar(select(AdminOwner.id)) is None, (
            "Use a fresh disposable test database."
        )
        assert await session.scalar(select(RSVP.id).limit(1)) is None, (
            "Never bootstrap on a database with guests."
        )
    claims = [
        {"sub": f"bootstrap-{uuid4().hex}"},
        {"sub": f"bootstrap-{uuid4().hex}"},
    ]
    results = await asyncio.gather(
        *(
            run_event(AdminState.load_owner(), token=user["sub"], claims=user)
            for user in claims
        )
    )
    assert sum(bool(result["owner_allowed"]) for result in results) == 1
    async with rx.asession() as session:
        owners = (await session.scalars(select(AdminOwner))).all()
        assert len(owners) == 1 and owners[0].id == 1
        assert owners[0].sub in {user["sub"] for user in claims}


async def run_admin_tests(run_event: RunEvent):
    async with rx.asession() as session:
        owner_sub = await session.scalar(
            select(AdminOwner.sub).where(AdminOwner.id == 1)
        )
    assert owner_sub, (
        "Admin tests require an existing owner in a disposable test database."
    )
    prefix = f"Admin test {uuid4().hex}"
    owner = {"sub": owner_sub}
    outsider = {"sub": f"other-{uuid4().hex}"}
    owner_token = f"{prefix}-owner"
    outsider_token = f"{prefix}-other"
    ids: set[int] = set()
    try:
        result = await run_event(
            AdminState.load_owner(), token=outsider_token, claims=outsider
        )
        assert result["owner_ready"] and not result["owner_allowed"]
        await run_event(
            AdminState.create_item({"item_name": prefix}),
            token=outsider_token,
            claims=outsider,
            state={"owner_allowed": True},
        )
        async with rx.asession() as session:
            assert (
                await session.scalar(
                    select(RecommendedItem.id).where(
                        RecommendedItem.name == prefix
                    )
                )
                is None
            )
        result = await run_event(
            AdminState.load_owner(), token=owner_token, claims=owner
        )
        assert result["owner_allowed"]
        for invalid_name in (" ", "x" * 101, "bad\x00", ["forged"]):
            result = await run_event(
                AdminState.create_item({"item_name": invalid_name}),
                token=owner_token,
                claims=owner,
            )
            assert result["error"] and not result["saving"]
        result = await run_event(
            AdminState.create_item({"item_name": f" {prefix} "}),
            token=owner_token,
            claims=owner,
        )
        async with rx.asession() as session:
            item_id = await session.scalar(
                select(RecommendedItem.id).where(
                    RecommendedItem.normalized_name == prefix.casefold()
                )
            )
        assert item_id is not None
        ids.add(item_id)
        result = await run_event(
            AdminState.create_item({"item_name": prefix.upper()}),
            token=owner_token,
            claims=owner,
        )
        assert "already exists" in result["error"]
        await run_event(
            AdminState.begin_edit(item_id), token=owner_token, claims=owner
        )
        renamed = f"{prefix} renamed"
        result = await run_event(
            AdminState.save_name({"edit_name": f" {renamed} "}),
            token=owner_token,
            claims=owner,
        )
        assert not result["error"]
        await run_event(
            AdminState.toggle_item(item_id), token=owner_token, claims=owner
        )
        async with rx.asession() as session:
            item = await session.get(RecommendedItem, item_id)
            assert item.name == renamed and not item.active
        await run_event(
            AdminState.toggle_item(item_id), token=owner_token, claims=owner
        )
        async with rx.asession() as session:
            session.add(
                RSVP(
                    guest_name=prefix,
                    contribution=renamed,
                    recommended_item_id=item_id,
                )
            )
            await session.commit()
        await run_event(
            AdminState.load_items(), token=owner_token, claims=owner
        )
        for event, state in (
            (AdminState.toggle_item(item_id), None),
            (
                AdminState.save_name({"edit_name": "Historical mutation"}),
                {"edit_id": item_id},
            ),
            (AdminState.confirm_remove(), {"remove_id": item_id}),
        ):
            result = await run_event(
                event, token=owner_token, claims=owner, state=state
            )
            assert "claimed" in result["error"]
        async with rx.asession() as session:
            item = await session.get(RecommendedItem, item_id)
            guest = await session.scalar(
                select(RSVP).where(RSVP.recommended_item_id == item_id)
            )
            assert item.name == renamed and guest.contribution == renamed
        await run_event(
            AdminState.create_item({"item_name": f"{prefix} removable"}),
            token=owner_token,
            claims=owner,
        )
        async with rx.asession() as session:
            removable_id = await session.scalar(
                select(RecommendedItem.id).where(
                    RecommendedItem.name == f"{prefix} removable"
                )
            )
        assert removable_id is not None
        ids.add(removable_id)
        await run_event(
            AdminState.ask_remove(removable_id), token=owner_token, claims=owner
        )
        await run_event(
            AdminState.cancel_remove(), token=owner_token, claims=owner
        )
        await run_event(
            AdminState.confirm_remove(), token=owner_token, claims=owner
        )
        async with rx.asession() as session:
            assert await session.get(RecommendedItem, removable_id) is not None
        await run_event(
            AdminState.ask_remove(removable_id), token=owner_token, claims=owner
        )
        await run_event(
            AdminState.confirm_remove(), token=owner_token, claims=owner
        )
        await run_event(
            AdminState.load_items(), token=owner_token, claims=owner
        )
        async with rx.asession() as session:
            assert await session.get(RecommendedItem, removable_id) is None
        await run_event(
            AdminState.load_items(), token=outsider_token, claims=outsider
        )
        async with rx.asession() as session:
            assert (
                await session.scalar(
                    select(AdminOwner.sub).where(AdminOwner.id == 1)
                )
                == owner_sub
            )
    finally:
        async with rx.asession() as session:
            await session.execute(
                delete(RSVP).where(RSVP.recommended_item_id.in_(ids))
            )
            await session.execute(
                delete(RecommendedItem).where(RecommendedItem.id.in_(ids))
            )
            await session.commit()
