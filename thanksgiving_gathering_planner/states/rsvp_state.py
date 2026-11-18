import reflex as rx
import reflex_enterprise as rxe

import asyncio
import logging
from typing import Any, TypedDict

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from thanksgiving_gathering_planner.models import RSVP, RecommendedItem

NOTHING = "Nothing — just bringing myself"
CLAIM_ERROR = "Someone just claimed this item. Please choose another."


class Guest(TypedDict):
    id: int
    name: str
    contribution: str


class Recommendation(TypedDict):
    id: int
    name: str


class RSVPState(rx.State):
    recommendations: list[Recommendation] = rxe.field([], auth=False)
    selection: str = rxe.field("", auth=False)
    contribution_mode: str = rxe.field("dish", auth=False)
    last_dish_selection: str = rxe.field("", auth=False)
    guest_name: str = rxe.field("", auth=False)
    custom_text: str = rxe.field("", auth=False)
    error: str = rxe.field("", auth=False)
    list_error: str = rxe.field("", auth=False)
    saving: bool = rxe.field(False, auth=False)
    loading: bool = rxe.field(False, auth=False)
    submitted: bool = rxe.field(False, auth=False)
    saved_name: str = rxe.field("", auth=False)
    saved_contribution: str = rxe.field("", auth=False)
    form_version: int = rxe.field(0, auth=False)
    guests: list[Guest] = rxe.field([], auth=False)

    @rxe.var(auth=False)
    def contribution_summary(self) -> str:
        if self.contribution_mode == "myself" and self.selection == NOTHING:
            return "Bringing good vibes"
        if self.contribution_mode == "custom" and self.selection == "custom":
            text = self.custom_text.strip()
            return (
                f"You’re bringing: {text}"
                if text
                else "Tell us what you’re bringing."
            )
        if self.contribution_mode == "dish":
            item = next(
                (
                    item
                    for item in self.recommendations
                    if str(item["id"]) == self.selection
                ),
                None,
            )
            if item:
                return f"You’re bringing: {item['name']}"
        return "Choose a contribution before confirming."

    @rxe.event(auth=False)
    def set_contribution_mode(self, mode: str):
        if (
            self.saving
            or self.submitted
            or mode not in ("dish", "custom", "myself")
        ):
            return
        valid_ids = {str(item["id"]) for item in self.recommendations}
        if self.selection in valid_ids:
            self.last_dish_selection = self.selection
        self.contribution_mode = mode
        if mode == "custom":
            self.selection = "custom"
        elif mode == "myself":
            self.selection = NOTHING
        else:
            self.selection = (
                self.last_dish_selection
                if self.last_dish_selection in valid_ids
                else ""
            )
        self.error = ""

    @rxe.event(auth=False)
    def update_guest_name(self, value: str):
        if not self.saving and not self.submitted:
            self.guest_name = value

    @rxe.event(auth=False)
    def update_custom_text(self, value: str):
        if not self.saving and not self.submitted:
            self.custom_text = value

    @rxe.event(auth=False)
    def confirm_response(self, form_data: dict[str, Any]):
        if not self.saving and not self.submitted:
            return RSVPState.submit_rsvp(
                {
                    "guest_name": form_data.get("guest_name", self.guest_name),
                    "custom_text": form_data.get(
                        "custom_text", self.custom_text
                    ),
                }
            )

    def _selected_id(self) -> int:
        if (
            self.selection.isascii()
            and self.selection.isdecimal()
            and len(self.selection) <= 18
        ):
            item_id = int(self.selection)
            return item_id if 0 < item_id <= 2**31 - 1 else 0
        return 0

    @rxe.event(auth=False)
    def select_contribution(self, choice: str):
        if self.saving or self.submitted:
            return
        valid_ids = {str(item["id"]) for item in self.recommendations}
        if choice not in valid_ids and choice not in ("custom", NOTHING):
            self.error = (
                "Please choose an available item or one of the alternatives."
            )
            return
        self.selection = choice
        self.contribution_mode = (
            "custom"
            if choice == "custom"
            else ("myself" if choice == NOTHING else "dish")
        )
        if self.contribution_mode == "dish":
            self.last_dish_selection = choice
        self.error = ""

    def _validate_response(self) -> str:
        if not self.guest_name or "\x00" in self.guest_name:
            return "Please enter your name."
        if len(self.guest_name) > 100:
            return "Please keep your name to 100 characters or fewer."
        if (
            self.contribution_mode not in ("dish", "custom", "myself")
            or (
                self.contribution_mode == "custom"
                and self.selection != "custom"
            )
            or (
                self.contribution_mode == "myself" and self.selection != NOTHING
            )
            or (
                self.contribution_mode == "dish"
                and self.selection in ("custom", NOTHING)
            )
        ):
            return "Please choose a contribution option again."
        if self.selection == "custom":
            if not self.custom_text or "\x00" in self.custom_text:
                return "Please tell us what you’re bringing."
            if len(self.custom_text) > 200:
                return (
                    "Please keep your contribution to 200 characters or fewer."
                )
        elif self.selection != NOTHING and self._selected_id() <= 0:
            return (
                "Please choose a contribution, or select Bringing good vibes."
            )
        return ""

    @rxe.event(auth=False)
    async def submit_rsvp(self, form_data: dict[str, Any]):
        if self.saving or self.submitted:
            return
        raw_name = form_data.get("guest_name", "")
        raw_custom = form_data.get("custom_text", self.custom_text)
        self.guest_name = raw_name.strip() if isinstance(raw_name, str) else ""
        self.custom_text = (
            raw_custom.strip() if isinstance(raw_custom, str) else ""
        )
        self.error = self._validate_response()
        if self.error:
            return
        self.saving = True
        yield
        item_id = self._selected_id()
        contribution = (
            self.custom_text if self.selection == "custom" else NOTHING
        )
        try:
            async with asyncio.timeout(6):
                async with rx.asession() as session:
                    if item_id:
                        item = await session.scalar(
                            select(RecommendedItem)
                            .where(RecommendedItem.id == item_id)
                            .with_for_update()
                        )
                        claimed = await session.scalar(
                            select(RSVP.id).where(
                                RSVP.recommended_item_id == item_id
                            )
                        )
                        if (
                            item is None
                            or not item.active
                            or claimed is not None
                        ):
                            self.error = CLAIM_ERROR
                        else:
                            contribution = item.name
                    if not self.error:
                        session.add(
                            RSVP(
                                guest_name=self.guest_name,
                                contribution=contribution,
                                recommended_item_id=item_id or None,
                            )
                        )
                        await session.commit()
        except IntegrityError:
            self.error = (
                CLAIM_ERROR
                if item_id
                else "Your RSVP could not be saved. Please try again."
            )
        except (SQLAlchemyError, OSError, TimeoutError):
            logging.exception("Unable to save RSVP")
            self.error = "Your RSVP could not be saved. Please try again."
        self.saving = False
        if self.error:
            if self.error == CLAIM_ERROR:
                self.selection = ""
                self.last_dish_selection = ""
                self.contribution_mode = "dish"
            self.form_version += 1
            yield
            yield RSVPState.load_guests
            return
        self.saved_name = self.guest_name
        self.saved_contribution = contribution
        self.submitted = True
        self.guest_name = ""
        self.custom_text = ""
        self.selection = ""
        self.last_dish_selection = ""
        self.contribution_mode = "dish"
        self.form_version += 1
        yield
        yield RSVPState.load_guests

    @rxe.event(auth=False)
    def new_response(self):
        if self.saving:
            return
        self.submitted = False
        self.guest_name = ""
        self.custom_text = ""
        self.selection = ""
        self.last_dish_selection = ""
        self.contribution_mode = "dish"
        self.error = ""
        self.saved_name = ""
        self.saved_contribution = ""
        self.form_version += 1
        yield RSVPState.load_guests

    @rxe.event(auth=False)
    async def load_guests(self):
        if self.loading:
            return
        self.loading = True
        self.list_error = ""
        yield
        try:
            async with asyncio.timeout(6):
                async with rx.asession() as session:
                    records = (
                        await session.scalars(
                            select(RSVP).order_by(RSVP.created_at, RSVP.id)
                        )
                    ).all()
                    items = (
                        await session.scalars(
                            select(RecommendedItem)
                            .where(
                                RecommendedItem.active.is_(True),
                                ~select(RSVP.id)
                                .where(
                                    RSVP.recommended_item_id
                                    == RecommendedItem.id
                                )
                                .exists(),
                            )
                            .order_by(
                                RecommendedItem.created_at, RecommendedItem.id
                            )
                        )
                    ).all()
                    self.guests = [
                        {
                            "id": row.id,
                            "name": row.guest_name,
                            "contribution": row.contribution,
                        }
                        for row in records
                    ]
                    self.recommendations = [
                        {"id": item.id, "name": item.name} for item in items
                    ]
        except (SQLAlchemyError, OSError, TimeoutError):
            logging.exception("Unable to load RSVP choices and guest list")
            self.list_error = (
                "We couldn’t refresh the list. Please try Refresh again."
            )
        finally:
            self.loading = False
