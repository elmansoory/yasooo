---
name: Parent portal access model
description: How parent read-only access (bearer codes) and the owner code-admin gate are designed in this Streamlit app, and why.
---

# Parent portal access model

The parent-facing page authenticates with a **bearer secret code only** (no member selectors/lists ever shown there). The owner manages codes on a SEPARATE sidebar page.

**Rule 1 — re-verify on every render, not just at login.**
Store only the code in `st.session_state` and re-check it each rerun (a lightweight `verify_code` that does NOT update `last_viewed_at`). Use the touching `authenticate` only at the login submit.
**Why:** Streamlit reruns top-to-bottom; if you cache the resolved member_id in session and trust it, a deactivated or regenerated code keeps working until logout. Re-verifying makes revocation/regeneration take effect immediately.
**How to apply:** any per-user session gated by a revocable token in this app should re-validate the token each render and clear all session artifacts (incl. cached PDF bytes) on logout/failed re-check.

**Rule 2 — gate the owner code-admin page with a PIN.**
The whole app has no global auth (single local owner assumption). The code-admin page can mint/reveal secret codes, so it is gated by an owner PIN stored as a salted SHA-256 hash in `data/club_settings.json` (`set_owner_pin`/`verify_owner_pin`/`has_owner_pin` in `src/utils/settings.py`), unlocked into `st.session_state["owner_unlocked"]`.
**Why:** "separate sidebar page" alone is not protection — if the app is ever shared/deployed, any visitor could open it. Full app-wide login is a larger separate feature; the PIN is the proportionate mitigation for the one secret-minting surface.

# Finance membership status (related)
`membership_status` distinguishes three NULL-ish cases, do not collapse them:
- no membership row at all → `none` (no subscription)
- has a membership row but NULL/invalid `payment_date` → `unknown` (cannot compute expiry; NOT expired)
- valid date → compute expiry via SQL `date(payment_date,'+N months')`.
Pick the latest membership row by `date(payment_date) DESC, id DESC` WITHOUT filtering out NULL dates, and detect existence via the joined `membership_id`.
