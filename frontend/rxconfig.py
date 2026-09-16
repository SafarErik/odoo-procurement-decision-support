"""Reflex application configuration."""

import reflex as rx

config = rx.Config(
    app_name="app",
    app_module_import="app",
    backend_port=8001,
)
