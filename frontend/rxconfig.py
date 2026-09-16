"""Reflex application configuration."""

import reflex as rx

config = rx.Config(
    app_name="app",
    app_module_import="app",
    backend_port=8001,
    plugins=[
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(
                appearance="light",
                accent_color="plum",
                gray_color="mauve",
                radius="small",
            )
        ),
        rx.plugins.SitemapPlugin(),
    ],
)
