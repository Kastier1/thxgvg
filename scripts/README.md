# Initial content and event checks

## Orchestrator: seed once after build

For the existing Thanksgiving event of 10–13 guests, the refined initial recommendations are, in order: Mashed potatoes, Stuffing, Cranberry sauce, Green beans, Veggies, Dinner rolls & butter, Pie, Non-alcoholic drinks, Beer, and Spirits. Pie is offered as one generic option rather than separate pumpkin and apple choices; beverages are three separate choices: non-alcoholic drinks, beer, and spirits. The default RSVP is Simon bringing “Turkey & Gravy,” established once through the managed data migration that replaces Ingrid’s existing Turkey RSVP. This combined contribution is reserved for Simon; Turkey gravy is no longer a separate remaining default choice.

Use the managed database `run_python` environment for explicit, once-only initial content setup: import `seed_default_recommendations_once` from `scripts.seed_recommendations` and await it (or call it through `asyncio.run` in a synchronous runner). The function inserts missing names with PostgreSQL `ON CONFLICT DO NOTHING` on `normalized_name`; it does not replace or reactivate existing rows, and it does not touch RSVPs or AdminOwner. The managed data migration separately establishes Simon’s default RSVP by updating Ingrid’s existing RSVP row to Simon and the canonical contribution “Turkey & Gravy,” reserving the combined contribution for Simon, and removing only the unclaimed separate Turkey gravy recommendation. On a fresh migrated database, create this same one-time default RSVP only when safe and unclaimed. Record completion in the orchestration step and do not rerun setup on refresh, restart, deployment, or after admins remove or hide choices. Preserve other guest and admin records, but do not automatically recreate any recommendation or RSVP after an admin edits or removes it. There is intentionally no automatic application seeding; do not blanket-reseed the current database. The public form handles an empty recommendation table.

## Event tests

The async suites accept an injected `run_event` adapter matching `scripts.test_rsvp.RunEvent`. The adapter must dispatch EventSpecs through the real application's event processor and authorization middleware, retain an independent session for each token, apply optional state overrides before dispatch, inject the test authenticated claims via the event test context, exhaust async-generator updates, execute returned/yielded event chains, and return the final flattened state snapshot. `claims=None` means an anonymous session. Do not use handler `.fn`, provider-state instantiation, mocks, or direct handler calls.

Run `run_public_tests(run_event)` and `run_admin_tests(run_event)` on a disposable migrated test database. The checks exercise anonymous validation, write-ins/nothing, duplicate submissions, availability refresh, stale and invalid IDs, concurrent claims, normalized duplicate names, unauthorized mutations despite forged visibility, item edits, hidden items, claimed-item immutability, and confirmed deletion persistence. Fixtures use unique names and remove only their own rows.

On a fresh disposable database only, explicitly run `test_singleton_bootstrap_on_empty_test_database(run_event)` first. It races two authenticated admin visits, asserts exactly one owner wins, and intentionally retains that singleton for the subsequent admin suite. Never run the bootstrap test against the deployed database or delete its actual owner. The first real authenticated visitor to `/admin` claims the deployed instance's admin ownership.

## Admin guest event checks

`run_admin_guest_tests(run_event)` in `scripts.test_admin_guests` uses the same adapter and existing admin identity. Run it on a disposable migrated test database with an owner already present. It creates uniquely named temporary recommendations and RSVPs and cleans up only its fixtures, never the owner or existing content. It covers prefilling an inactive current reservation, cancel/no-selection guards, trimming and length validation, canonical recommendation names/FKs, custom/nothing reservation release, claimed/hidden dish conflicts, unauthorized guest events despite forged view flags, cross-session stale edits, concurrent public/admin claiming, confirmed RSVP-only deletion, and public persistence refresh. The suite is supplied, not automatically executed by the app.

### New AdminState guest events

- `begin_guest_edit(guest_id: int)` reads persisted data and initializes the editor.
- `cancel_guest_edit()` closes the editor without writing.
- `save_guest(form_data)` submits `guest_edit_name`, `guest_choice`, and `guest_custom_text`. Missing keys retain the prefilled draft; a name-only submission retains the current reservation.
- `ask_remove_guest(guest_id: int)` reads the persisted guest and creates the explicit confirmation selection.
- `cancel_remove_guest()` clears the confirmation without deleting.
- `confirm_remove_guest()` takes no arguments and requires a valid selection established by `ask_remove_guest`.
- Existing `load_items()` now refreshes both guests and recommendation claims; existing `load_items_preserving_feedback()` refreshes both after mutations. Admin load continues through `load_owner()` with its unchanged policy.

### Guest fields and payload values

Every guest field and event is gated with `auth=is_admin`. View data: `guests` (each record has `id`, `name`, `contribution`, `recommended_item_id`, with `0` for no reservation), `guest_loaded`, `guest_loading`, `guest_saving`, `guest_list_error`, `guest_error`, `guest_notice`. Editor data: `guest_edit_id`, `guest_edit_name`, `guest_choice`, `guest_custom_text`, `guest_choices` (records with `value` and `label`), `guest_form_version`; snapshot fields: `guest_original_name`, `guest_original_contribution`, `guest_original_item_id`. Confirmation data: `guest_remove_id`, `guest_remove_ready`, `guest_remove_name`, `guest_remove_contribution`, `guest_remove_item_id`.

Choice values are the recommendation ID as a decimal string, `custom`, or `nothing`. Custom text is trimmed and required only for `custom`; `nothing` persists the exact contribution `Nothing — just bringing myself` with no FK. Prefer dispatching begin/ask events rather than overriding snapshot/selection fields. Invalid, stale, or unselected operations leave the database unchanged and populate `guest_error`; successful edits/deletions clear their panel selection, set `guest_notice`, and chain admin and current-session public refresh events. Cross-client live synchronization is not promised.

Sign-in discovery was already checked by the supplied platform execution (HTTP 200 JSON with an authorization endpoint). The final interactive sign-in still needs a person to click Sign in; these tests do not automate provider login.
