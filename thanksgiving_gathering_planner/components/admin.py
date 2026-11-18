import reflex as rx

from reflex_enterprise.auth import User

from thanksgiving_gathering_planner.states.admin_state import AdminGuest, AdminItem, AdminState
from thanksgiving_gathering_planner.states.rsvp_state import NOTHING


BUTTON = "inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border border-[#D9D4C4] bg-[#FFFCF5] px-4 py-2 text-sm font-medium text-[#343D2B] hover:bg-[#F1EBDD] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#B85732] disabled:cursor-not-allowed disabled:opacity-50"
PRIMARY = "inline-flex min-h-12 items-center justify-center gap-2 rounded-2xl bg-[#B85732] px-5 py-3 text-sm font-semibold text-white hover:bg-[#9C492B] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#B85732] disabled:cursor-wait disabled:opacity-60"
REMOVE = "inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border border-[#B42318]/40 bg-[#FFFCF5] px-4 py-2 text-sm font-medium text-[#B42318] hover:border-[#B42318] hover:bg-[#FEF3F2] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#B42318] disabled:cursor-not-allowed disabled:opacity-50"
DESTRUCTIVE = "inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-[#B42318] px-4 py-2 text-sm font-semibold text-white hover:bg-[#912018] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#B42318] disabled:cursor-wait disabled:opacity-60"
TAB = "min-h-11 rounded-xl px-4 py-2 text-sm font-semibold text-[#59634B] before:!hidden after:!hidden hover:bg-[#F1EBDD] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#B85732] data-[state=active]:!bg-[#F7EADF] data-[state=active]:!text-[#9C492B] disabled:cursor-not-allowed disabled:opacity-50"
INPUT = "h-12 w-full rounded-2xl border border-[#D5D0BF] bg-white px-4 text-sm text-[#343D2B] placeholder:text-[#6D715E] focus-visible:outline-2 focus-visible:outline-[#B85732] disabled:opacity-60"


def item_status(item: AdminItem) -> rx.Component:
    return rx.match(
        item["status"],
        (
            "Available",
            rx.el.span(
                "Available",
                class_name="w-fit rounded-full bg-[#E7EBD9] px-3 py-1 text-xs font-semibold text-[#455638]",
            ),
        ),
        (
            "Claimed",
            rx.el.span(
                "Claimed",
                class_name="w-fit rounded-full bg-[#F1E4C2] px-3 py-1 text-xs font-semibold text-[#775B24]",
            ),
        ),
        (
            "Hidden",
            rx.el.span(
                "Hidden",
                class_name="w-fit rounded-full bg-[#EAE6DF] px-3 py-1 text-xs font-semibold text-[#645E55]",
            ),
        ),
        rx.el.span(
            "Unavailable",
            class_name="w-fit rounded-full bg-[#EAE6DF] px-3 py-1 text-xs text-[#645E55]",
        ),
    )


def edit_form() -> rx.Component:
    return rx.el.form(
        rx.el.label(
            "Item name",
            html_for="edit_name",
            class_name="mb-2 block text-sm font-medium text-[#343D2B]",
        ),
        rx.el.input(
            id="edit_name",
            name="edit_name",
            default_value=AdminState.edit_name,
            key=AdminState.edit_name,
            required=True,
            max_length=100,
            disabled=AdminState.saving
            | AdminState.guest_saving
            | AdminState.loading
            | AdminState.guest_loading,
            class_name=INPUT,
        ),
        rx.el.div(
            rx.el.button(
                rx.cond(AdminState.saving, "Saving…", "Save name"),
                type="submit",
                disabled=AdminState.saving
                | AdminState.guest_saving
                | AdminState.loading
                | AdminState.guest_loading,
                class_name=PRIMARY,
            ),
            rx.el.button(
                "Cancel",
                type="button",
                on_click=AdminState.cancel_edit,
                disabled=AdminState.saving
                | AdminState.guest_saving
                | AdminState.loading
                | AdminState.guest_loading,
                class_name=BUTTON,
            ),
            class_name="mt-3 flex flex-wrap gap-2",
        ),
        on_submit=AdminState.save_name,
        class_name="mt-4 w-full rounded-2xl border border-[#D9D4C4] bg-[#FAF6EE] p-4",
    )


def remove_confirmation(item: AdminItem) -> rx.Component:
    return rx.el.div(
        rx.el.p(
            f"Remove {item['name']}?",
            class_name="text-sm font-semibold text-[#343D2B]",
        ),
        rx.el.p(
            "This removes it from recommendations and cannot be undone.",
            class_name="mt-1 text-sm text-[#69715D]",
        ),
        rx.el.div(
            rx.el.button(
                rx.cond(AdminState.saving, "Removing…", "Confirm remove"),
                type="button",
                on_click=AdminState.confirm_remove,
                disabled=AdminState.saving
                | AdminState.guest_saving
                | AdminState.loading
                | AdminState.guest_loading,
                class_name=DESTRUCTIVE,
            ),
            rx.el.button(
                "Cancel",
                type="button",
                on_click=AdminState.cancel_remove,
                disabled=AdminState.saving
                | AdminState.guest_saving
                | AdminState.loading
                | AdminState.guest_loading,
                class_name=BUTTON,
            ),
            class_name="mt-3 flex flex-wrap gap-2",
        ),
        role="group",
        aria_label=f"Confirm removal of {item['name']}",
        class_name="mt-4 rounded-2xl border border-[#D9B89F] bg-[#FDF0E5] p-4",
    )


def admin_item(item: AdminItem) -> rx.Component:
    return rx.el.li(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("utensils", class_name="h-5 w-5 text-[#B85732]"),
                    class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#F7EADF]",
                ),
                rx.el.div(
                    rx.el.h3(
                        item["name"],
                        class_name="break-words text-base font-semibold text-[#343D2B]",
                    ),
                    rx.cond(
                        item["claimed"],
                        rx.el.p(
                            f"Bringing it: {item['guest_name']}",
                            class_name="mt-1 break-words text-sm text-[#59634B]",
                        ),
                    ),
                    class_name="min-w-0 flex-1",
                ),
                item_status(item),
                class_name="flex min-w-0 flex-1 items-start gap-3",
            ),
            rx.cond(
                ~item["claimed"],
                rx.el.div(
                    rx.el.button(
                        "Edit",
                        type="button",
                        on_click=lambda: AdminState.begin_edit(item["id"]),
                        disabled=AdminState.saving
                        | AdminState.guest_saving
                        | AdminState.loading
                        | AdminState.guest_loading,
                        aria_label=f"Edit {item['name']}",
                        class_name=BUTTON,
                    ),
                    rx.el.button(
                        rx.cond(item["active"], "Hide", "Unhide"),
                        type="button",
                        on_click=lambda: AdminState.toggle_item(item["id"]),
                        disabled=AdminState.saving
                        | AdminState.guest_saving
                        | AdminState.loading
                        | AdminState.guest_loading,
                        aria_label=f"Change visibility of {item['name']}",
                        class_name=BUTTON,
                    ),
                    rx.el.button(
                        "Remove",
                        type="button",
                        on_click=lambda: AdminState.ask_remove(item["id"]),
                        disabled=AdminState.saving
                        | AdminState.guest_saving
                        | AdminState.loading
                        | AdminState.guest_loading,
                        aria_label=f"Remove {item['name']}",
                        class_name=REMOVE,
                    ),
                    class_name="flex shrink-0 flex-wrap gap-2",
                ),
            ),
            class_name="flex flex-col gap-3 md:flex-row md:items-center md:justify-between",
        ),
        rx.cond(AdminState.edit_id == item["id"], edit_form()),
        rx.cond(AdminState.remove_id == item["id"], remove_confirmation(item)),
        key=item["id"],
        class_name="border-b border-[#E5DECF] py-3 first:pt-0 last:border-b-0 last:pb-0",
    )


def guest_edit_form() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            "Edit guest",
            class_name="mb-4 text-base font-semibold text-[#343D2B]",
        ),
        rx.el.label(
            "Guest name",
            html_for="guest_edit_name",
            class_name="mb-2 block text-sm font-medium text-[#343D2B]",
        ),
        rx.el.input(
            id="guest_edit_name",
            name="guest_edit_name",
            form="admin-guest-save",
            value=AdminState.guest_edit_name,
            on_change=AdminState.update_guest_edit_name,
            key="guest-name-draft",
            required=True,
            max_length=100,
            disabled=AdminState.guest_saving
            | AdminState.saving
            | AdminState.loading
            | AdminState.guest_loading,
            class_name=INPUT,
        ),
        rx.el.label(
            "Contribution",
            html_for="guest_choice",
            class_name="mb-2 mt-4 block text-sm font-medium text-[#343D2B]",
        ),
        rx.el.div(
            rx.el.select(
                rx.cond(
                    (AdminState.guest_choice != "custom")
                    & (AdminState.guest_choice != "nothing")
                    & ~AdminState.guest_choices.pluck("value").contains(
                        AdminState.guest_choice
                    ),
                    rx.el.option(
                        "Previously selected dish — unavailable; choose another",
                        value=AdminState.guest_choice,
                        disabled=True,
                    ),
                ),
                rx.foreach(
                    AdminState.guest_choices,
                    lambda choice: rx.el.option(
                        choice["label"],
                        value=choice["value"],
                        key=choice["value"],
                    ),
                ),
                rx.el.option("Custom contribution", value="custom"),
                rx.el.option("Bringing good vibes", value="nothing"),
                id="guest_choice",
                name="guest_choice",
                form="admin-guest-save",
                value=AdminState.guest_choice,
                on_change=AdminState.set_guest_choice,
                required=True,
                disabled=AdminState.guest_saving
                | AdminState.saving
                | AdminState.loading
                | AdminState.guest_loading,
                class_name="h-12 w-full appearance-none rounded-2xl border border-[#D5D0BF] bg-white py-2 pl-4 pr-10 text-sm text-[#343D2B] focus-visible:outline-2 focus-visible:outline-[#B85732] disabled:opacity-60",
            ),
            rx.icon(
                "chevron-down",
                class_name="pointer-events-none absolute right-4 top-4 h-4 w-4 text-[#69715D]",
            ),
            class_name="relative w-full",
        ),
        rx.cond(
            AdminState.guest_choice == "custom",
            rx.el.div(
                rx.el.label(
                    "Custom contribution",
                    html_for="guest_custom_text",
                    class_name="mb-2 mt-4 block text-sm font-medium text-[#343D2B]",
                ),
                rx.el.input(
                    id="guest_custom_text",
                    name="guest_custom_text",
                    form="admin-guest-save",
                    value=AdminState.guest_custom_text,
                    on_change=AdminState.update_guest_custom_text,
                    key="guest-custom-draft",
                    required=True,
                    max_length=200,
                    disabled=AdminState.guest_saving
                    | AdminState.saving
                    | AdminState.loading
                    | AdminState.guest_loading,
                    class_name=INPUT,
                ),
            ),
        ),
        rx.el.form(
            rx.el.button(
                rx.cond(AdminState.guest_saving, "Saving…", "Save guest"),
                type="submit",
                disabled=AdminState.guest_saving
                | AdminState.saving
                | AdminState.guest_loading
                | AdminState.loading,
                class_name=PRIMARY,
            ),
            rx.el.button(
                "Cancel",
                type="button",
                on_click=AdminState.cancel_guest_edit,
                disabled=AdminState.guest_saving
                | AdminState.saving
                | AdminState.guest_loading
                | AdminState.loading,
                class_name=BUTTON,
            ),
            id="admin-guest-save",
            on_submit=AdminState.save_guest_draft,
            class_name="mt-4 flex flex-wrap gap-2",
        ),
        key=AdminState.guest_form_version,
        class_name="mt-4 w-full rounded-2xl border border-[#D9D4C4] bg-[#FAF6EE] p-4",
    )


def guest_remove_confirmation() -> rx.Component:
    return rx.el.div(
        rx.el.p(
            f"Remove {AdminState.guest_remove_name}?",
            class_name="break-words text-sm font-semibold text-[#343D2B]",
        ),
        rx.el.p(
            "This deletes only their RSVP and cannot be undone. If they reserved a recommended dish, it becomes available again when active.",
            class_name="mt-1 text-sm leading-relaxed text-[#69715D]",
        ),
        rx.el.div(
            rx.el.button(
                rx.cond(AdminState.guest_saving, "Removing…", "Confirm remove"),
                type="button",
                on_click=AdminState.confirm_remove_guest,
                disabled=AdminState.guest_saving
                | AdminState.saving
                | AdminState.guest_loading
                | AdminState.loading,
                class_name=DESTRUCTIVE,
            ),
            rx.el.button(
                "Cancel",
                type="button",
                on_click=AdminState.cancel_remove_guest,
                disabled=AdminState.guest_saving
                | AdminState.saving
                | AdminState.guest_loading
                | AdminState.loading,
                class_name=BUTTON,
            ),
            class_name="mt-3 flex flex-wrap gap-2",
        ),
        role="group",
        aria_label=f"Confirm removal of {AdminState.guest_remove_name}",
        class_name="mt-4 rounded-2xl border border-[#D9B89F] bg-[#FDF0E5] p-4",
    )


def admin_guest(guest: AdminGuest) -> rx.Component:
    return rx.el.li(
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    guest["name"],
                    class_name="break-words text-base font-semibold text-[#343D2B]",
                ),
                rx.el.p(
                    rx.cond(
                        guest["contribution"] == NOTHING,
                        "Bringing good vibes",
                        guest["contribution"],
                    ),
                    class_name="mt-1 break-words text-sm leading-relaxed text-[#59634B]",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.div(
                rx.el.button(
                    "Edit",
                    type="button",
                    on_click=lambda: AdminState.begin_guest_edit(guest["id"]),
                    aria_label=f"Edit guest {guest['name']}",
                    disabled=AdminState.guest_saving
                    | AdminState.saving
                    | AdminState.guest_loading
                    | AdminState.loading,
                    class_name=BUTTON,
                ),
                rx.el.button(
                    "Remove",
                    type="button",
                    on_click=lambda: AdminState.ask_remove_guest(guest["id"]),
                    aria_label=f"Remove guest {guest['name']}",
                    disabled=AdminState.guest_saving
                    | AdminState.saving
                    | AdminState.guest_loading
                    | AdminState.loading,
                    class_name=REMOVE,
                ),
                class_name="flex shrink-0 flex-wrap gap-2",
            ),
            class_name="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between",
        ),
        rx.cond(AdminState.guest_edit_id == guest["id"], guest_edit_form()),
        rx.cond(
            (AdminState.guest_remove_id == guest["id"])
            & AdminState.guest_remove_ready,
            guest_remove_confirmation(),
        ),
        key=guest["id"],
        class_name="border-b border-[#E5DECF] py-3 first:pt-0 last:border-b-0 last:pb-0",
    )


def admin_guests() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.h2(
                "Guests",
                class_name="font-['Playfair_Display'] text-3xl text-[#343D2B]",
            ),
            rx.el.button(
                rx.icon("refresh-cw", class_name="h-4 w-4"),
                "Refresh",
                type="button",
                on_click=AdminState.load_items,
                disabled=AdminState.guest_loading
                | AdminState.loading
                | AdminState.guest_saving
                | AdminState.saving,
                class_name=BUTTON,
            ),
            class_name="flex flex-wrap items-center justify-between gap-3",
        ),
        rx.cond(
            AdminState.guest_loaded,
            rx.el.p(
                AdminState.guest_count_label,
                class_name="mb-4 mt-2 text-sm text-[#69715D]",
            ),
            rx.el.p(
                rx.cond(
                    AdminState.guest_list_error != "",
                    "Guest count unavailable",
                    "Loading guest count…",
                ),
                class_name="mb-4 mt-2 text-sm text-[#69715D]",
            ),
        ),
        rx.cond(
            AdminState.guest_list_error != "",
            rx.el.p(
                AdminState.guest_list_error,
                role="alert",
                class_name="mb-4 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800",
            ),
        ),
        rx.cond(
            AdminState.guest_error != "",
            rx.el.p(
                AdminState.guest_error,
                role="alert",
                class_name="mb-4 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800",
            ),
        ),
        rx.cond(
            AdminState.guest_notice != "",
            rx.el.p(
                AdminState.guest_notice,
                role="status",
                class_name="mb-4 rounded-2xl bg-[#E7EBD9] p-4 text-sm text-[#455638]",
            ),
        ),
        rx.cond(
            AdminState.guest_loading,
            rx.el.p(
                "Loading guests and dish availability…",
                role="status",
                class_name="mb-4 animate-pulse text-sm text-[#69715D]",
            ),
        ),
        rx.cond(
            AdminState.guests.length() > 0,
            rx.el.ul(
                rx.foreach(AdminState.guests, admin_guest), class_name="w-full"
            ),
            rx.cond(
                ~AdminState.guest_loading & (AdminState.guest_list_error == ""),
                rx.el.p(
                    "No guests have RSVP’d yet.",
                    class_name="py-6 text-sm text-[#69715D]",
                ),
            ),
        ),
        aria_label="Guest management",
        class_name="mt-5 rounded-3xl border border-[#E5DECF] bg-[#FFFCF5] p-5 sm:p-6",
    )


def admin_recommendations() -> rx.Component:
    return rx.el.div(
        rx.el.section(
            rx.el.h2(
                "Add an item", class_name="text-lg font-semibold text-[#343D2B]"
            ),
            rx.el.form(
                rx.el.div(
                    rx.el.label(
                        "Item name",
                        html_for="item_name",
                        class_name="mb-2 block text-sm font-medium text-[#343D2B]",
                    ),
                    rx.el.input(
                        id="item_name",
                        name="item_name",
                        placeholder="e.g. Green beans",
                        default_value=AdminState.draft_name,
                        key=AdminState.draft_name,
                        required=True,
                        max_length=100,
                        disabled=AdminState.saving
                        | AdminState.guest_saving
                        | AdminState.loading
                        | AdminState.guest_loading,
                        class_name=INPUT,
                    ),
                    class_name="min-w-0 flex-1",
                ),
                rx.el.button(
                    rx.icon("plus", class_name="h-4 w-4"),
                    rx.cond(AdminState.saving, "Saving…", "Add item"),
                    type="submit",
                    disabled=AdminState.saving
                    | AdminState.guest_saving
                    | AdminState.loading
                    | AdminState.guest_loading,
                    class_name=PRIMARY,
                ),
                on_submit=AdminState.create_item,
                key=AdminState.form_version,
                class_name="mt-3 flex flex-col gap-3 sm:flex-row sm:items-end",
            ),
            class_name="mt-5 rounded-3xl border border-[#E5DECF] bg-[#FFFCF5] p-5 sm:p-6",
        ),
        rx.cond(
            AdminState.error != "",
            rx.el.p(
                AdminState.error,
                role="alert",
                class_name="mt-5 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800",
            ),
        ),
        rx.cond(
            AdminState.notice != "",
            rx.el.p(
                AdminState.notice,
                role="status",
                class_name="mt-5 rounded-2xl bg-[#E7EBD9] p-4 text-sm text-[#455638]",
            ),
        ),
        rx.el.section(
            rx.el.div(
                rx.el.h2(
                    "Items", class_name="text-lg font-semibold text-[#343D2B]"
                ),
                rx.el.button(
                    rx.icon("refresh-cw", class_name="h-4 w-4"),
                    "Refresh",
                    type="button",
                    on_click=AdminState.load_items,
                    disabled=AdminState.loading
                    | AdminState.saving
                    | AdminState.guest_loading
                    | AdminState.guest_saving,
                    class_name=BUTTON,
                ),
                class_name="mb-6 flex items-center justify-between gap-4",
            ),
            rx.cond(
                AdminState.loading & (AdminState.items.length() == 0),
                rx.el.p(
                    "Loading items…",
                    role="status",
                    class_name="animate-pulse py-6 text-sm text-[#69715D]",
                ),
                rx.cond(
                    AdminState.items.length() > 0,
                    rx.el.ul(
                        rx.foreach(AdminState.items, admin_item),
                        class_name="w-full",
                    ),
                    rx.el.p(
                        "No recommended items yet. Add an item above.",
                        class_name="py-6 text-sm text-[#69715D]",
                    ),
                ),
            ),
            class_name="mt-5 rounded-3xl border border-[#E5DECF] bg-[#FFFCF5] p-5 sm:p-6",
        ),
        class_name="w-full",
    )


def admin_content() -> rx.Component:
    return rx.el.div(
        rx.el.h1(
            "Admin",
            class_name="mb-5 font-['Playfair_Display'] text-4xl tracking-tight text-[#343D2B] sm:text-5xl",
        ),
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger(
                    "Guests",
                    value="guests",
                    class_name=TAB,
                    disabled=AdminState.saving
                    | AdminState.guest_saving
                    | AdminState.loading
                    | AdminState.guest_loading,
                ),
                rx.tabs.trigger(
                    "Recommended items",
                    value="recommendations",
                    class_name=TAB,
                    disabled=AdminState.saving
                    | AdminState.guest_saving
                    | AdminState.loading
                    | AdminState.guest_loading,
                ),
                aria_label="Thanksgiving admin sections",
                class_name="flex h-auto w-full flex-wrap gap-2 border-b border-[#D9D4C4] bg-transparent pb-3 text-[#343D2B] [&>div]:flex-wrap",
            ),
            rx.tabs.content(
                admin_guests(),
                value="guests",
                force_mount=True,
                hidden=AdminState.admin_tab != "guests",
                class_name=rx.cond(
                    AdminState.admin_tab == "guests",
                    "w-full text-[#343D2B] focus-visible:outline-2 focus-visible:outline-[#B85732]",
                    "!hidden",
                ),
            ),
            rx.tabs.content(
                admin_recommendations(),
                value="recommendations",
                force_mount=True,
                hidden=AdminState.admin_tab != "recommendations",
                class_name=rx.cond(
                    AdminState.admin_tab == "recommendations",
                    "w-full text-[#343D2B] focus-visible:outline-2 focus-visible:outline-[#B85732]",
                    "!hidden",
                ),
            ),
            value=AdminState.admin_tab,
            on_change=AdminState.set_admin_tab,
            class_name="w-full",
        ),
        class_name="w-full py-7 sm:py-9",
    )


def admin_page() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            rx.el.header(
                rx.el.a(
                    rx.icon("leaf", class_name="h-5 w-5 text-[#B85732]"),
                    rx.el.span(
                        "Thanksgiving",
                        class_name="font-['Playfair_Display'] text-xl text-[#343D2B]",
                    ),
                    href="/",
                    class_name="flex min-h-11 items-center gap-2 rounded-xl focus-visible:outline-2 focus-visible:outline-[#B85732]",
                ),
                rx.el.nav(
                    rx.el.a("Back to event", href="/", class_name=BUTTON),
                    rx.el.button(
                        "Sign out",
                        type="button",
                        on_click=User.logout,
                        class_name=BUTTON,
                    ),
                    aria_label="Admin navigation",
                    class_name="flex flex-wrap gap-2",
                ),
                class_name="flex flex-wrap items-center justify-between gap-3 border-b border-[#D9D4C4] py-5",
            ),
            rx.cond(
                ~AdminState.owner_ready,
                rx.el.p(
                    "Checking access…",
                    role="status",
                    class_name="py-12 text-sm text-[#69715D]",
                ),
                rx.cond(
                    AdminState.owner_allowed,
                    admin_content(),
                    rx.el.section(
                        rx.icon(
                            "lock-keyhole",
                            class_name="mb-5 h-8 w-8 text-[#B85732]",
                        ),
                        rx.el.h1(
                            "Access denied",
                            class_name="font-['Playfair_Display'] text-4xl text-[#343D2B]",
                        ),
                        rx.el.p(
                            rx.cond(
                                AdminState.access_error != "",
                                AdminState.access_error,
                                "Only the event admin can manage recommended items.",
                            ),
                            class_name="mt-4 text-sm leading-relaxed text-[#59634B]",
                        ),
                        rx.el.button(
                            "Retry access",
                            type="button",
                            on_click=AdminState.load_owner,
                            class_name=BUTTON,
                        ),
                        class_name="my-10 flex flex-col items-start gap-4 rounded-3xl border border-[#E5DECF] bg-[#FFFCF5] p-8",
                    ),
                ),
            ),
            class_name="mx-auto w-full max-w-[1100px] px-5 sm:px-8",
        ),
        class_name="min-h-dvh bg-[#FAF6EE] font-['Inter'] text-[#343D2B]",
    )
