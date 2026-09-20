# T7-S manual Odoo setup

## Mandatory stop gate

These are administrator actions for the local `procurement_poc` development
database. They have not been performed by the implementation agent. Take a fresh
database backup first. Do not use the original `Procurement Integration` user or
change its T6 groups.

Do not create the T7 receipt fixture until the focused T7-S live contract passes.

## Why the dedicated user is mandatory

T7-S needs an Odoo identity so the side-by-side application can call the guarded
projection through JSON-2. The identity is deliberately separate from the existing
`Procurement Integration` user because Odoo ACLs are additive: adding T7-S access to
an identity that already has broader Purchase or Inventory permissions would make it
impossible to prove that the projection itself is the only readable inventory-history
surface.

The dedicated portal user is therefore a least-privilege security principal used only
for T7-S validation and, if retained, later read-only projection calls. Its API key
authenticates that principal; it does not create additional permissions. The custom
`T7-S Inventory-History Projection Reader` group permits only the guarded method call
and deliberately supplies no generic model ACL. This separation lets the acceptance
test prove both sides of the boundary: bounded same-company projection reads succeed,
while direct reads of `stock.picking`, `stock.move`, and `stock.move.line` remain
denied.

## 1. Make the local addon visible

The Compose file mounts `infra/odoo/addons` read-only and adds it to `addons_path`.
From the repository root, recreate only the Odoo service; do not remove volumes:

```powershell
$podmanPath = Join-Path $env:LOCALAPPDATA "Programs\Podman\podman.exe"
& $podmanPath compose --env-file .env -f infra/odoo/compose.yaml up -d --force-recreate odoo
& $podmanPath compose --env-file .env -f infra/odoo/compose.yaml logs --tail=100 odoo
```

Expected effect: Odoo restarts against the existing database and volumes, with
`/mnt/extra-addons` mounted read-only. Stop if the log reports an addon-path or
Python-import error.

## 2. Install the addon through Odoo

1. Sign in to the local Odoo database as an administrator.
2. Open **Settings** and activate **Developer mode**.
3. Open **Apps**.
4. Select **Update Apps List**, then confirm **Update**.
5. Clear the default **Apps** search filter if necessary.
6. Search the exact module name `T7-S Inventory-History Projection`.
7. Open it and select **Activate**.
8. Expected effect: installation succeeds without a new application menu. Do not
   install any suggested Inventory or Purchase role.

If the module is absent or installation fails, stop and preserve the exact error.
Do not edit the database or install it through a shell workaround.

## 3. Create a dedicated non-internal caller

1. Open **Contacts** and select **New**.
2. Create an individual contact named exactly
   `T7-S Inventory History Integration` with a unique local email address that you
   can use to sign in. Save it.
3. From the contact's **Action** menu, select **Grant portal access**.
4. Confirm the email/login and select **Grant Access**.
5. Open **Settings > Users section > Manage Users**.
6. Remove the default **Internal Users** filter, add the **Portal Users** filter,
   and open `T7-S Inventory History Integration`.
7. Confirm **User Type/Role** is **Portal**, **Companies** contains only the company
   validated as company ID 1, and **Default Company** is that same company. Save.

Safety stop: do not convert this identity to an internal user. Do not assign
**Role / User**, **Purchase / User**, **Purchase / Administrator**,
**Inventory / User**, or **Inventory / Administrator**.

## 4. Assign only the projection group

1. Still in developer mode, open
   **Settings > Technical > Users & Companies > Groups**.
2. Search the exact group
   `T7-S Inventory-History Projection Reader` and open it.
3. In **Users/Members**, add only `T7-S Inventory History Integration`.
4. Save.
5. Confirm the group has no inherited/implied groups and no Access Rights rows.

Expected effect: the user can pass the projection method's explicit group check but
receives no generic model ACL from this addon.

## 5. Generate the dedicated API key

Odoo 19 hides portal-user API-key creation unless an administrator enables its
dedicated portal setting, and the portal security page shows the section only in
developer mode. Enable this setting only long enough to create the key because it is
database-wide for portal users.

1. While signed in as an administrator with developer mode active, open
   **Settings > General Settings > Permissions > API Keys**.
2. Enable **Customers can generate API Keys** and select **Save**. Do not change the
   T7-S identity to an internal user and do not grant an Inventory or Purchase role.
3. Sign out of the administrator account.
4. Sign in as `T7-S Inventory History Integration`.
5. Open `/my/security?debug=1` on the local Odoo host. For the default local URL,
   use `http://localhost:8069/my/security?debug=1`.
6. Under **Developer API Keys**, select **New API Key**.
7. Use description `T7-S local projection validation`, choose **1 Day**, and confirm
   with the portal user's current password. A passkey and two-factor authentication
   are not required for this local validation step.
8. Copy the value immediately; Odoo displays it only once. Never paste it into a
   tracked file, terminal output, issue, or chat.
9. Sign back in as the administrator, return to
   **Settings > General Settings > Permissions > API Keys**, disable
   **Customers can generate API Keys**, and select **Save**. Disabling key generation
   does not revoke the key that was just created.
10. In the repository's ignored `.env`, set only:

   ```text
   ODOO_T7S_API_KEY=<the new key>
   RUN_T7S_LIVE_CONTRACTS=true
   ```

Keep the existing `ODOO_API_KEY` unchanged. Never paste either key into a tracked
file, terminal output, issue, or chat. If **Developer API Keys** does not appear after
the setting is saved and `/my/security?debug=1` is loaded, stop and report that exact
UI limitation; do not promote the user to an internal role as a workaround.

## 6. Run the focused security acceptance

From the repository root:

```powershell
pytest tests/integration/test_live_odoo_contract.py -m integration -k t7s -v
```

The contract must prove:

- a same-company bounded call succeeds;
- the response uses only the fixed sanitized schema;
- generic read/create/write/unlink rights are false on the projection;
- generic rights and direct `search_read` remain denied on `stock.picking`,
  `stock.move`, and `stock.move.line`;
- another company is rejected; and
- missing bounds, empty line IDs, an excessive limit, and a 367-day window are
  rejected.

Immediately set `RUN_T7S_LIVE_CONTRACTS=false` after the run. Preserve any failure
without granting extra access or editing records to force a pass.

## 7. Next gate

After the focused contract passes, report the result. The implementation agent will
review the evidence. Only then follow `docs/T7_FIXTURE_SETUP.md` to create the four
controlled T7 receipt scenarios and enable both T7-S and T7 gates for final live
validation.

## Rollback

1. Set `RUN_T7S_LIVE_CONTRACTS=false` and remove `ODOO_T7S_API_KEY` from `.env`.
2. From the dedicated user's **Account Security**, delete the T7-S API key.
3. Remove the user from `T7-S Inventory-History Projection Reader`.
4. Revoke portal access from the contact if the identity is no longer required.
5. Uninstall the addon only after confirming no validation depends on it.

Do not delete named volumes and do not use `podman compose down -v`.
