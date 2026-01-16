# `smmailbox` (phase 1)

`smmailbox` is a **local CLI** intended to help migrate accounts from a **Zimbra server** to a **Stalwart server**.

This is **not** a network API. Run it on an admin box (SSH) so you don’t create a new remote attack surface.

If you just want the short “sysadmin quickstart”, start with: `docs/SMMAILBOX_QUICKSTART.md`.

## Phase 1 scope

- Mail migration via **IMAP** using `imapsync` (fast path for large mailboxes).
- Preserve Zimbra tag *assignment* by copying IMAP keywords/flags (`MyTag:FLAG###` style).
- Export Zimbra tag metadata (SOAP) and map it to the IMAP keyword names so UIs can restore:
  - Pretty tag names (with spaces)
  - Tag colors (Zimbra color id)

Not in scope (yet):
- Account provisioning on Stalwart (create users). Provision accounts first using your existing method.
- Outgoing filters (separate future step).

## Network protocol usage (by subcommand)

- `export-tag-map`: Zimbra **SOAP** + source **IMAP** (reads `FLAGS`)
- `imapsync`: source **IMAP** → destination **IMAP** (via `imapsync`)
- `bridge-import-tags`: no network; writes to Project Z-Bridge `BRIDGE_DATA_DIR`
- `clone`: Zimbra **SOAP** + source **IMAP** (imapsync) + destination **JMAP** (bridge tag import)
- `clone-all`: `clone` + `clone-filters` + `clone-contacts` + `clone-calendars`
- `clone-filters`: Zimbra **SOAP** + destination **JMAP** (SieveScript)
- `clone-contacts`: Zimbra **SOAP** + destination **JMAP** (contacts/address books)
- `clone-calendars`: Zimbra **SOAP** (discover calendars) + Zimbra **REST** `/home/...?...fmt=ics` export + destination **JMAP** (calendars/events)
- `init`: local OS installs (may use network to fetch packages or clone `imapsync`)

## Quickstart (do everything)

Clone mail/folders/flags (imapsync) **and** import tag colors/names into Project Z-Bridge **and** clone filters/contacts/calendars:

```bash
./smmailbox clone-all \
  --src-host mail.example.com \
  --src-user user@example.com \
  --src-password-env ZIMBRA_PASS \
  --dst-host stalwart.example.com \
  --dst-user user@example.com \
  --dst-password-env STALWART_PASS
```

Notes:
- This is safe to re-run (it is a “clone/sync”, not a destructive move), but see the idempotency notes per subcommand below.
- For very large mailboxes, many admins will run `imapsync` repeatedly (nightly) and only run filters/contacts/calendars once. You can always run the subcommands individually.

## Quickstart (phase 1: mail + tags + bridge tag import)

Clone mail + folders + flags/tags from Zimbra IMAP to Stalwart IMAP, and import tag metadata into Project Z-Bridge so ZWC shows the correct **tag names + colors**:

```bash
./smmailbox clone \
  --src-host mail.example.com \
  --src-user user@example.com \
  --src-password-env ZIMBRA_PASS \
  --dst-host stalwart.example.com \
  --dst-user user@example.com \
  --dst-password-env STALWART_PASS
```

Notes:
- `--zimbra-host/--zimbra-user/--zimbra-password-*` are legacy aliases for `--src-host/--src-user/--src-password-*`.
- `clone` writes `tagmap.csv` and `tagmap.json` (by default in the current directory) for debugging/record.
  - If you don’t want these artifacts, add `--clean` to remove them after a successful run.
- `clone` fetches the Stalwart JMAP session (`/.well-known/jmap`) to auto-detect the correct `apiUrl` host + primary mail `accountId` for the bridge tag store. If that lookup fails, you can pass `--bridge-host` / `--bridge-account-id`.
- Refresh ZWC after running `clone` so the UI reloads the updated tag metadata.

## Install / init

Best-effort dependency install (currently just `imapsync`):

```bash
./smmailbox --init
```

Notes:
- On Ubuntu, `imapsync` is usually in the `universe` component. If `apt-get install imapsync` fails, enable `universe` and retry:
  - `sudo apt-get install -y software-properties-common`
  - `sudo add-apt-repository -y universe`
  - `sudo apt-get update && sudo apt-get install -y imapsync`
- If `imapsync` still isn’t available as a package, `smmailbox --init` falls back to a source install (clones https://github.com/imapsync/imapsync and installs Perl deps).
  - Env: set `IMAPSYNC_DIR` to control the clone path (default: `~/imapsync`).
  - Env: set `IMAPSYNC_TESTSLIVE=1` to run `imapsync --testslive` after install (default: off).

Dry-run:

```bash
./smmailbox --dry-run --init
```

## Developer: publish a sanitized subset

This repo is a dev workspace. If you want to publish a small sanitized subset (no internal hostnames/users), use the repo-level publishing tool (config-driven) rather than adding publish logic to `smmailbox` itself.

## Attribution / License

- Maintainer: J Dunphy
- AI assistance: OpenAI Codex (GPT-5.2)
- License: MIT

## Export Zimbra tags + IMAP keyword mapping

Writes `tagmap.csv` and `tagmap.json` by:
- fetching tags from Zimbra SOAP (`GetTagRequest`)
- reading IMAP `FLAGS` keywords from a mailbox (`SELECT INBOX`)
- mapping SOAP tag names to IMAP keywords by canonicalizing the name (strip spaces/punctuation)

```bash
./smmailbox export-tag-map \
  --src-host mail.example.com \
  --src-user user@example.com \
  --src-password-env ZIMBRA_PASS \
  --out-csv tagmap.csv
```

If your SOAP/IMAP cert isn’t trusted:

```bash
./smmailbox export-tag-map ... --insecure
```

Notes:
- IMAP keywords are the *only* part imapsync can preserve automatically.
- The SOAP tag `id` is **not** the same as the IMAP `FLAG###` suffix.

## Mail migration (imapsync wrapper)

Run `imapsync` using passfiles (avoids passwords in process args).

```bash
./smmailbox imapsync \
  --src-host mail.example.com \
  --src-user user@example.com \
  --src-password-env ZIMBRA_PASS \
  --dst-host stalwart.example.com \
  --dst-user user@example.com \
  --dst-password-env STALWART_PASS
```

Notes:
- `imapsync` output is very verbose; by default `smmailbox` filters it to folder-level progress + summary.
  - Use `--verbose` to pass through full output.
- For repeated incremental runs, you can enable `imapsync` caching (speeds up subsequent syncs):
  - `--imapsync-arg --usecache`
  - Cache files live under `--tmpdir` (default system tmp) at `imapsync_cache/` (so use a stable `--tmpdir`, e.g. `/var/tmp`, if you want the cache to persist across reboots):
    - `--imapsync-arg --tmpdir --imapsync-arg /var/tmp`

Add raw `imapsync` flags (repeatable):

```bash
./smmailbox imapsync ... \
  --imapsync-arg --automap \
  --imapsync-arg --delete2
```

Dry-run:

```bash
./smmailbox --dry-run imapsync ...
```

### What to expect on the destination

- New folder hierarchy appearing as the run progresses.
- Messages copied into those folders.
- Zimbra tags arriving as IMAP keywords like `MyTag:FLAG256` (visible via IMAP `FETCH FLAGS`).
- No deletions by default (we do not pass `--delete2`), so it’s “copy/sync”, not “move”.

Note: Stalwart (server) stores these as IMAP keywords; it does not provide “colored tags” metadata. Project Z-Bridge’s ZWC tags are shim-managed, so migrated IMAP keywords will not show up as ZWC tags until you import the mapping via `bridge-import-tags` (below).

## Import tags into Project Z-Bridge (ZWC)

After:
1) `imapsync` has copied IMAP keywords (tags) to Stalwart, and
2) you have generated `tagmap.json` from Zimbra via `export-tag-map`,

…import the mapping into Project Z-Bridge’s tag store so ZWC can display the **tag names + colors** for those existing IMAP keywords:

```bash
./smmailbox bridge-import-tags \
  --tagmap-json ./bin/tagmap.json \
  --bridge-host stalwart.example.com \
  --bridge-username user@example.com
```

Notes:
- `--bridge-account-id` is optional. If omitted, `smmailbox` will try to find an existing bridge tag store file for that user; otherwise it defaults to `c` (common Stalwart mail account id). You can still pass it explicitly or look it up via `./manage.sh probe`.
- This writes to `BRIDGE_DATA_DIR/tags/<session-key>.json`. Refresh the ZWC page to see the updated tags.

## Clone incoming filters (Zimbra → Stalwart)

Imports **incoming** Zimbra filters into Stalwart’s `zbridge-incoming-model` SieveScript so they appear in:

`Preferences → Filters`

Default behavior is safe:
- Imported rules are set to **inactive**, so they land under **Available Filters** (not Active Filters).
- Nothing is activated server-side by `smmailbox`.

Basic usage:

```bash
./smmailbox clone-filters \
  --src-host mail.example.com \
  --src-user user@example.com \
  --src-password-env ZIMBRA_PASS \
  --dst-host stalwart.example.com \
  --dst-user user@example.com \
  --dst-password-env STALWART_PASS
```

Options:
- `--preserve-active`: keep Zimbra’s active/disabled state (default: import everything inactive)
- `--script-name`: override destination script name (default: `zbridge-incoming-model`)

### Conflict/duplicate policy (idempotent)

Re-running `clone-filters` should not create a large pile of duplicates. The merge rules are:

- If the destination has an **inactive** rule with the same name, it is **overwritten in place**.
- This means: if you manually edit an imported rule while it’s still under **Available Filters**, then re-run `clone-filters`, your edits will be replaced by whatever is currently on the Zimbra source (by design — `clone-filters` treats Zimbra as the source of truth for rule bodies).
- If the destination has an **active** rule with the same name, the imported rule is written to `Name(1)` (inactive by default).
  - If `Name(1)` exists and is inactive, it is overwritten.
  - If both `Name` and `Name(1)` are active, `clone-filters` aborts (use `--force` if you really want to override).

Dangerous override:
- `--force` allows overwriting active/conflicting rules and also overwriting a destination script that is not marked `# Managed-by: zbridge`.

## Clone contacts (Zimbra → Stalwart)

Clones **contact folders** (address books) and **contacts** into Stalwart via JMAP:

```bash
./smmailbox clone-contacts \
  --src-host mail.example.com \
  --src-user user@example.com \
  --src-password-env ZIMBRA_PASS \
  --dst-host stalwart.example.com \
  --dst-user user@example.com \
  --dst-password-env STALWART_PASS
```

What it does:
- Discovers Zimbra contact folders via SOAP `GetFolderRequest view="contact"`.
- Maps Zimbra folder id `7` (“Contacts”) into Stalwart’s **default** address book.
- Creates additional Stalwart address books (by name) for other Zimbra contact folders.
- Upserts contacts via JMAP `ContactCard/set`.

### Idempotency / overwrite behavior

`clone-contacts` is safe to re-run:
- Each imported contact is assigned a **stable** `uid` derived from `(zimbra_host, zimbra_user, zimbra_contact_id)`.
- If a destination contact already has that `uid`, it is **updated in place**.
- Contacts on the destination that **don’t** have a matching `uid` are left untouched (no deletions).

IMPORTANT: `--src-host` is part of the stable identity for imported contacts. Use the **same hostname** on every run (don’t switch between aliases like `mail.example.com` vs `mail1.example.com`) or contacts will be treated as coming from a different source and you’ll get duplicates.

Debugging options:
- `--limit-contacts N`: limit total contacts processed
- `--zimbra-search-page-size N`: SOAP `SearchRequest` paging (default: 200)
- `--jmap-query-page-size N`: destination indexing paging (default: 500)
- `--jmap-batch-size N`: `ContactCard/set` batch size (default: 100)

## Clone calendars (Zimbra → Stalwart)

Clones calendars (folder list) and calendar events:

```bash
./smmailbox clone-calendars \
  --src-host mail.example.com \
  --src-user user@example.com \
  --src-password-env ZIMBRA_PASS \
  --dst-host stalwart.example.com \
  --dst-user user@example.com \
  --dst-password-env STALWART_PASS
```

What it does:
- Discovers Zimbra calendar folders via SOAP `GetFolderRequest view="appointment"`.
- Maps Zimbra folder id `10` (“Calendar”) into Stalwart’s **default** calendar (selected by `isDefault`, otherwise the first calendar with a non-empty `timeZone`, otherwise the first calendar returned by JMAP).
- Exports each calendar as ICS via `https://<zimbra-host>/home/<user>/<CalendarPath>?fmt=ics` (cookie auth).
- Imports via JMAP `CalendarEvent/parse` + `CalendarEvent/set` (with `sendSchedulingMessages=false` to avoid emailing attendees).
- **Does not migrate alarms/notifications** (alerts are intentionally dropped for now).

### Idempotency / overwrite behavior

`clone-calendars` is safe to re-run:
- Events are matched by iCal `uid` when available.
- If an event `uid` is missing, a stable uuid5 is generated from `(zimbra_host, zimbra_user, calendarPath, start, title)`.
- If a destination event already has that `uid`, it is **updated in place**; otherwise it is created. If the existing event lives in a different destination calendar, it is updated and moved into the target calendar to avoid duplicates.
- No deletions are performed.

IMPORTANT: `--src-host` is part of the stable identity for imported calendar events. Use the **same hostname** on every run (don’t switch between aliases) or events may be treated as coming from a different source and you’ll get duplicates.

Debugging options:
- `--since-days N`: import events with start >= now-N days (default: 365)
- `--dedupe-equal-events`: skip exact duplicate VEVENTs (same content but different UID) within an ICS export
- `--jmap-query-page-size N`: destination event indexing page size (default: 500)
- `--jmap-batch-size N`: `CalendarEvent/set` batch size (default: 50)
- `--limit-events N`: limit total events processed (debug)

## Roadmap (not implemented yet)

- `clone` outgoing filters (not implemented yet).

## Security notes

- Prefer `--*-password-env`, `--*-password-file`, or `--prompt-password` over passing passwords on the command line.
- `imapsync` is run via temporary `--passfile1/--passfile2` files with mode `0600`.
- `--insecure` disables TLS verification (use only for lab/testing).

## Tests (local, no network)

The unit tests in `bin/test_smmailbox_*.py` validate **pure helper logic** (no SOAP/IMAP/JMAP calls):

- `bin/test_smmailbox_filters.py`: filter merge/duplicate policy (`merge_imported_filter_rules`)
- `bin/test_smmailbox_contacts.py`: contact mapping helpers (email/phone/name/date)
- `bin/test_smmailbox_calendars.py`: calendar naming + datetime parsing + dedupe keys

Run:

```bash
python3 -m unittest -v \
  bin/test_smmailbox_filters.py \
  bin/test_smmailbox_contacts.py \
  bin/test_smmailbox_calendars.py
```
