"""Identifiers written into stored planning records.

Every value here is a stored contract id: saved cases, decisions, PDFs or idempotency
fingerprints contain it, so changing a value makes existing records unreadable or makes
an exact retry look like a new request. The ``t14``/``t15``/``t17`` names are historical.
"""

# Stored contract id; changing it breaks stored records. Also the persistence check constraint.
SNAPSHOT_VERSION = "t15-controlled-planning-v1"
# Stored contract id; changing it breaks stored records.
DECISION_VERSION = "t17-final-decision-v1"
# Stored contract id; changing it breaks stored records.
CONTENT_VERSION = "t17-approved-planning-v1"
# Stored contract id; changing it breaks stored PDF references.
DOCUMENT_VERSION = "t17-approved-pdf-v3"
# Stored contract id (``facts.input_kind``); changing it breaks stored records.
HISTORY_INPUT_KIND = "odoo_quotations_odoo_history"

# Stored risk-context reference prefixes; changing them breaks stored records.
ASSESSMENTS_REFERENCE_PREFIX = "t14-assessments:"
VALIDITY_REFERENCE_PREFIX = "t14-quantity-independent-controlled-proxy:"
# Stored in every assessment's quantity validity; changing it breaks stored records.
SCORE_QUANTITIES_REFERENCE = "controlled-proxy-v1"
# Part of the caller fingerprint of a creation request; changing it breaks exact retries.
PENDING_HISTORY_REFERENCE = "backend-owned-odoo-history"
