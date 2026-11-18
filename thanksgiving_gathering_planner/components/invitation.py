import reflex as rx


def autumn_art() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="absolute left-7 top-4 h-64 w-64 rounded-full bg-[#465139] md:h-72 md:w-72"
        ),
        rx.el.div(
            rx.el.div(
                class_name="absolute bottom-0 left-20 h-64 w-px -rotate-[24deg] bg-[#798363]"
            ),
            rx.el.div(
                class_name="absolute left-7 top-4 h-16 w-9 -rotate-[65deg] rounded-[100%_0_100%_0] bg-[#92997A]"
            ),
            rx.el.div(
                class_name="absolute left-16 top-14 h-20 w-10 rotate-[15deg] rounded-[0_100%_0_100%] bg-[#788263]"
            ),
            rx.el.div(
                class_name="absolute left-0 top-20 h-20 w-11 -rotate-[65deg] rounded-[100%_0_100%_0] bg-[#788263]"
            ),
            rx.el.div(
                class_name="absolute left-10 top-32 h-20 w-10 rotate-[15deg] rounded-[0_100%_0_100%] bg-[#92997A]"
            ),
            class_name="absolute left-0 top-6 h-64 w-32 -rotate-[15deg]",
        ),
        rx.el.div(
            rx.el.div(
                class_name="absolute -top-8 left-[45%] h-12 w-5 -rotate-12 rounded-t-lg bg-[#5F6548]"
            ),
            rx.el.div(
                class_name="absolute inset-x-0 top-0 h-44 rounded-[48%] bg-[#C87443]"
            ),
            rx.el.div(
                class_name="absolute left-[12%] top-0 h-44 w-[76%] rounded-[48%] border-x-2 border-[#A85532]/45 bg-[#D68A51]"
            ),
            rx.el.div(
                class_name="absolute left-[28%] top-0 h-44 w-[44%] rounded-[48%] border-x-2 border-[#A85532]/45 bg-[#DC9458]"
            ),
            rx.el.div(
                class_name="absolute left-[43%] top-0 h-44 w-[15%] rounded-[48%] border-x border-[#A85532]/30 bg-[#E2A168]"
            ),
            class_name="absolute bottom-9 right-4 h-44 w-64 rotate-[5deg]",
        ),
        rx.el.div(
            rx.el.div(
                class_name="absolute -top-4 left-[45%] h-7 w-3 rotate-12 rounded-t-md bg-[#686B4D]"
            ),
            rx.el.div(class_name="absolute inset-0 rounded-[48%] bg-[#DDD0A4]"),
            rx.el.div(
                class_name="absolute inset-y-0 left-[18%] w-[64%] rounded-[48%] border-x-2 border-[#BBAA74] bg-[#E8DDB6]"
            ),
            rx.el.div(
                class_name="absolute inset-y-0 left-[38%] w-[24%] rounded-[48%] border-x border-[#BBAA74] bg-[#EDE3C3]"
            ),
            class_name="absolute bottom-3 left-8 h-24 w-32 -rotate-12",
        ),
        rx.el.div(
            class_name="absolute bottom-1 right-1 h-px w-80 bg-[#DDD0A4]/30"
        ),
        rx.el.div(
            class_name="absolute right-0 top-10 h-10 w-6 rotate-45 rounded-[100%_0_100%_0] bg-[#B69A57]"
        ),
        rx.el.div(
            class_name="absolute right-6 top-0 h-5 w-3 -rotate-12 rounded-[100%_0_100%_0] bg-[#B85732]/70"
        ),
        aria_hidden=True,
        class_name="relative mx-auto hidden h-[350px] w-[360px] max-w-full md:block",
    )


def invitation() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.h1(
                "Thanksgiving",
                class_name="font-['Playfair_Display'] text-[clamp(2.6rem,6.7vw,5.5rem)] leading-[1.1] tracking-[-0.045em] text-[#FFF7E6]",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.p(
                        "WHEN",
                        class_name="mb-2 text-xs font-semibold tracking-[0.15em] text-[#DDDCC3]",
                    ),
                    rx.el.p(
                        "Thursday, November 26, 2026",
                        class_name="mb-2 text-sm font-medium leading-relaxed text-[#FFF7E6]",
                    ),
                    rx.el.p(
                        rx.icon(
                            "clock-3",
                            class_name="h-4 w-4 shrink-0 text-[#E6B882]",
                        ),
                        "4pm PST",
                        class_name="flex items-center gap-2.5 text-sm font-medium text-[#FFF7E6]",
                    ),
                    class_name="rounded-2xl border border-[#F6EBD2]/15 bg-[#FFF7E6]/5 px-5 py-4",
                ),
                rx.el.div(
                    rx.el.p(
                        "WHERE",
                        class_name="mb-2 text-xs font-semibold tracking-[0.15em] text-[#DDDCC3]",
                    ),
                    rx.el.a(
                        rx.icon(
                            "map-pin",
                            class_name="mt-0.5 h-4 w-4 shrink-0 text-[#E6B882]",
                        ),
                        "625 Market St SF Fl 6",
                        href="https://www.google.com/maps/search/?api=1&query=625%20Market%20St%2C%20San%20Francisco%2C%20CA",
                        target="_blank",
                        rel="noopener noreferrer",
                        aria_label="Open 625 Market St, San Francisco in Google Maps (opens in a new tab)",
                        class_name="flex items-start gap-2.5 text-sm font-medium text-[#FFF7E6] underline underline-offset-4 hover:decoration-[#E6B882] focus-visible:rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#E6B882]",
                    ),
                    class_name="rounded-2xl border border-[#F6EBD2]/15 bg-[#FFF7E6]/5 px-5 py-4",
                ),
                class_name="mt-5 flex flex-wrap gap-3 md:mt-8",
            ),
            rx.el.p(
                "Around 10–13 guests",
                class_name="mt-4 text-sm text-[#DDDCC3]",
            ),
            class_name="relative z-10 min-w-0 py-3 md:py-10",
        ),
        autumn_art(),
        aria_label="Thanksgiving event details",
        class_name="mt-6 grid items-center gap-4 overflow-hidden rounded-3xl bg-[#343D2B] px-6 py-7 sm:px-10 md:grid-cols-[1.65fr_1fr] md:gap-0 md:px-12 md:py-7",
    )
