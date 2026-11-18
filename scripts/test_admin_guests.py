import reflex as rx

import asyncio
from uuid import uuid4

from sqlalchemy import delete, select

from thanksgiving_gathering_planner.models import AdminOwner, RecommendedItem, RSVP
from thanksgiving_gathering_planner.states.admin_state import AdminState
from thanksgiving_gathering_planner.states.rsvp_state import NOTHING, RSVPState
from scripts.test_rsvp import RunEvent


async def run_admin_guest_tests(run_event: RunEvent):
    """Use real event authorization; fixtures and cleanup touch only test-owned rows."""
    async with rx.asession() as session:
        owner_sub = await session.scalar(
            select(AdminOwner.sub).where(AdminOwner.id == 1)
        )
    assert owner_sub, (
        "Requires the existing admin; never bootstrap ownership in this suite."
    )
    prefix = f"Guest test {uuid4().hex}"
    owner = {"sub": owner_sub}
    token = f"{prefix}-owner"
    other = {"sub": f"{prefix}-outsider"}
    item_ids: list[int] = []
    guest_ids: list[int] = []
    try:
        async with rx.asession() as session:
            fixtures = [
                RecommendedItem(
                    name=f"{prefix} hidden",
                    normalized_name=f"{prefix} hidden".casefold(),
                    active=False,
                ),
                RecommendedItem(
                    name=f"{prefix} available",
                    normalized_name=f"{prefix} available".casefold(),
                ),
                RecommendedItem(
                    name=f"{prefix} claimed",
                    normalized_name=f"{prefix} claimed".casefold(),
                ),
                RecommendedItem(
                    name=f"{prefix} race",
                    normalized_name=f"{prefix} race".casefold(),
                ),
            ]
            session.add_all(fixtures)
            await session.flush()
            item_ids = [item.id for item in fixtures]
            hidden_id, available_id, claimed_id, race_id = item_ids
            guests = [
                RSVP(
                    guest_name=f"{prefix} guest",
                    contribution=fixtures[0].name,
                    recommended_item_id=hidden_id,
                ),
                RSVP(
                    guest_name=f"{prefix} other",
                    contribution=fixtures[2].name,
                    recommended_item_id=claimed_id,
                ),
            ]
            session.add_all(guests)
            await session.flush()
            guest_ids = [guest.id for guest in guests]
            guest_id, other_id = guest_ids
            await session.commit()

        async def dispatch(
            event: rx.event.EventSpec, state: dict[str, object] | None = None
        ) -> dict[str, object]:
            return await run_event(
                event, token=token, claims=owner, state=state
            )

        async def read_guest(row_id: int) -> tuple[str, str, int]:
            async with rx.asession() as session:
                row = await session.get(RSVP, row_id)
                assert row is not None
                return (
                    row.guest_name,
                    row.contribution,
                    row.recommended_item_id or 0,
                )

        result = await dispatch(AdminState.load_items())
        assert result["guest_loaded"] and not result["guest_loading"]
        assert any(g["id"] == guest_id for g in result["guests"])
        result = await dispatch(AdminState.begin_guest_edit(guest_id))
        assert result["guest_edit_id"] == guest_id
        assert result["guest_choice"] == str(hidden_id)
        assert result["guest_custom_text"] == ""
        option_ids = {c["value"] for c in result["guest_choices"]}
        assert str(hidden_id) in option_ids and str(available_id) in option_ids
        assert str(claimed_id) not in option_ids
        version = result["guest_form_version"]
        await dispatch(AdminState.update_guest_edit_name("Unsaved guest name"))
        await dispatch(AdminState.set_guest_choice("custom"))
        await dispatch(AdminState.update_guest_custom_text("Unsaved bread"))
        await dispatch(AdminState.set_admin_tab("recommendations"))
        result = await dispatch(AdminState.set_admin_tab("guests"))
        assert result["guest_edit_id"] == guest_id
        assert result["guest_edit_name"] == "Unsaved guest name"
        assert result["guest_custom_text"] == "Unsaved bread"
        assert result["guest_form_version"] == version
        result = await dispatch(AdminState.set_guest_choice("nothing"))
        assert result["guest_choice"] == "nothing"
        result = await dispatch(AdminState.set_guest_choice("custom"))
        assert result["guest_custom_text"] == "Unsaved bread"
        assert result["guest_edit_name"] == "Unsaved guest name"
        assert result["guest_form_version"] == version
        result = await dispatch(AdminState.set_guest_choice("invalid"))
        assert result["guest_choice"] == "custom"
        result = await dispatch(AdminState.set_admin_tab("invalid"))
        assert result["admin_tab"] == "guests"
        result = await dispatch(
            AdminState.set_admin_tab("recommendations"), {"guest_saving": True}
        )
        assert result["admin_tab"] == "guests"
        result = await dispatch(AdminState.set_guest_choice("nothing"))
        assert result["guest_choice"] == "custom"
        await dispatch(
            AdminState.set_admin_tab("guests"), {"guest_saving": False}
        )
        assert await read_guest(guest_id) == (
            f"{prefix} guest",
            f"{prefix} hidden",
            hidden_id,
        )
        await dispatch(AdminState.cancel_guest_edit())
        result = await dispatch(
            AdminState.save_guest({"guest_edit_name": "No selection"})
        )
        assert result["guest_error"]
        assert (await read_guest(guest_id))[2] == hidden_id

        await dispatch(AdminState.begin_guest_edit(guest_id))
        for form in (
            {"guest_edit_name": " "},
            {"guest_edit_name": "x" * 101},
            {"guest_edit_name": "bad\x00"},
            {"guest_edit_name": ["forged"]},
            {
                "guest_edit_name": prefix,
                "guest_choice": "custom",
                "guest_custom_text": " ",
            },
            {
                "guest_edit_name": prefix,
                "guest_choice": "custom",
                "guest_custom_text": "x" * 201,
            },
            {
                "guest_edit_name": prefix,
                "guest_choice": "custom",
                "guest_custom_text": "bad\x00",
            },
            {"guest_edit_name": prefix, "guest_choice": "-1"},
        ):
            result = await dispatch(AdminState.save_guest(form))
            assert result["guest_error"] and not result["guest_saving"]
            assert (await read_guest(guest_id))[2] == hidden_id
        await dispatch(AdminState.begin_guest_edit(guest_id))
        result = await dispatch(
            AdminState.save_guest({"guest_edit_name": f" {prefix} renamed "})
        )
        assert not result["guest_error"]
        assert await read_guest(guest_id) == (
            f"{prefix} renamed",
            f"{prefix} hidden",
            hidden_id,
        )
        await dispatch(AdminState.begin_guest_edit(guest_id))
        result = await dispatch(
            AdminState.save_guest({"guest_choice": str(claimed_id)})
        )
        assert "claimed" in result["guest_error"]
        assert (await read_guest(guest_id))[2] == hidden_id

        await dispatch(AdminState.begin_guest_edit(guest_id))
        result = await dispatch(
            AdminState.save_guest({"guest_choice": str(available_id)})
        )
        assert not result["guest_error"]
        assert (await read_guest(guest_id))[1:] == (
            f"{prefix} available",
            available_id,
        )
        await dispatch(AdminState.begin_guest_edit(guest_id))
        result = await dispatch(
            AdminState.save_guest({"guest_choice": str(hidden_id)})
        )
        assert "hidden" in result["guest_error"]
        await dispatch(AdminState.begin_guest_edit(guest_id))
        result = await dispatch(
            AdminState.save_guest(
                {
                    "guest_choice": "custom",
                    "guest_custom_text": "  Homemade bread  ",
                }
            )
        )
        assert not result["guest_error"]
        assert (await read_guest(guest_id))[1:] == ("Homemade bread", 0)
        assert any(
            i["id"] == available_id and not i["claimed"]
            for i in result["items"]
        )
        result = await dispatch(AdminState.begin_guest_edit(guest_id))
        assert (
            result["guest_choice"] == "custom"
            and result["guest_custom_text"] == "Homemade bread"
        )
        result = await dispatch(
            AdminState.save_guest({"guest_choice": "nothing"})
        )
        assert not result["guest_error"] and (await read_guest(guest_id))[
            1:
        ] == (NOTHING, 0)
        result = await dispatch(AdminState.begin_guest_edit(guest_id))
        assert result["guest_choice"] == "nothing"

        before = await read_guest(guest_id)
        outsider_token = f"{prefix}-outsider"
        forged = {
            "owner_allowed": True,
            "guest_edit_id": guest_id,
            "guest_original_name": before[0],
            "guest_original_contribution": before[1],
            "guest_original_item_id": before[2],
            "guest_edit_name": "Forged",
            "guest_choice": "nothing",
            "guest_remove_id": guest_id,
            "guest_remove_ready": True,
            "guest_remove_name": before[0],
            "guest_remove_contribution": before[1],
            "guest_remove_item_id": before[2],
        }
        for event in (
            AdminState.begin_guest_edit(guest_id),
            AdminState.cancel_guest_edit(),
            AdminState.save_guest(
                {"guest_edit_name": "Forged", "guest_choice": "nothing"}
            ),
            AdminState.ask_remove_guest(guest_id),
            AdminState.cancel_remove_guest(),
            AdminState.confirm_remove_guest(),
            AdminState.load_items(),
        ):
            await run_event(
                event, token=outsider_token, claims=other, state=forged
            )
            assert await read_guest(guest_id) == before

        await dispatch(AdminState.begin_guest_edit(guest_id))
        second_token = f"{prefix}-second-owner-session"
        await run_event(
            AdminState.begin_guest_edit(guest_id),
            token=second_token,
            claims=owner,
        )
        await run_event(
            AdminState.save_guest({"guest_edit_name": f"{prefix} newer"}),
            token=second_token,
            claims=owner,
        )
        result = await dispatch(
            AdminState.save_guest({"guest_edit_name": f"{prefix} stale"})
        )
        assert "another session" in result["guest_error"]
        assert (await read_guest(guest_id))[0] == f"{prefix} newer"

        await dispatch(AdminState.begin_guest_edit(guest_id))
        public_token = f"{prefix}-public"
        await run_event(RSVPState.load_guests(), token=public_token)
        await run_event(
            RSVPState.select_contribution(str(race_id)), token=public_token
        )
        await asyncio.gather(
            dispatch(AdminState.save_guest({"guest_choice": str(race_id)})),
            run_event(
                RSVPState.submit_rsvp({"guest_name": f"{prefix} public"}),
                token=public_token,
            ),
        )
        async with rx.asession() as session:
            claimants = (
                await session.scalars(
                    select(RSVP).where(RSVP.recommended_item_id == race_id)
                )
            ).all()
            assert len(claimants) == 1
            public_ids = (
                await session.scalars(
                    select(RSVP.id).where(RSVP.guest_name == f"{prefix} public")
                )
            ).all()
            guest_ids.extend(public_ids)

        await dispatch(AdminState.ask_remove_guest(other_id))
        await dispatch(AdminState.cancel_remove_guest())
        result = await dispatch(AdminState.confirm_remove_guest())
        assert (
            result["guest_error"]
            and (await read_guest(other_id))[2] == claimed_id
        )
        for invalid_id in (0, -1, 2**31):
            result = await dispatch(AdminState.ask_remove_guest(invalid_id))
            assert result["guest_error"] and result["guest_remove_id"] == 0
        await dispatch(AdminState.ask_remove_guest(other_id))
        result = await dispatch(AdminState.confirm_remove_guest())
        assert not result["guest_error"] and result["guest_remove_id"] == 0
        assert any(
            i["id"] == claimed_id and not i["claimed"] for i in result["items"]
        )
        async with rx.asession() as session:
            assert await session.get(RSVP, other_id) is None
            assert await session.get(RecommendedItem, claimed_id) is not None
        result = await dispatch(AdminState.begin_guest_edit(other_id))
        assert "no longer exists" in result["guest_error"]
        await dispatch(AdminState.ask_remove_guest(guest_id))
        result = await dispatch(AdminState.confirm_remove_guest())
        assert not result["guest_error"]
        public = await run_event(RSVPState.load_guests(), token=public_token)
        assert not any(
            g["id"] in (guest_id, other_id) for g in public["guests"]
        )
        assert any(i["id"] == claimed_id for i in public["recommendations"])
    finally:
        async with rx.asession() as session:
            await session.execute(
                delete(RSVP).where(
                    RSVP.id.in_(guest_ids)
                    | (RSVP.guest_name == f"{prefix} public")
                )
            )
            await session.execute(
                delete(RecommendedItem).where(RecommendedItem.id.in_(item_ids))
            )
            await session.commit()
