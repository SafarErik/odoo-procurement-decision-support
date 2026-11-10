"""Reflex build configuration: app module, backend port and the light iris/sage Radix
theme every component inherits (DESIGN.md tokens adjust its accent)."""

import reflex as rx

config = rx.Config(
    app_name="app",
    app_module_import="app",
    backend_port=8001,
    show_built_with_reflex=False,
    plugins=[
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(
                appearance="light",
                accent_color="iris",
                gray_color="sage",
                radius="small",
            )
        ),
        rx.plugins.SitemapPlugin(),
    ],
)
