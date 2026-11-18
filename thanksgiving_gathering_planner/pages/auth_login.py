import reflex as rx
import reflex_enterprise as rxe

import os
from collections.abc import Sequence

from reflex_enterprise.auth import AuthUserState

_PROVIDER_NAME = os.environ.get("OIDC_PROVIDER_NAME", "")
_LOGIN_LABEL = (
    f"Continue with {_PROVIDER_NAME}" if _PROVIDER_NAME else "Sign in"
)


class LoginRedirectState(rx.State):
    @rxe.event(auth=False)
    def continue_to_app(self):
        raw = self.router.page.params.get("redirect_to", "/")
        target = (
            raw
            if isinstance(raw, str)
            and raw.startswith("/")
            and not raw.startswith("//")
            and not any(c in raw for c in "\t\r\n\\")
            else "/"
        )
        return rx.redirect(target)


def _login_buttons(providers: Sequence) -> list[rx.Component]:
    return [
        provider.get_login_button(
            rx.el.button(
                _LOGIN_LABEL,
                type="button",
                class_name="flex min-h-12 w-full items-center justify-center rounded-2xl bg-[#B85732] px-5 py-3 text-sm font-semibold text-white hover:bg-[#9C492B] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#B85732]",
            )
        )
        for provider in providers
    ]


def login_page(*, providers: Sequence, **context) -> rx.Component:
    return rx.fragment(
        rx.el.main(
            rx.el.section(
                rx.icon(
                    "leaf", class_name="mx-auto mb-5 h-8 w-8 text-[#B85732]"
                ),
                rx.el.h1(
                    "Thanksgiving",
                    class_name="font-['Playfair_Display'] text-4xl text-[#343D2B]",
                ),
                rx.el.p(
                    "Sign in to access admin.",
                    class_name="mb-8 mt-4 text-sm text-[#69715D]",
                ),
                *_login_buttons(providers),
                rx.el.a(
                    "Back to event",
                    href="/",
                    class_name="mt-6 inline-block rounded-sm text-sm text-[#9C492B] underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#B85732]",
                ),
                class_name="w-full max-w-md rounded-3xl border border-[#D9D4C4] bg-[#FFFCF5] p-8 text-center sm:p-10",
            ),
            class_name="flex min-h-dvh items-center justify-center bg-[#FAF6EE] p-5 font-['Inter'] text-[#343D2B]",
        ),
        rx.cond(
            AuthUserState.provider_name != "",
            rx.el.div(on_mount=LoginRedirectState.continue_to_app),
        ),
    )
