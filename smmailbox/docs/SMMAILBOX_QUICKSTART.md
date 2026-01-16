# `smmailbox` — Quickstart for sysadmins

`smmailbox` helps **clone** a Zimbra mailbox into a Stalwart mailbox (and Project Z-Bridge/ZWC UI metadata) using a “copy/sync” approach.

## 0) Prereqs

- Zimbra: IMAP enabled for the mailbox(es) you’re cloning.
- Stalwart: the destination account already exists (phase 1 does not create users).
- A machine where you can run the tool (SSH admin box).

## 1) Install dependencies

Install `imapsync` (best-effort):

```bash
./smmailbox --init
```

## 2) Dry-run (recommended)

```bash
export ZIMBRA_PASS='...'
export STALWART_PASS='...'

./smmailbox --dry-run clone-all \
  --src-host mail.example.com \
  --src-user user@example.com \
  --src-password-env ZIMBRA_PASS \
  --dst-host stalwart.example.com \
  --dst-user user@example.com \
  --dst-password-env STALWART_PASS
```

## 3) Do everything (per account)

This runs:
1) export Zimbra tags → IMAP keyword mapping (`tagmap.csv/json`)
2) `imapsync` mail/folders/flags
3) import tag **names + colors** into Project Z-Bridge (so ZWC shows pretty tags)
4) clone incoming filters (as inactive / “Available Filters” by default)
5) clone contacts/address books
6) clone calendars/events (last `365` days by default)

```bash
./smmailbox clone-all \
  --src-host mail.example.com \
  --src-user user@example.com \
  --src-password-env ZIMBRA_PASS \
  --dst-host stalwart.example.com \
  --dst-user user@example.com \
  --dst-password-env STALWART_PASS
```

## 4) Verify

- In an IMAP client (or Stalwart UI): folders/messages copied.
- In ZWC (Project Z-Bridge): refresh the page and confirm tag names/colors, filters, contacts, calendars.

## Notes / gotchas

- **Stable hostnames matter:** always use the exact same `--src-host` string on re-runs (don’t switch between aliases like `mail1` vs `mail`). Some idempotency keys include this value.
- **Large mailboxes:** it’s common to run `./smmailbox imapsync ...` repeatedly (nightly) and run `clone-filters`/`clone-contacts`/`clone-calendars` once. `clone-all` is for “one command per mailbox”, but you can mix-and-match subcommands.
- **Output:** by default `smmailbox` filters the very-verbose `imapsync` output to folder-level progress + summary; use `--verbose` to pass through full output.
- **Imapsync cache (optional):** on repeated runs you can speed up `imapsync` by enabling cache:
  - `--imapsync-arg --usecache`
  - Cache lives under `--tmpdir` (default system tmp) at `imapsync_cache/`, so set a stable tmp dir if needed:
    - `--imapsync-arg --tmpdir --imapsync-arg /var/tmp`
- **Artifacts:** `clone`/`clone-all` write `tagmap.csv` + `tagmap.json` in the current directory for debugging/record. Add `--clean` to remove them after a successful run.
- **Passwords:** this tool currently assumes you can authenticate as the user (SOAP + IMAP). That’s often not realistic at scale.
  - Short-term options: collect user passwords, do a temporary password reset during migration, or use a Zimbra admin/delegated-auth approach.
  - `smmailbox` does not implement admin delegation yet; if your environment supports it, you can sometimes pass extra `imapsync` options via `--imapsync-arg ...` and avoid knowing the user password.

## Attribution / License

- Maintainer: J Dunphy
- AI assistance: OpenAI Codex (GPT-5.2)
- License: MIT
