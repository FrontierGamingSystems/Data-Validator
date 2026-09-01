# Setup

Every step is a **direct link**. Click it and you land on the right page.

**You never open bms-production.** Nothing in the e-commerce project is opened,
created, edited or deleted.

---

# STEP 1 — get a token

**Click:** https://supabase.com/dashboard/account/tokens

- Click **Generate new token**
- Name it: `session-figures`
- Click **Generate token**
- **Copy it now** — Supabase shows it once and never again
- Paste it into Notepad. It starts `sbp_`

---

# STEP 2 — paste it in

**Click:** https://supabase.com/dashboard/project/lkcfbgnuodqzvowschjn/settings/functions

That is **Operational DB**.

- Click **Add new secret**
- Name: `SUPABASE_PAT`
- Value: paste the `sbp_...` line from Notepad
- Click **Save**

---

# STEP 3 — test it

**Click:** https://supabase.com/dashboard/project/lkcfbgnuodqzvowschjn/functions/session-figures

- Click the **Test** tab
- In the body box, delete what's there and type: `{"probe": true}`
- Click **Send**

You want:

```json
{ "ok": true, "sessions_visible": 270, "writes_refused": true }
```

If `"ok": false` — read the `error` line, it names the fix.

---

# STEP 4 — make two logins

**Click:** https://supabase.com/dashboard/project/lkcfbgnuodqzvowschjn/auth/users

- **Add user** → **Create new user**
- Email: `rwc@frontiergamingsystems.com`
- Password: your choice
- Tick **Auto Confirm User**
- **Create user**

Do it again for `sc@frontiergamingsystems.com`.

---

# STEP 5 — upload the app

**Click:** https://github.com/FrontierGamingSystems/Data-Validator/edit/main/index.html

- Ctrl+A, Delete
- Open `index.html` from this folder in Notepad → Ctrl+A → Ctrl+C
- Click in the GitHub box → Ctrl+V
- Click **Commit changes**

---

# STEP 6 — check it

**Click:** https://frontiergamingsystems.github.io/Data-Validator/

- Press **Ctrl+Shift+R**
- Sign in as `rwc@frontiergamingsystems.com`
- Hall **Redwood City**, date **2026-08-11**, click **Start**

**Should read $38,619 · attendance 142 · people 160.**

---

## If something breaks

| On screen | Redo step |
|---|---|
| "Set ONE of these as a secret" | 2 |
| "SUPABASE_PAT was rejected" | 1 — token wrong or expired |
| "cannot reach the e-commerce project" | 1 — generate it from the account that can see the **FGS** organisation |
| Cannot sign in | 4 |
| Old version still showing | 6 — Ctrl+Shift+R |

---

## Why the token and not a database password

The connection string needs the bms-production database password. Supabase does
not show that password anywhere — it can only be **reset**, and resetting it is a
change to bms-production that would break anything else connecting with it. So
the token is the route that touches nothing.

If a password ever does become available, the function also accepts a secret
called `ECOM_DB_URL` on Operational DB, and prefers it when both are set. It
does not expire, where a token does.

---

## What this did to bms-production

Nothing. It is only ever read from.

The function wraps every read in a read-only transaction, and Postgres refuses
writes there — tested against bms-production:

```
begin read only; create temp table ... ;
ERROR: 25006: cannot execute CREATE TABLE in a read-only transaction
```

The token being a powerful one does not matter. The transaction, not the
credential, is what stops a write.

---

## When the token expires

Figures stop loading and the message says the token was rejected. Redo steps 1
and 2. Nothing else is affected — sessions already keyed stay in the database.

---

## Optional tidy-up

In the GitHub repo, delete `publish_data.py` and the `data/` folder.
Nothing reads them any more.
