import reflex as rx
import reflex_enterprise as rxe

config = rxe.Config(
    app_name="thanksgiving_gathering_planner",
    default_color_mode="light",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        rxe.AuthPlugin(auth=True, login_page="app.pages.auth_login.login_page"),
    ],
)
