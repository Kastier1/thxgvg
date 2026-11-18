import reflex as rx
import reflex_enterprise as rxe

import asyncio
import logging
from typing import Any, TypedDict

from reflex_enterprise.auth import User
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from thanksgiving_gathering_planner.models import AdminOwner, RecommendedItem, RSVP
from thanksgiving_gathering_planner.states.admin_access import is_admin


class AdminItem(TypedDict):
    id: int
    name: str
    active: bool
    claimed: bool
    guest_name: str
    status: str


class AdminGuest(TypedDict):
    id: int
    name: str
    contribution: str
    recommended_item_id: int


class GuestChoice(TypedDict):
    value: str
    label: str


class AdminState(rx.State):
    owner_ready: bool = rxe.field(False, auth=False)
    owner_allowed: bool = rxe.field(False, auth=False)
    access_error: str = rxe.field("", auth=False)
    admin_tab: str = rxe.field("guests", auth=is_admin)
    items: list[AdminItem] = rxe.field([], auth=is_admin)
    loading: bool = rxe.field(False, auth=is_admin)
    saving: bool = rxe.field(False, auth=is_admin)
    error: str = rxe.field("", auth=is_admin)
    notice: str = rxe.field("", auth=is_admin)
    draft_name: str = rxe.field("", auth=is_admin)
    edit_id: int = rxe.field(0, auth=is_admin)
    edit_name: str = rxe.field("", auth=is_admin)
    remove_id: int = rxe.field(0, auth=is_admin)
    form_version: int = rxe.field(0, auth=is_admin)
    guests: list[AdminGuest] = rxe.field([], auth=is_admin)
    guest_loading: bool = rxe.field(False, auth=is_admin)
    guest_loaded: bool = rxe.field(False, auth=is_admin)
    guest_saving: bool = rxe.field(False, auth=is_admin)
    guest_list_error: str = rxe.field("", auth=is_admin)
    guest_error: str = rxe.field("", auth=is_admin)
    guest_notice: str = rxe.field("", auth=is_admin)
    guest_edit_id: int = rxe.field(0, auth=is_admin)
    guest_edit_name: str = rxe.field("", auth=is_admin)
    guest_choice: str = rxe.field("", auth=is_admin)
    guest_custom_text: str = rxe.field("", auth=is_admin)
    guest_choices: list[GuestChoice] = rxe.field([], auth=is_admin)
    guest_form_version: int = rxe.field(0, auth=is_admin)
    guest_original_name: str = rxe.field("", auth=is_admin)
    guest_original_contribution: str = rxe.field("", auth=is_admin)
    guest_original_item_id: int = rxe.field(0, auth=is_admin)
    guest_remove_id: int = rxe.field(0, auth=is_admin)
    guest_remove_ready: bool = rxe.field(False, auth=is_admin)
    guest_remove_name: str = rxe.field("", auth=is_admin)
    guest_remove_contribution: str = rxe.field("", auth=is_admin)
    guest_remove_item_id: int = rxe.field(0, auth=is_admin)

    @rxe.var(auth=is_admin, initial_value="0 guests")
    def guest_count_label(self) -> str:
        count = len(self.guests)
        return "1 guest" if count == 1 else f"{count} guests"

    @rxe.event(auth=is_admin)
    def set_admin_tab(self, value: str):
        if value in ("guests", "recommendations") and not (
            self.saving
            or self.guest_saving
            or self.loading
            or self.guest_loading
        ):
            self.admin_tab = value

    @rxe.event(auth=is_admin)
    def update_guest_edit_name(self, value: str):
        if not (
            self.saving
            or self.guest_saving
            or self.loading
            or self.guest_loading
        ):
            self.guest_edit_name = value

    @rxe.event(auth=is_admin)
    def update_guest_custom_text(self, value: str):
        if not (
            self.saving
            or self.guest_saving
            or self.loading
            or self.guest_loading
        ):
            self.guest_custom_text = value

    @rxe.event(auth=is_admin)
    def set_guest_choice(self, value: str):
        if (
            self.saving
            or self.guest_saving
            or self.loading
            or self.guest_loading
        ):
            return
        allowed = {choice["value"] for choice in self.guest_choices}
        if value in allowed or value in ("custom", "nothing"):
            self.guest_choice = value
            self.guest_error = ""

    @rxe.event(auth=is_admin)
    def save_guest_draft(self, form_data: dict[str, Any]):
        if not (
            self.saving
            or self.guest_saving
            or self.loading
            or self.guest_loading
        ):
            return AdminState.save_guest(form_data)

    @rxe.event(auth=True)
    async def load_owner(self):
        self.owner_ready = False
        self.owner_allowed = False
        self.access_error = ""
        yield
        user = await User.current() or {}
        sub = user.get("sub")
        if not isinstance(sub, str) or not sub.strip():
            self.access_error = "Your sign-in could not be verified. Please sign out and try again."
            self.owner_ready = True
            return
        try:
            async with asyncio.timeout(6):
                async with rx.asession() as session:
                    await session.execute(
                        insert(AdminOwner)
                        .values(id=1, sub=sub)
                        .on_conflict_do_nothing()
                    )
                    await session.commit()
                    owner_sub = await session.scalar(
                        select(AdminOwner.sub).where(AdminOwner.id == 1)
                    )
            self.owner_allowed = owner_sub == sub
        except (SQLAlchemyError, OSError, TimeoutError):
            logging.exception("Unable to initialize admin ownership")
            self.access_error = (
                "We couldn’t check access. Use Retry access to try again."
            )
        self.owner_ready = True
        if self.owner_allowed:
            yield AdminState.load_items

    async def _refresh_items(self):
        async with rx.asession() as session:
            rows = (
                await session.execute(
                    select(RecommendedItem, RSVP.guest_name, RSVP.id)
                    .outerjoin(
                        RSVP, RSVP.recommended_item_id == RecommendedItem.id
                    )
                    .order_by(RecommendedItem.created_at, RecommendedItem.id)
                )
            ).all()
            records = (
                await session.scalars(
                    select(RSVP).order_by(RSVP.created_at, RSVP.id)
                )
            ).all()
            guests = [
                {
                    "id": row.id,
                    "name": row.guest_name,
                    "contribution": row.contribution,
                    "recommended_item_id": row.recommended_item_id or 0,
                }
                for row in records
            ]
            self.items = [
                {
                    "id": item.id,
                    "name": item.name,
                    "active": item.active,
                    "claimed": rsvp_id is not None,
                    "guest_name": guest_name or "",
                    "status": "Claimed"
                    if rsvp_id is not None
                    else ("Available" if item.active else "Hidden"),
                }
                for item, guest_name, rsvp_id in rows
            ]
            self.guests = guests
            self.guest_loaded = True
            self.guest_list_error = ""
            if self.guest_edit_id:
                self._set_guest_choices(self.guest_edit_id)

    @rxe.event(auth=is_admin)
    async def load_items(self):
        if self.loading or self.saving or self.guest_saving:
            return
        self.loading = True
        self.guest_loading = True
        self.guest_list_error = ""
        self.error = ""
        yield
        try:
            async with asyncio.timeout(6):
                await self._refresh_items()
        except (SQLAlchemyError, OSError, TimeoutError):
            logging.exception("Unable to load recommended items")
            self.error = (
                "Items couldn’t be loaded. Select Refresh to try again."
            )
            self.guest_list_error = (
                "Guests couldn’t be loaded. Select Refresh to try again."
            )
        finally:
            self.loading = False
            self.guest_loading = False

    def _validate_name(self, raw: object) -> tuple[str, str]:
        name = raw.strip() if isinstance(raw, str) else ""
        if not name or "\x00" in name:
            return name, "Enter an item name."
        if len(name) > 100:
            return name, "Keep item names to 100 characters or fewer."
        return name, ""

    @rxe.event(auth=is_admin)
    async def create_item(self, form_data: dict[str, Any]):
        if (
            self.saving
            or self.guest_saving
            or self.loading
            or self.guest_loading
        ):
            return
        name, self.error = self._validate_name(form_data.get("item_name", ""))
        self.draft_name = name
        self.notice = ""
        if self.error:
            return
        self.saving = True
        yield
        try:
            async with asyncio.timeout(6):
                async with rx.asession() as session:
                    session.add(
                        RecommendedItem(
                            name=name, normalized_name=name.casefold()
                        )
                    )
                    await session.commit()
            self.draft_name = ""
            self.form_version += 1
            self.notice = "Item added."
        except IntegrityError:
            self.error = "That name already exists, including hidden or claimed items. Choose another name."
        except (SQLAlchemyError, OSError, TimeoutError):
            logging.exception("Unable to create recommended item")
            self.error = "Item couldn’t be added. Please try again."
        finally:
            self.saving = False
        yield AdminState.load_items_preserving_feedback

    @rxe.event(auth=is_admin)
    async def load_items_preserving_feedback(self):
        self.guest_loading = True
        yield
        try:
            async with asyncio.timeout(6):
                await self._refresh_items()
        except (SQLAlchemyError, OSError, TimeoutError):
            logging.exception("Unable to refresh recommended items")
            self.error = "The list couldn’t refresh. Select Refresh before making another change."
            self.guest_list_error = "Guests couldn’t refresh. Select Refresh before making another change."
        finally:
            self.guest_loading = False

    @rxe.event(auth=is_admin)
    def begin_edit(self, item_id: int):
        if (
            self.saving
            or self.guest_saving
            or self.loading
            or self.guest_loading
        ):
            return
        item = next(
            (item for item in self.items if item["id"] == item_id), None
        )
        if item is None or item["claimed"]:
            self.error = "Only unclaimed items can be edited. Refresh the list."
            return
        self.edit_id = item_id
        self.edit_name = item["name"]
        self.remove_id = 0
        self.error = ""
        self.notice = ""

    @rxe.event(auth=is_admin)
    def cancel_edit(self):
        if not (
            self.saving
            or self.guest_saving
            or self.loading
            or self.guest_loading
        ):
            self.edit_id = 0
            self.edit_name = ""

    @rxe.event(auth=is_admin)
    def ask_remove(self, item_id: int):
        if (
            self.saving
            or self.guest_saving
            or self.loading
            or self.guest_loading
        ):
            return
        item = next(
            (item for item in self.items if item["id"] == item_id), None
        )
        if item is None or item["claimed"]:
            self.error = (
                "Only unclaimed items can be removed. Refresh the list."
            )
            return
        self.remove_id = item_id
        self.edit_id = 0
        self.error = ""
        self.notice = ""

    @rxe.event(auth=is_admin)
    def cancel_remove(self):
        if not (
            self.saving
            or self.guest_saving
            or self.loading
            or self.guest_loading
        ):
            self.remove_id = 0

    async def _mutate_unclaimed(
        self, item_id: int, action: str, name: str = ""
    ):
        if (
            isinstance(item_id, bool)
            or not isinstance(item_id, int)
            or item_id <= 0
            or item_id > 2**31 - 1
        ):
            self.error = "That item is invalid. Refresh and try again."
            return
        async with rx.asession() as session:
            item = await session.scalar(
                select(RecommendedItem)
                .where(RecommendedItem.id == item_id)
                .with_for_update()
            )
            claimed = await session.scalar(
                select(RSVP.id).where(RSVP.recommended_item_id == item_id)
            )
            if item is None:
                self.error = "This item was removed. Refresh the list."
                return
            if claimed is not None:
                self.error = "This item has been claimed. Its name and contribution cannot be changed."
                return
            if action == "rename":
                item.name = name
                item.normalized_name = name.casefold()
            elif action == "toggle":
                item.active = not item.active
            elif action == "remove":
                await session.delete(item)
            await session.commit()

    @rxe.event(auth=is_admin)
    async def save_name(self, form_data: dict[str, Any]):
        if (
            self.saving
            or self.guest_saving
            or self.loading
            or self.guest_loading
        ):
            return
        name, self.error = self._validate_name(form_data.get("edit_name", ""))
        self.edit_name = name
        self.notice = ""
        if self.error:
            return
        self.saving = True
        yield
        try:
            async with asyncio.timeout(6):
                await self._mutate_unclaimed(self.edit_id, "rename", name)
            if not self.error:
                self.edit_id = 0
                self.notice = "Name updated."
        except IntegrityError:
            self.error = (
                "That name already exists. Choose a different item name."
            )
        except (SQLAlchemyError, OSError, TimeoutError):
            logging.exception("Unable to rename recommended item")
            self.error = "The name couldn’t be saved. Please try again."
        finally:
            self.saving = False
        yield AdminState.load_items_preserving_feedback

    @rxe.event(auth=is_admin)
    async def toggle_item(self, item_id: int):
        if (
            self.saving
            or self.guest_saving
            or self.loading
            or self.guest_loading
        ):
            return
        self.saving = True
        self.error = ""
        self.notice = ""
        yield
        try:
            async with asyncio.timeout(6):
                await self._mutate_unclaimed(item_id, "toggle")
            if not self.error:
                self.notice = "Visibility updated."
        except (SQLAlchemyError, OSError, TimeoutError):
            logging.exception("Unable to change item visibility")
            self.error = "Visibility couldn’t be changed. Please try again."
        finally:
            self.saving = False
        yield AdminState.load_items_preserving_feedback

    def _valid_guest_id(self, value: object) -> bool:
        return (
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 < value <= 2**31 - 1
        )

    def _choice_item_id(self, choice: str) -> int:
        if choice.isascii() and choice.isdecimal() and len(choice) <= 10:
            value = int(choice)
            return value if self._valid_guest_id(value) else 0
        return 0

    def _set_guest_choices(self, guest_id: int):
        guest = next((g for g in self.guests if g["id"] == guest_id), None)
        current_id = guest["recommended_item_id"] if guest else 0
        self.guest_choices = [
            {
                "value": str(item["id"]),
                "label": f"{item['name']} (currently reserved)"
                if item["id"] == current_id
                else item["name"],
            }
            for item in self.items
            if item["id"] == current_id
            or (item["active"] and not item["claimed"])
        ]

    def _clear_guest_edit(self):
        self.guest_edit_id = 0
        self.guest_edit_name = ""
        self.guest_choice = ""
        self.guest_custom_text = ""
        self.guest_choices = []
        self.guest_original_name = ""
        self.guest_original_contribution = ""
        self.guest_original_item_id = 0
        self.guest_form_version += 1

    def _clear_guest_remove(self):
        self.guest_remove_ready = False
        self.guest_remove_id = 0
        self.guest_remove_name = ""
        self.guest_remove_contribution = ""
        self.guest_remove_item_id = 0

    @rxe.event(auth=is_admin)
    async def begin_guest_edit(self, guest_id: int):
        if (
            self.saving
            or self.guest_saving
            or self.loading
            or self.guest_loading
        ):
            return
        self.guest_error = ""
        self.guest_notice = ""
        if not self._valid_guest_id(guest_id):
            self.guest_error = (
                "That guest ID is invalid. Refresh and try again."
            )
            return
        self.guest_loading = True
        yield
        try:
            async with asyncio.timeout(6):
                await self._refresh_items()
            guest = next((g for g in self.guests if g["id"] == guest_id), None)
            if guest is None:
                self._clear_guest_edit()
                self.guest_error = (
                    "This guest RSVP no longer exists. Refresh the list."
                )
                return
            from thanksgiving_gathering_planner.states.rsvp_state import NOTHING

            self._clear_guest_remove()
            self.guest_edit_id = guest_id
            self.guest_edit_name = guest["name"]
            self.guest_original_name = guest["name"]
            self.guest_original_contribution = guest["contribution"]
            self.guest_original_item_id = guest["recommended_item_id"]
            self.guest_choice = (
                str(guest["recommended_item_id"])
                if guest["recommended_item_id"]
                else (
                    "nothing" if guest["contribution"] == NOTHING else "custom"
                )
            )
            self.guest_custom_text = (
                guest["contribution"] if self.guest_choice == "custom" else ""
            )
            self._set_guest_choices(guest_id)
            self.guest_form_version += 1
        except (SQLAlchemyError, OSError, TimeoutError):
            logging.exception("Unable to open guest editor")
            self.guest_error = (
                "The guest editor couldn’t load. Refresh and try again."
            )
        finally:
            self.guest_loading = False

    @rxe.event(auth=is_admin)
    def cancel_guest_edit(self):
        if self.saving or self.guest_saving or self.guest_loading:
            return
        self._clear_guest_edit()
        self.guest_error = ""

    @rxe.event(auth=is_admin)
    async def ask_remove_guest(self, guest_id: int):
        if (
            self.saving
            or self.guest_saving
            or self.loading
            or self.guest_loading
        ):
            return
        self.guest_error = ""
        self.guest_notice = ""
        self._clear_guest_remove()
        if not self._valid_guest_id(guest_id):
            self.guest_error = (
                "That guest ID is invalid. Refresh and try again."
            )
            return
        self.guest_loading = True
        yield
        try:
            async with asyncio.timeout(6):
                await self._refresh_items()
            guest = next((g for g in self.guests if g["id"] == guest_id), None)
            if guest is None:
                self.guest_error = (
                    "This guest RSVP no longer exists. Refresh the list."
                )
                return
            self._clear_guest_edit()
            self.guest_remove_id = guest_id
            self.guest_remove_name = guest["name"]
            self.guest_remove_contribution = guest["contribution"]
            self.guest_remove_item_id = guest["recommended_item_id"]
            self.guest_remove_ready = True
        except (SQLAlchemyError, OSError, TimeoutError):
            logging.exception("Unable to prepare guest removal")
            self.guest_error = (
                "The guest couldn’t be loaded. Refresh and try again."
            )
        finally:
            self.guest_loading = False

    @rxe.event(auth=is_admin)
    def cancel_remove_guest(self):
        if self.saving or self.guest_saving or self.guest_loading:
            return
        self._clear_guest_remove()
        self.guest_error = ""

    async def _mutate_guest(
        self,
        guest_id: int,
        action: str,
        name: str = "",
        choice: str = "",
        custom: str = "",
    ) -> str:
        if not self._valid_guest_id(guest_id):
            return "Select a valid guest before saving or confirming removal."
        from thanksgiving_gathering_planner.states.rsvp_state import NOTHING

        target_id = self._choice_item_id(choice) if action == "edit" else 0
        expected = (
            (
                self.guest_original_name,
                self.guest_original_contribution,
                self.guest_original_item_id,
            )
            if action == "edit"
            else (
                self.guest_remove_name,
                self.guest_remove_contribution,
                self.guest_remove_item_id,
            )
        )
        async with rx.asession() as session:
            before = (
                await session.execute(
                    select(
                        RSVP.guest_name,
                        RSVP.contribution,
                        RSVP.recommended_item_id,
                    ).where(RSVP.id == guest_id)
                )
            ).first()
            if before is None:
                return "This guest RSVP no longer exists. Refresh the list."
            old_id = before.recommended_item_id or 0
            lock_ids = sorted({i for i in (old_id, target_id) if i})
            locked_items = (
                await session.scalars(
                    select(RecommendedItem)
                    .where(RecommendedItem.id.in_(lock_ids))
                    .order_by(RecommendedItem.id)
                    .with_for_update()
                )
            ).all()
            guest = await session.scalar(
                select(RSVP)
                .where(RSVP.id == guest_id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            if guest is None:
                return "This guest RSVP no longer exists. Refresh the list."
            actual = (
                guest.guest_name,
                guest.contribution,
                guest.recommended_item_id or 0,
            )
            if actual != expected or actual != (
                before.guest_name,
                before.contribution,
                old_id,
            ):
                return "This guest was changed in another session. Cancel and reopen the editor or removal confirmation."
            if action == "remove":
                await session.delete(guest)
            else:
                contribution = custom if choice == "custom" else NOTHING
                if target_id:
                    item = next(
                        (i for i in locked_items if i.id == target_id), None
                    )
                    if item is None:
                        return "That recommended dish was removed. Refresh and choose another."
                    if not item.active and target_id != old_id:
                        return "That recommended dish is now hidden. Choose an available dish."
                    claimed = await session.scalar(
                        select(RSVP.id).where(
                            RSVP.recommended_item_id == target_id,
                            RSVP.id != guest_id,
                        )
                    )
                    if claimed is not None:
                        return "Another guest has claimed that dish. Refresh and choose another."
                    contribution = item.name
                guest.guest_name = name
                guest.contribution = contribution
                guest.recommended_item_id = target_id or None
            await session.commit()
        return ""

    @rxe.event(auth=is_admin)
    async def save_guest(self, form_data: dict[str, Any]):
        if (
            self.saving
            or self.guest_saving
            or self.loading
            or self.guest_loading
        ):
            return
        self.guest_error = ""
        self.guest_notice = ""
        raw_name = form_data.get("guest_edit_name", self.guest_edit_name)
        raw_custom = form_data.get("guest_custom_text", self.guest_custom_text)
        raw_choice = form_data.get("guest_choice", self.guest_choice)
        self.guest_edit_name = (
            raw_name.strip() if isinstance(raw_name, str) else ""
        )
        self.guest_custom_text = (
            raw_custom.strip() if isinstance(raw_custom, str) else ""
        )
        self.guest_choice = raw_choice if isinstance(raw_choice, str) else ""
        if not self._valid_guest_id(self.guest_edit_id):
            self.guest_error = "Select a valid guest before saving."
        elif not self.guest_edit_name or "\x00" in self.guest_edit_name:
            self.guest_error = "Enter a guest name."
        elif len(self.guest_edit_name) > 100:
            self.guest_error = "Keep guest names to 100 characters or fewer."
        elif self.guest_choice == "custom":
            if not self.guest_custom_text or "\x00" in self.guest_custom_text:
                self.guest_error = "Enter a custom contribution."
            elif len(self.guest_custom_text) > 200:
                self.guest_error = (
                    "Keep contributions to 200 characters or fewer."
                )
        elif self.guest_choice != "nothing" and not self._choice_item_id(
            self.guest_choice
        ):
            self.guest_error = "Choose an available dish, a custom contribution, or Bringing good vibes."
        if self.guest_error:
            return
        self.guest_saving = True
        yield
        try:
            async with asyncio.timeout(6):
                self.guest_error = await self._mutate_guest(
                    self.guest_edit_id,
                    "edit",
                    self.guest_edit_name,
                    self.guest_choice,
                    self.guest_custom_text,
                )
            if not self.guest_error:
                self._clear_guest_edit()
                self.guest_notice = "Guest updated."
        except IntegrityError:
            self.guest_error = "That dish was just claimed by another guest. Refresh and choose another."
        except (SQLAlchemyError, OSError, TimeoutError):
            logging.exception("Unable to save guest RSVP")
            self.guest_error = (
                "The guest couldn’t be saved. Please refresh and try again."
            )
        finally:
            self.guest_saving = False
        yield AdminState.load_items_preserving_feedback
        if not self.guest_error:
            from thanksgiving_gathering_planner.states.rsvp_state import RSVPState

            yield RSVPState.load_guests

    @rxe.event(auth=is_admin)
    async def confirm_remove_guest(self):
        if (
            self.saving
            or self.guest_saving
            or self.loading
            or self.guest_loading
        ):
            return
        self.guest_error = ""
        self.guest_notice = ""
        if (
            not self._valid_guest_id(self.guest_remove_id)
            or not self.guest_remove_ready
        ):
            self.guest_error = "Select a guest and confirm removal first."
            return
        self.guest_saving = True
        yield
        try:
            async with asyncio.timeout(6):
                self.guest_error = await self._mutate_guest(
                    self.guest_remove_id, "remove"
                )
            if not self.guest_error:
                self._clear_guest_remove()
                self.guest_notice = "Guest removed. Any active reserved dish is available again."
        except IntegrityError:
            self.guest_error = (
                "This RSVP changed while removing it. Refresh and try again."
            )
        except (SQLAlchemyError, OSError, TimeoutError):
            logging.exception("Unable to remove guest RSVP")
            self.guest_error = (
                "The guest couldn’t be removed. Please refresh and try again."
            )
        finally:
            self.guest_saving = False
        yield AdminState.load_items_preserving_feedback
        if not self.guest_error:
            from thanksgiving_gathering_planner.states.rsvp_state import RSVPState

            yield RSVPState.load_guests

    @rxe.event(auth=is_admin)
    async def confirm_remove(self):
        if (
            self.saving
            or self.guest_saving
            or self.loading
            or self.guest_loading
            or self.remove_id <= 0
        ):
            return
        self.saving = True
        self.error = ""
        self.notice = ""
        yield
        try:
            async with asyncio.timeout(6):
                await self._mutate_unclaimed(self.remove_id, "remove")
            if not self.error:
                self.remove_id = 0
                self.notice = "Item removed."
        except (SQLAlchemyError, OSError, TimeoutError):
            logging.exception("Unable to remove recommended item")
            self.error = "Item couldn’t be removed. Please try again."
        finally:
            self.saving = False
        yield AdminState.load_items_preserving_feedback
