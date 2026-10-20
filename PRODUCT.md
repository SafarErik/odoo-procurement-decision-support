# Product

<!-- impeccable:product-schema 1 -->

Product context for design work, updated 2026-10-20. Requirements remain on Drive
(see [docs/agents/project-baseline.md](docs/agents/project-baseline.md)); the earlier
brief is kept in [docs/history/PRODUCT_2026-10-14.md](docs/history/PRODUCT_2026-10-14.md).

## Platform

web (Reflex), desktop-first with usable phone layouts.

## Users

A procurement buyer, including occasional users who need explanations of the inputs
and tradeoffs without knowing procurement terminology in advance.
The thesis demonstration uses the same honest workflow. Interface language is
Hungarian by default with an English switch; wording must read as natural
Hungarian procurement language, not a literal translation.

## Product Purpose

For one product and one approved demand, show which suppliers to buy from and how
much, what a lower-risk alternative costs, how disruptions change the plan, and let
the buyer record one deliberate decision that produces a purchase-order proposal PDF.

## Positioning

A Python helper beside Odoo 19. It reads quotations and supplier history, never
places orders and never writes business data to Odoo.

## Workflow and information architecture

Sidebar: Home (up to five recent pending and saved cases), Cases (searchable,
filterable saved comparisons), New procurement (start from Odoo quotations).
Preparation uses four freely revisitable steps: Quotations, Demand, Terms, Review.
Supplier terms are expandable; Odoo facts, buyer changes and unchanged suggestions
are distinguished. In-session drafts survive step and language changes; persistent
autosave is outside scope. Case creation explicitly calculates and saves; it does
not approve a plan.
A case has tabs: Overview, Suppliers, Plans, What if…?, Decision & PDF; Audit is a
secondary view for exact values, hashes, tree paths and provenance. Buyer views
use business language and charts first; system metadata stays in Audit.
Demo-data cases carry a visible badge and can be filtered; there is no separate
practice area.

## Constraints

- Saved cases are immutable; reopening never recalculates.
- Approval happens once per base case; scenarios cannot be approved; No-award has no PDF.
- The buyer UI requires a rationale for every decision, including minimum cost.
  The existing backend contract remains unchanged.
- The supplier score is an uncalibrated exposure signal, not a failure probability.
- Simulated scenario prices are assumptions, not Odoo facts.
- Tokens stay on the server; the browser never talks to Odoo or the database.
- Home lists are bounded recent records, not whole-library statistics.
- Retain the deep green, pale green and purple visual identity; no blue rebrand.
