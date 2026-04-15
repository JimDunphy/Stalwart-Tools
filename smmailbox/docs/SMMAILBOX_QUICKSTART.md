# `smmailbox` — Quickstart for sysadmins

`smmailbox` helps **clone** a Zimbra mailbox into a Stalwart mailbox (and Project Z-Bridge/ZWC UI metadata) using a “copy/sync” approach.

## 0) Prereqs

- Zimbra: IMAP enabled for the mailbox(es) you’re cloning.
- Stalwart: the destination account already exists (phase 1 does not create users).
- A machine where you can run the tool (SSH admin box).
- If you want `clone` / `clone-all` to import Project Z-Bridge tag names/colors automatically, run `smmailbox` on the bridge host or on a machine with the bridge `BRIDGE_DATA_DIR` mounted/shared. That tag step is a local file write, not a bridge HTTP login/API call.

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

Important:
- `clone-all` can migrate mail, filters, contacts, and calendars from any admin box that can reach Zimbra and Stalwart.
- But its Project Z-Bridge tag import step writes directly to `BRIDGE_DATA_DIR`.
- So if you run it away from the bridge host without that directory mounted/shared, the account migration can still succeed while ZWC tag names/colors do not appear until you run `bridge-import-tags` on the bridge host later.

## 4) Verify

- In an IMAP client (or Stalwart UI): folders/messages copied.
- In ZWC (Project Z-Bridge): refresh the page and confirm tag names/colors, filters, contacts, calendars.

## Notes / gotchas

- **Stable hostnames matter:** always use the exact same `--src-host` string on re-runs (don’t switch between aliases like `mail1` vs `mail`). Some idempotency keys include this value.
- **Large mailboxes:** it’s common to run `./smmailbox imapsync ...` repeatedly (nightly) and run `clone-filters`/`clone-contacts`/`clone-calendars` once. `clone-all` is for “one command per mailbox”, but you can mix-and-match subcommands.
- **Bridge tags are local bridge state:** `clone` / `clone-all` do not send tag metadata to the bridge over HTTP. They write bridge tag files under `BRIDGE_DATA_DIR`, so that step requires bridge-host or shared-filesystem access.
- **Calendar reruns:** `clone-calendars` matches by UID across the whole destination account, preserves recurring events, and infers missing durations from parsed `end` values so re-runs update/move older series instead of duplicating or dropping them.
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
