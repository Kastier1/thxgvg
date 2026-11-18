import reflex as rx
import reflex_enterprise as rxe

from thanksgiving_gathering_planner.components.admin import admin_page
from thanksgiving_gathering_planner.components.invitation import invitation
from thanksgiving_gathering_planner.components.rsvp import guest_list, rsvp_panel
from thanksgiving_gathering_planner.states.admin_state import AdminState
from thanksgiving_gathering_planner.states.rsvp_state import RSVPState


def index() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            rx.el.header(
                rx.el.div(
                    rx.icon(
                        "leaf", class_name="h-5 w-5 -rotate-12 text-[#B85732]"
                    ),
                    rx.el.span(
                        "Thanksgiving",
                        class_name="font-['Playfair_Display'] text-xl tracking-tight text-[#343D2B]",
                    ),
                    class_name="flex items-center gap-2.5",
                ),
                rx.el.span(
                    "YOU’RE INVITED",
                    class_name="text-xs font-semibold tracking-[0.15em] text-[#69715D]",
                ),
                class_name="flex min-h-20 flex-wrap items-center justify-between gap-3 border-b border-[#D9D4C4] py-4",
            ),
            invitation(),
            rx.el.div(
                rsvp_panel(),
                guest_list(),
                class_name="grid w-full grid-cols-1 items-start gap-6 py-8 md:grid-cols-[minmax(0,1.8fr)_minmax(0,1fr)] md:gap-8 md:py-10",
            ),
            rx.el.footer(
                rx.icon("leaf", class_name="h-3.5 w-3.5 text-[#B85732]"),
                rx.el.span(
                    "Thanksgiving · 625 Market St SF Fl 6",
                    class_name="text-xs text-[#69715D]",
                ),
                rx.el.a(
                    "Admin",
                    href="/admin",
                    class_name="ml-3 inline-flex min-h-11 items-center rounded-xl px-3 text-sm font-medium text-[#9C492B] underline underline-offset-4 hover:bg-[#F1EBDD] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#B85732]",
                ),
                class_name="flex flex-wrap items-center justify-center gap-2 border-t border-[#D9D4C4] py-5",
            ),
            class_name="mx-auto w-full max-w-[1100px] px-5 sm:px-8",
        ),
        class_name="min-h-dvh bg-[#FAF6EE] font-['Inter'] text-[#343D2B] selection:bg-[#EBCAB6]",
    )


app = rxe.App(
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(
            rel="preconnect",
            href="https://fonts.gstatic.com",
            cross_origin="",
        ),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Playfair+Display:ital,wght@0,400;0,500;0,600;1,400&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(
    index,
    route="/",
    auth=False,
    title="Thanksgiving — RSVP",
    description="Join us for Thanksgiving on Thursday, November 26, 2026 at 4pm PST, at 625 Market St SF Fl 6. RSVP and choose what you’re bringing.",
    on_load=RSVPState.load_guests,
)
app.add_page(
    admin_page,
    route="/admin",
    auth=True,
    title="Admin — Thanksgiving",
    on_load=AdminState.load_owner,
)
