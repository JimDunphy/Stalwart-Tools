# Zimbra tags + IMAP (findings)

This captures what we observed while testing tag preservation for a Zimbra → Stalwart migration.

## Folder listing / hierarchy

Zimbra exposes the folder tree via IMAP `LIST "" "*"` using `/` as the hierarchy delimiter, for example:

- `INBOX`
- `Drafts` (`\\Drafts`)
- `Sent` (`\\Sent`)
- `Trash` (`\\Trash`)
- `Junk` (`\\Junk`)
- `test1/test2` (nested folders)

This is compatible with `imapsync` folder replication.

## Sequence numbers (gotcha)

IMAP message *sequence numbers* start at **1**. `FETCH 0:*` is invalid.

Also, `FETCH 1:*` fails if the selected mailbox has `0 EXISTS`.

## Tags over IMAP

Zimbra exposes tags as IMAP keywords/flags:

- Tag *assignment* appears in per-message flags:
  - `* 3 FETCH (FLAGS (\\Seen MyTag:FLAG256 BlueTag:FLAG257))`

- The mailbox-wide `FLAGS (...)` list can also include those keywords:
  - `* FLAGS (... MyTag:FLAG256 BlueTag:FLAG257)`

These keywords have two properties:

1) They are **IMAP-safe atoms** (no spaces).
2) They include a suffix of the form `:FLAG<NNN>`.

### Spaces in tag names

SOAP shows the pretty tag names (spaces preserved):

- `<tag color="1" name="Blue Tag" id="321"/>`
- `<tag color="9" name="My Tag" id="320"/>`

But IMAP cannot represent keywords with spaces, so Zimbra normalizes the name when exposing it over IMAP:

- `Blue Tag` → `BlueTag:FLAG257`
- `My Tag` → `MyTag:FLAG256`

## SOAP vs IMAP IDs

Important: the SOAP tag `id` is **not** the same as the IMAP `FLAG###` suffix.

In our test:

- SOAP ids: `320`, `321`
- IMAP keywords: `...:FLAG256`, `...:FLAG257`

So you cannot derive the IMAP keyword from SOAP `id`.

## Migration implication

### Tag preservation (assignment)

If `imapsync` copies user-defined IMAP keywords (it should, since they’re flags), tag assignment can be preserved by simply running `imapsync`.

To verify on the destination IMAP server, fetch flags for a known copied message UID:

- `UID FETCH <uid> (FLAGS)` should include keywords like `MyTag:FLAG256`.

### Tag metadata (name + color)

IMAP keywords do not carry colors. If you want UIs to show the original:

- pretty tag names (with spaces)
- tag colors

…you need to export them via SOAP (GetTagRequest) and build a mapping:

- SOAP: `name="My Tag" color="9" id="320"`
- IMAP: keyword `MyTag:FLAG256`

One practical join strategy is:

- canonicalize SOAP name by stripping whitespace and non-alphanumerics (e.g. `My Tag` → `MyTag`)
- match that to the prefix in IMAP keywords that end in `:FLAG<NNN>`

This can be ambiguous if two tags canonicalize to the same stem; those need manual resolution.

## Pilot verification checklist

Do this on one mailbox before scaling:

1) **Zimbra SOAP returns tags + colors**
   - `GetTagRequest` returns `<tag id="…" name="…" color="…"/>`
2) **Zimbra IMAP exposes `:FLAG<NNN>` keywords**
   - Pick a message that has a tag in Zimbra and confirm `FETCH FLAGS` includes something like `MyTag:FLAG256`.
3) **imapsync copies keywords**
   - On the destination (Stalwart), check the migrated message flags contain the same keyword(s).
4) **Import tag metadata for ZWC**
   - Run `smmailbox clone`/`clone-all` (or `bridge-import-tags`) so Project Z Bridge can show the tag name + color for the existing IMAP keyword.
5) **Refresh ZWC and spot-check**
   - Refresh the web UI and verify: tag list shows pretty names/colors and tagged messages show their tags.

## Common failure modes

- **Keywords missing after imapsync**
  - Tag assignment is not being migrated. Confirm your `imapsync` options include flag syncing (this tool uses `--syncflags`).
- **SOAP tag exists but no matching IMAP keyword**
  - Often means the tag exists in Zimbra but has never been applied to a message (so it doesn’t appear in `FLAGS` yet).
  - In `tagmap.json`, those will be `missing-imap`.
- **Canonicalization collision**
  - Two SOAP tag names normalize to the same stem (example: `A-B` and `A B` → `AB`).
  - Mapping becomes ambiguous; you’ll need to resolve manually (or apply one of the tags to at least one message and re-export to see the distinct IMAP keyword).
- **Punctuation / non-IMAP-safe characters**
  - IMAP keywords cannot contain spaces and many punctuation characters, so Zimbra necessarily normalizes the name for the keyword.
  - Always prefer the observed IMAP keyword string as the canonical “tag assignment” value.
