# Decision Core

This directory is reserved for the ERP-independent Decision Core. T0 intentionally
contains no domain model, scoring, ranking, constraint, or persistence logic.

Future code here must not import Odoo, FastAPI, Reflex, or database frameworks.
