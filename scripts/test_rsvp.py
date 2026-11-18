import reflex as rx

import asyncio
from typing import Protocol
from uuid import uuid4

from sqlalchemy import delete, select

from thanksgiving_gathering_planner.models import RSVP, RecommendedItem
from thanksgiving_gathering_planner.states.rsvp_state import CLAIM_ERROR, NOTHING, RSVPState


class RunEvent(Protocol):
    async def __call__(
        self,
        event: rx.event.EventSpec,
        *,
        token: str,
        state: dict[str, object] | None = None,
        claims: dict[str, str] | None = None,
    ) -> dict[str, object]:
        """Dispatch through the app; return final flattened state after chained events."""
        ...


async def test_public_validation(run_event: RunEvent):
    token = f"validation-{uuid4().hex}"
    result = await run_event(
        RSVPState.select_contribution("custom"), token=token
    )
    assert result["selection"] == "custom"
    result = await run_event(
        RSVPState.select_contribution("invented"), token=token
    )
    assert result["selection"] == "custom" and result["error"]
    for form_data in (
        {"guest_name": "  ", "custom_text": "Beans"},
        {"guest_name": "x" * 101, "custom_text": "Beans"},
        {"guest_name": "Guest", "custom_text": " "},
        {"guest_name": "Guest", "custom_text": "x" * 201},
        {"guest_name": ["forged"], "custom_text": "Beans"},
        {"guest_name": "Guest\x00", "custom_text": "Beans"},
    ):
        result = await run_event(RSVPState.submit_rsvp(form_data), token=token)
        assert (
            result["error"] and not result["saving"] and not result["submitted"]
        )
    result = await run_event(
        RSVPState.select_contribution(NOTHING),
        token=token,
        state={"saving": True},
    )
    assert result["selection"] == "custom"


async def test_write_in_nothing_and_duplicate_guard(run_event: RunEvent):
    prefix = f"Event test {uuid4().hex}"
    names = [f"{prefix} custom", f"{prefix} nothing"]
    try:
        for index, choice in enumerate(("custom", NOTHING)):
            token = f"{prefix}-{index}"
            await run_event(RSVPState.select_contribution(choice), token=token)
            result = await run_event(
                RSVPState.submit_rsvp(
                    {
                        "guest_name": f" {names[index]} ",
                        "custom_text": " Beans ",
                    }
                ),
                token=token,
            )
            assert result["submitted"] and result["saved_name"] == names[index]
            assert result["saved_contribution"] == (
                "Beans" if choice == "custom" else NOTHING
            )
            await run_event(
                RSVPState.submit_rsvp({"guest_name": names[index]}), token=token
            )
            async with rx.asession() as session:
                rows = (
                    await session.scalars(
                        select(RSVP).where(RSVP.guest_name == names[index])
                    )
                ).all()
                assert len(rows) == 1 and rows[0].recommended_item_id is None
            result = await run_event(RSVPState.new_response(), token=token)
            assert not result["submitted"] and result["guest_name"] == ""
            assert "recommendations" in result
    finally:
        async with rx.asession() as session:
            await session.execute(
                delete(RSVP).where(RSVP.guest_name.in_(names))
            )
            await session.commit()


async def test_atomic_reservation(run_event: RunEvent):
    prefix = f"Reservation test {uuid4().hex}"
    async with rx.asession() as session:
        item = RecommendedItem(name=prefix, normalized_name=prefix.casefold())
        session.add(item)
        await session.commit()
        item_id = item.id
    names = [f"{prefix} A", f"{prefix} B"]
    tokens = [f"{prefix}-A", f"{prefix}-B"]
    try:
        for token in tokens:
            result = await run_event(RSVPState.load_guests(), token=token)
            assert any(
                row["id"] == item_id for row in result["recommendations"]
            )
            await run_event(
                RSVPState.select_contribution(str(item_id)), token=token
            )
        async with rx.asession() as session:
            assert (
                await session.scalar(
                    select(RSVP.id).where(RSVP.recommended_item_id == item_id)
                )
                is None
            )
        results = await asyncio.gather(
            *(
                run_event(
                    RSVPState.submit_rsvp({"guest_name": name}), token=token
                )
                for name, token in zip(names, tokens, strict=True)
            )
        )
        assert sum(bool(result["submitted"]) for result in results) == 1
        loser = next(result for result in results if not result["submitted"])
        assert loser["error"] == CLAIM_ERROR and loser["guest_name"] in names
        assert not any(row["id"] == item_id for row in loser["recommendations"])
        async with rx.asession() as session:
            rows = (
                await session.scalars(
                    select(RSVP).where(RSVP.recommended_item_id == item_id)
                )
            ).all()
            assert len(rows) == 1 and rows[0].contribution == prefix
        result = await run_event(
            RSVPState.load_guests(), token=f"{prefix}-reload"
        )
        assert not any(
            row["id"] == item_id for row in result["recommendations"]
        )
        assert any(
            row["name"] in names and row["contribution"] == prefix
            for row in result["guests"]
        )
    finally:
        async with rx.asession() as session:
            await session.execute(
                delete(RSVP).where(RSVP.recommended_item_id == item_id)
            )
            await session.execute(
                delete(RecommendedItem).where(RecommendedItem.id == item_id)
            )
            await session.commit()


async def test_stale_hidden_and_forged_selection(run_event: RunEvent):
    name = f"Stale test {uuid4().hex}"
    async with rx.asession() as session:
        item = RecommendedItem(
            name=name, normalized_name=name.casefold(), active=False
        )
        session.add(item)
        await session.commit()
        item_id = item.id
    try:
        result = await run_event(
            RSVPState.submit_rsvp({"guest_name": name}),
            token=name,
            state={"selection": str(item_id)},
        )
        assert result["error"] == CLAIM_ERROR and result["guest_name"] == name
        result = await run_event(
            RSVPState.submit_rsvp({"guest_name": name}),
            token=name,
            state={"selection": "999999999999999999999999999999"},
        )
        assert result["error"] and not result["submitted"]
        async with rx.asession() as session:
            assert (
                await session.scalar(
                    select(RSVP.id).where(RSVP.guest_name == name)
                )
                is None
            )
    finally:
        async with rx.asession() as session:
            await session.execute(
                delete(RecommendedItem).where(RecommendedItem.id == item_id)
            )
            await session.commit()


async def test_contribution_mode_drafts(run_event: RunEvent):
    token = f"mode-drafts-{uuid4().hex}"
    await run_event(
        RSVPState.update_guest_name("Draft guest"),
        token=token,
        state={"recommendations": [{"id": 123, "name": "Pumpkin pie"}]},
    )
    result = await run_event(RSVPState.select_contribution("123"), token=token)
    assert result["contribution_mode"] == "dish"
    assert result["contribution_summary"] == "You’re bringing: Pumpkin pie"
    await run_event(RSVPState.set_contribution_mode("custom"), token=token)
    result = await run_event(
        RSVPState.update_custom_text("Homemade bread"), token=token
    )
    assert result["guest_name"] == "Draft guest"
    assert result["selection"] == "custom"
    assert result["contribution_summary"] == "You’re bringing: Homemade bread"
    result = await run_event(
        RSVPState.set_contribution_mode("myself"), token=token
    )
    assert result["selection"] == NOTHING
    assert result["contribution_summary"] == "Bringing good vibes"
    assert result["custom_text"] == "Homemade bread"
    result = await run_event(
        RSVPState.set_contribution_mode("dish"), token=token
    )
    assert (
        result["selection"] == "123" and result["guest_name"] == "Draft guest"
    )
    result = await run_event(
        RSVPState.set_contribution_mode("invalid"), token=token
    )
    assert (
        result["contribution_mode"] == "dish" and result["selection"] == "123"
    )
    result = await run_event(
        RSVPState.set_contribution_mode("custom"),
        token=token,
        state={"saving": True},
    )
    assert (
        result["selection"] == "123" and result["contribution_mode"] == "dish"
    )
    result = await run_event(
        RSVPState.set_contribution_mode("dish"),
        token=token,
        state={"saving": False, "recommendations": [], "selection": ""},
    )
    assert result["selection"] == ""
    assert (
        result["contribution_summary"]
        == "Choose a contribution before confirming."
    )
    await run_event(RSVPState.set_contribution_mode("custom"), token=token)
    result = await run_event(
        RSVPState.submit_rsvp({"guest_name": ""}), token=token
    )
    assert result["error"] and result["custom_text"] == "Homemade bread"
    result = await run_event(RSVPState.new_response(), token=token)
    assert result["contribution_mode"] == "dish"
    assert result["guest_name"] == "" and result["custom_text"] == ""
    assert result["selection"] == "" and result["last_dish_selection"] == ""


async def run_public_tests(run_event: RunEvent):
    await test_contribution_mode_drafts(run_event)
    await test_public_validation(run_event)
    await test_write_in_nothing_and_duplicate_guard(run_event)
    await test_atomic_reservation(run_event)
    await test_stale_hidden_and_forged_selection(run_event)
