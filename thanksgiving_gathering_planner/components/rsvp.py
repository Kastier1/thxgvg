import reflex as rx

from thanksgiving_gathering_planner.states.rsvp_state import Guest, NOTHING, Recommendation, RSVPState


def contribution_tile(item: Recommendation) -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.icon("utensils", class_name="h-5 w-5 text-[#B85732]"),
            class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-[#F7EADF]",
        ),
        rx.el.div(
            rx.el.span(
                item["name"],
                class_name="block break-words text-sm font-semibold text-[#343D2B]",
            ),
            rx.el.span(
                "Available", class_name="mt-1 block text-xs text-[#59634B]"
            ),
            class_name="min-w-0 flex-1 text-left",
        ),
        rx.cond(
            RSVPState.selection == item["id"].to_string(),
            rx.icon(
                "circle-check", class_name="h-5 w-5 shrink-0 text-[#B85732]"
            ),
            rx.el.span(
                class_name="h-5 w-5 shrink-0 rounded-full border border-[#CFCAB9]"
            ),
        ),
        type="button",
        on_click=lambda: RSVPState.select_contribution(item["id"].to_string()),
        disabled=RSVPState.saving | RSVPState.submitted,
        aria_pressed=RSVPState.selection == item["id"].to_string(),
        key=item["id"],
        class_name=rx.cond(
            RSVPState.selection == item["id"].to_string(),
            "flex min-h-20 w-full items-center gap-3 rounded-2xl border-2 border-[#B85732] bg-[#FDF0E5] p-3 text-[#343D2B] transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#B85732] disabled:opacity-60",
            "flex min-h-20 w-full items-center gap-3 rounded-2xl border-2 border-[#E6E0D4] bg-[#FFFCF5] p-3 text-[#343D2B] transition-colors hover:border-[#B85732]/60 hover:bg-[#F7F0E5] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#B85732] disabled:opacity-60",
        ),
    )


def mode_choice(label: str, choice: str, icon: str) -> rx.Component:
    return rx.el.button(
        rx.icon(icon, class_name="h-4 w-4 shrink-0"),
        rx.el.span(label, class_name="flex-1 text-left"),
        rx.cond(
            RSVPState.contribution_mode == choice,
            rx.icon("check", class_name="h-4 w-4"),
        ),
        type="button",
        on_click=lambda: RSVPState.set_contribution_mode(choice),
        disabled=RSVPState.saving | RSVPState.submitted,
        aria_pressed=RSVPState.contribution_mode == choice,
        class_name=rx.cond(
            RSVPState.contribution_mode == choice,
            "flex min-h-11 w-full items-center gap-3 rounded-2xl border border-[#B85732] bg-[#F7EADF] px-4 py-3.5 text-sm font-medium text-[#9C492B] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#B85732] disabled:opacity-60",
            "flex min-h-11 w-full items-center gap-3 rounded-2xl border border-[#DEDACD] bg-[#FFFCF5] px-4 py-3.5 text-sm font-medium text-[#59634B] hover:border-[#B85732] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#B85732] disabled:opacity-60",
        ),
    )


def dish_choices() -> rx.Component:
    return rx.el.div(
        rx.el.p(
            "Claimed dishes are removed from these choices. See who’s bringing what in the guest list.",
            class_name="mb-3 text-xs leading-relaxed text-[#69715D]",
        ),
        rx.cond(
            RSVPState.loading & (RSVPState.recommendations.length() == 0),
            rx.el.p(
                "Loading available items…",
                role="status",
                class_name="animate-pulse rounded-2xl bg-[#F3EEE2] p-4 text-sm text-[#59634B]",
            ),
            rx.cond(
                RSVPState.recommendations.length() > 0,
                rx.el.div(
                    rx.foreach(RSVPState.recommendations, contribution_tile),
                    class_name="grid grid-cols-1 gap-3 min-[520px]:grid-cols-2",
                ),
                rx.el.p(
                    "No recommended items are available. Bring something else, or bring good vibes.",
                    class_name="rounded-2xl bg-[#F3EEE2] p-4 text-sm leading-relaxed text-[#59634B]",
                ),
            ),
        ),
        rx.el.div(
            rx.el.p(
                "Your dish is reserved when you confirm your RSVP.",
                class_name="text-xs leading-relaxed text-[#69715D]",
            ),
            rx.el.button(
                rx.icon("refresh-cw", class_name="h-3.5 w-3.5"),
                "Refresh choices",
                type="button",
                on_click=RSVPState.load_guests,
                disabled=RSVPState.loading
                | RSVPState.saving
                | RSVPState.submitted,
                class_name="flex min-h-11 shrink-0 items-center gap-2 rounded-xl px-2 text-xs font-medium text-[#59634B] hover:bg-[#F1EBDD] hover:text-[#9C492B] focus-visible:outline-2 focus-visible:outline-[#B85732] disabled:opacity-60",
            ),
            class_name="mt-2 flex flex-wrap items-center justify-between gap-x-2",
        ),
    )


def custom_contribution() -> rx.Component:
    return rx.el.div(
        rx.el.label(
            "Your contribution",
            html_for="custom_text",
            class_name="mb-2 block text-sm font-medium text-[#343D2B]",
        ),
        rx.el.input(
            id="custom_text",
            name="custom_text",
            form="rsvp-confirm",
            placeholder="What are you bringing?",
            value=RSVPState.custom_text,
            on_change=RSVPState.update_custom_text,
            key="custom-contribution-draft",
            required=True,
            max_length=200,
            disabled=RSVPState.saving | RSVPState.submitted,
            class_name="h-12 w-full rounded-2xl border border-[#D5D0BF] bg-[#FFFCF5] px-4 text-base text-[#343D2B] placeholder:text-[#7D806F] focus:border-[#B85732] focus:outline-2 focus:outline-[#B85732]/20 disabled:opacity-60",
        ),
        class_name="rounded-2xl bg-[#F3EEE2] p-4",
    )


def rsvp_form() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.label(
                rx.el.span(
                    "1",
                    class_name="mr-2 inline-flex h-7 w-7 items-center justify-center rounded-full bg-[#EAECDD] text-sm text-[#343D2B]",
                ),
                "Your name",
                rx.el.span(" *", class_name="text-[#B85732]"),
                html_for="guest_name",
                class_name="mb-2.5 block text-sm font-semibold text-[#343D2B]",
            ),
            rx.el.input(
                id="guest_name",
                name="guest_name",
                form="rsvp-confirm",
                placeholder="First and last name",
                value=RSVPState.guest_name,
                on_change=RSVPState.update_guest_name,
                key="guest-name-draft",
                required=True,
                max_length=100,
                auto_complete="name",
                disabled=RSVPState.saving | RSVPState.submitted,
                class_name="h-14 w-full rounded-2xl border border-[#D5D0BF] bg-[#FFFCF5] px-4 text-base text-[#343D2B] placeholder:text-[#7D806F] focus:border-[#B85732] focus:outline-2 focus:outline-[#B85732]/20 disabled:opacity-60",
            ),
            class_name="mb-6",
        ),
        rx.el.fieldset(
            rx.el.legend(
                rx.el.span(
                    "2",
                    class_name="mr-2 inline-flex h-7 w-7 items-center justify-center rounded-full bg-[#EAECDD] text-sm text-[#343D2B]",
                ),
                "What are you bringing",
                class_name="text-sm font-semibold text-[#343D2B]",
            ),
            rx.el.p(
                "Choose something for the table, or simply bring yourself.",
                class_name="mb-5 mt-2 text-sm leading-relaxed text-[#69715D]",
            ),
            rx.el.div(
                mode_choice("Choose a dish", "dish", "utensils"),
                mode_choice("Bring something else", "custom", "pencil-line"),
                mode_choice("Bringing good vibes", "myself", "smile"),
                role="group",
                aria_label="Contribution options",
                class_name="mb-4 flex flex-col gap-2",
            ),
            rx.match(
                RSVPState.contribution_mode,
                ("dish", dish_choices()),
                ("custom", custom_contribution()),
                (
                    "myself",
                    rx.el.p(
                        "Bringing good vibes — we’re happy you’re joining us.",
                        class_name="rounded-2xl border border-[#D9DFCA] bg-[#EEF0E4] p-4 text-sm leading-relaxed text-[#455638]",
                    ),
                ),
                rx.el.p(
                    "Choose a contribution option above.",
                    class_name="text-sm text-[#69715D]",
                ),
            ),
        ),
        rx.cond(
            RSVPState.error != "",
            rx.el.p(
                RSVPState.error,
                role="alert",
                class_name="mt-5 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800",
            ),
        ),
        rx.el.div(
            rx.el.p(
                RSVPState.contribution_summary,
                class_name="break-words text-sm font-semibold text-[#343D2B]",
            ),
            rx.el.p(
                "Confirm below to save your RSVP.",
                class_name="mt-1 text-xs text-[#69715D]",
            ),
            aria_live="polite",
            aria_atomic=True,
            class_name="mt-5 rounded-2xl border border-[#D9D4C4] bg-[#F7F2E7] p-3",
        ),
        rx.el.form(
            rx.el.button(
                rx.cond(RSVPState.saving, "Saving your RSVP…", "Confirm RSVP"),
                rx.cond(
                    RSVPState.saving,
                    rx.icon("loader-circle", class_name="h-4 w-4 animate-spin"),
                    rx.icon("arrow-right", class_name="h-4 w-4"),
                ),
                type="submit",
                disabled=RSVPState.saving | RSVPState.submitted,
                class_name="mt-3 flex h-14 w-full items-center justify-center gap-3 rounded-2xl bg-[#B85732] text-sm font-semibold text-white transition-colors hover:bg-[#9C492B] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#B85732] disabled:cursor-wait disabled:opacity-70",
            ),
            id="rsvp-confirm",
            on_submit=RSVPState.confirm_response,
        ),
        rx.cond(
            RSVPState.list_error != "",
            rx.el.p(
                RSVPState.list_error,
                role="alert",
                class_name="mt-4 text-sm text-red-800",
            ),
        ),
        rx.el.p(
            "Your name and contribution will appear on the guest list.",
            class_name="mt-3 text-center text-xs leading-relaxed text-[#69715D]",
        ),
        key=RSVPState.form_version,
        class_name="mt-5",
    )


def success_message() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("check", class_name="h-6 w-6 text-[#536442]"),
            class_name="mb-6 flex h-14 w-14 items-center justify-center rounded-full bg-[#E6EBD9]",
        ),
        rx.el.h3(
            f"You’re on the list, {RSVPState.saved_name}.",
            class_name="font-['Playfair_Display'] text-3xl leading-snug text-[#343D2B]",
        ),
        rx.el.p(
            "Your RSVP is saved. Thank you for joining us.",
            class_name="mt-4 text-sm leading-relaxed text-[#626B54]",
        ),
        rx.el.div(
            rx.el.p(
                "YOUR CONTRIBUTION",
                class_name="mb-2 text-xs font-semibold tracking-widest text-[#69715D]",
            ),
            rx.el.p(
                rx.cond(
                    RSVPState.saved_contribution == NOTHING,
                    "Bringing good vibes",
                    RSVPState.saved_contribution,
                ),
                class_name="text-base font-medium text-[#343D2B]",
            ),
            class_name="my-7 rounded-2xl border border-[#D9D4C4] bg-[#F7F2E7] p-5",
        ),
        rx.el.button(
            "Add another guest",
            rx.icon("arrow-right", class_name="h-4 w-4"),
            type="button",
            on_click=RSVPState.new_response,
            disabled=RSVPState.saving,
            class_name="flex min-h-11 items-center gap-3 rounded-2xl bg-[#B85732] px-5 py-3 text-sm font-semibold text-white hover:bg-[#9C492B] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#B85732] disabled:opacity-60",
        ),
        role="status",
        class_name="py-9",
    )


def rsvp_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    "YOU’RE INVITED",
                    class_name="mb-2 text-xs font-semibold tracking-[0.15em] text-[#9C492B]",
                ),
                rx.el.h2(
                    "RSVP",
                    class_name="font-['Playfair_Display'] text-[32px] tracking-tight text-[#343D2B]",
                ),
            ),
            rx.icon("utensils", class_name="h-7 w-7 text-[#959C80]"),
            class_name="flex items-center justify-between",
        ),
        rx.cond(RSVPState.submitted, success_message(), rsvp_form()),
        aria_label="RSVP for Thanksgiving",
        class_name="rounded-3xl border border-[#E5DECF] bg-[#FFFCF5] p-5 sm:p-8",
    )


def guest_row(guest: Guest) -> rx.Component:
    return rx.el.li(
        rx.el.div(
            rx.icon("user-round", class_name="h-4 w-4 text-[#6D775C]"),
            class_name="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#EAECDD]",
        ),
        rx.el.div(
            rx.el.p(
                guest["name"],
                class_name="break-words text-sm font-semibold text-[#343D2B]",
            ),
            rx.el.p(
                rx.cond(
                    guest["contribution"] == NOTHING,
                    "Bringing good vibes",
                    guest["contribution"],
                ),
                class_name="mt-1 break-words text-xs leading-relaxed text-[#69715D]",
            ),
            class_name="min-w-0 flex-1",
        ),
        key=guest["id"],
        class_name="flex items-start gap-3 border-b border-[#DDD8C9] py-5 last:border-b-0",
    )


def guest_list() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Who’s joining",
                    class_name="font-['Playfair_Display'] text-[30px] tracking-tight text-[#343D2B]",
                ),
                rx.el.span(
                    RSVPState.guests.length(),
                    class_name="flex h-7 min-w-7 items-center justify-center rounded-full bg-[#E9EBDD] px-2 text-xs font-semibold text-[#536442]",
                ),
                class_name="flex items-center gap-3",
            ),
            rx.el.p(
                "Our guests and what they’re bringing.",
                class_name="mt-3 text-sm leading-relaxed text-[#69715D]",
            ),
            class_name="border-b border-[#D9D4C4] pb-6",
        ),
        rx.cond(
            RSVPState.list_error != "",
            rx.el.p(
                RSVPState.list_error,
                role="alert",
                class_name="mt-4 rounded-2xl bg-red-50 p-3 text-sm text-red-800",
            ),
        ),
        rx.cond(
            RSVPState.loading & (RSVPState.guests.length() == 0),
            rx.el.p(
                "Loading the guest list…",
                role="status",
                class_name="py-9 text-sm text-[#69715D]",
            ),
            rx.cond(
                RSVPState.guests.length() > 0,
                rx.el.ul(
                    rx.foreach(RSVPState.guests, guest_row), class_name="w-full"
                ),
                rx.cond(
                    RSVPState.list_error == "",
                    rx.el.div(
                        rx.icon(
                            "sprout", class_name="mb-4 h-8 w-8 text-[#84916D]"
                        ),
                        rx.el.p(
                            "The table is waiting.",
                            class_name="font-['Playfair_Display'] text-xl text-[#343D2B]",
                        ),
                        rx.el.p(
                            "No RSVPs yet. Be the first to take a seat.",
                            class_name="mt-2 max-w-56 text-sm leading-relaxed text-[#69715D]",
                        ),
                        class_name="py-9",
                    ),
                ),
            ),
        ),
        rx.el.button(
            rx.icon(
                "refresh-cw",
                class_name=rx.cond(
                    RSVPState.loading, "h-3.5 w-3.5 animate-spin", "h-3.5 w-3.5"
                ),
            ),
            "Refresh list",
            type="button",
            on_click=RSVPState.load_guests,
            disabled=RSVPState.loading,
            class_name="mt-4 flex min-h-11 items-center gap-2 rounded-xl px-2 text-sm font-medium text-[#59634B] hover:bg-[#E4E8D5] hover:text-[#9C492B] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#B85732] disabled:opacity-60",
        ),
        aria_label="Submitted guest list",
        class_name="min-w-0 rounded-3xl border border-[#D9DFCA] bg-[#EEF0E4] p-6 sm:p-8",
    )
