# Stalwart-Tools — Zimbra → Stalwart Migration + Operations

## Overview
This repository is a toolkit for administrators and developers transitioning from **Zimbra Collaboration Suite (FOSS Edition)** to **Stalwart Mail Server**.

It focuses on:
- Migration and operational scripts (Sieve, config parsing, folder discovery, spam tooling).
- Documentation that maps “Zimbra concepts” to Stalwart’s architecture (JMAP, Sieve, CalDAV/CardDAV, etc.).
- Mailbox cloning: `smmailbox/` (Zimbra → Stalwart mail/folders/flags/tags + filters/contacts/calendars).
- Client strategy while migrating: keep the **same Zimbra Classic Web Client (ZWC) UI** while replacing the backend with Stalwart using **Project-Z-Bridge** (Zimbra SOAP → JMAP), use a native JMAP web UI like **jmap-webmail**, and/or rely on standard MUAs (IMAP/SMTP + CalDAV/CardDAV).
- Interop testing: validate calendars/contacts/filters across multiple clients at once (Z-Bridge, jmap-webmail, and Roundcube), all Dockerized with `manage.sh`-style workflows.

## Motivation
Zimbra has long been a capable and feature-rich collaboration suite, but its open-source future is uncertain.  
In recent years, **Zimbra has stopped providing full FOSS patch releases**, and the build process for community editions has become increasingly fragile. For example, as of late 2025, third-party repositories required for building FOSS packages have broken, preventing reliable updates or security patches.  

More details are available in the Zimbra wiki:  
[Zimbra FOSS Source Code Only Releases – wiki.zimbra.com](https://wiki.zimbra.com/wiki/Zimbra_Foss_Source_Code_Only_Releases)

In contrast, **Stalwart Mail Server** represents a modern, sustainable model for open-source email infrastructure:
- Fully written in **Rust** for performance, safety, and maintainability.  
- Implements modern standards like **JMAP**, **IMAP**, **SMTP**, and **LMTP** natively.  
- Offers transparent **enterprise licensing** ($60/year) while still allowing complete self-compilation of the enterprise edition from source.  
- Modular, efficient, and actively maintained by a responsive developer community.  

After running Stalwart in parallel for several months, it has proven stable, efficient, and significantly easier to manage and extend than Zimbra’s Java-based architecture.  
This project exists to help others make the same transition smoothly — preserving existing data and workflows while moving to a modern, open ecosystem.

## Zimbra vs Stalwart (Comparison Overview)

| Feature / Aspect                | Zimbra (FOSS Edition)                     | Stalwart Mail Server                       |
|---------------------------------|-------------------------------------------|--------------------------------------------|
| **Language / Platform**         | Java (Jetty, Lucene, OpenLDAP)            | Rust (high performance, memory safe)       |
| **Web Protocols**               | SOAP, partial REST, proprietary endpoints  | Full JMAP + IMAP + SMTP + LMTP             |
| **Architecture**                | Monolithic services, multiple daemons     | Modular microservices, unified configuration |
| **Database / Storage**          | MySQL / MariaDB, file blobs               | Embedded key-value store (RocksDB) or external DB |
| **Build & Patch Model**         | FOSS releases no longer maintained        | Fully open-source with optional paid license |
| **Extensibility**               | SOAP/Java extensions                      | JSON/TOML configs, modular backend APIs     |
| **Webmail Client**              | Zimbra Web Client (legacy, Zimbra backend) | JMAP-native MUAs + Zimbra Classic UI via Project-Z-Bridge (no Zimbra backend) |
| **Security Model**              | Dependent on patches from commercial branch | Regular open-source updates, TLS-first design |
| **Ease of Deployment**          | Complex multi-package system               | Single binary or container-based deployment |
| **Community Support**           | Declining                                 | Growing, active developer community         |

## Objectives
- Document operational parallels between Zimbra and Stalwart (mail flow, LDAP, proxying, configuration layout, etc.).
- Provide migration scripts to export, convert, and import mail, accounts, and folders.
- Provide a practical client strategy during migration, including running Zimbra-like workflows against Stalwart.

## Key Components
- **Mailbox cloning (`smmailbox/`):** Clone a Zimbra account into Stalwart using:
  - `imapsync` for mail/folders/flags (preserves Zimbra IMAP keywords used for tag assignment)
  - Zimbra SOAP + Stalwart JMAP for filters/contacts/calendars
  - Project Z Bridge tag metadata import (so ZWC can show tag names/colors for migrated IMAP keywords)
- **Documentation Library:** Technical mappings between Zimbra components and Stalwart equivalents.
- **Project-Z-Bridge (related project; not yet published):** Use the **classic Zimbra web client UI** (ZWC) against a Stalwart backend by translating Zimbra SOAP → Stalwart JMAP.
  - Mental model: `ZWC (static assets) ↔ Project‑Z‑Bridge (SOAP→JMAP) ↔ Stalwart (JMAP)`
  - No Zimbra server is required (ZWC is just static content; the backend is Stalwart via JMAP).
  - This will be published once the repo is ready for public release; until then, this README only documents the architecture and migration tooling in this repo.
- **jmap-webmail (related project):** A JMAP-native webmail/collaboration UI (mail + contacts + calendar + filters) designed to run in Docker and interoperate with other clients (e.g., JMAP, CalDAV/CardDAV).
- **Roundcube (related project):** A second web UI used for interoperability testing (IMAP + calendar/contacts plugins). In practice, differences between JMAP and CalDAV/CardDAV semantics sometimes require client-side patches or workarounds.
- **Validation Tools:** Scripts and test data for verifying migration accuracy and functional parity.

## Repository Layout

- `bin/` — operational scripts (Sieve management, config extraction, folder discovery, spam tooling).
- `doc/` — documentation and design notes.
- `rspamd/` — Rspamd integration scripts and guides.
- `smmailbox/` — `smmailbox` CLI (Zimbra → Stalwart mailbox clone: mail/folders/flags/tags + filters/contacts/calendars).

## Getting Started

1. Clone this repository:
   ```bash
   git clone https://github.com/JimDunphy/Stalwart-Tools.git
   cd Stalwart-Tools
   ```
2. Review scripts in `bin/` and `rspamd/`.
3. Read docs in `doc/`.
4. For mailbox cloning (Zimbra → Stalwart), start with `smmailbox/README.md`.
5. For web UI options (separate repos):
   - **Project-Z-Bridge** (not yet published): keep the classic Zimbra UI (ZWC) while replacing the backend with Stalwart (SOAP → JMAP; no Zimbra server).
   - **jmap-webmail**: JMAP-native web UI (also in Docker).
   - **Roundcube**: IMAP webmail + calendar/contacts plugins (also in Docker; useful for CalDAV/CardDAV interoperability testing).

## Roadmap
- [x] Repository initialization and migration script stubs  
- [ ] Configuration mapping between Zimbra and Stalwart  
- [ ] Mail export to Maildir with correct flag preservation (:2,S, :2,RS, etc.)  
- [ ] JMAP-based import and account creation utilities  
- [ ] Z-Bridge integration notes + “known gaps” checklists for parity testing  
- [ ] Dockerized test environment for validation  

## Future Directions
The long-term focus of this project is on **fully open systems**, not on extending or maintaining Zimbra.  
Since reliable FOSS builds of Zimbra are no longer sustainable, all future work will center on **Stalwart** as the foundation.

While JMAP is a modern standard and well supported by Stalwart, there are still gaps in “drop-in replacement” client coverage. The current approach is:

- Prefer JMAP-first web clients for feature completeness (e.g., **Project-Z-Bridge** and **jmap-webmail**), while still supporting CalDAV/CardDAV clients for calendar/contacts interoperability.
- Use **Project-Z-Bridge** for a Zimbra-like web UI backed by Stalwart JMAP (incremental migration, parity testing, and user familiarity).
- Explore ActiveSync strategies only if/when they are necessary (see `doc/zpush-shim-jmap-design.md`).

This approach would allow:
- Native integration with default **iOS** and **Android** mail clients.  
- Continued compatibility with **ActiveSync-capable clients** like Outlook.  
- A pathway to test, validate, and transition users without depending on Zimbra’s REST or SOAP APIs.  

Long-term goals include:
- Implementing a **JMAP-to-ActiveSync translation layer** for seamless synchronization.  
- Improving client interoperability for calendars/contacts (CalDAV/CardDAV) and filters (Sieve).  
- Building a **web-based admin console** for user and domain management.  
- Expanding migration tools for shared folders, distribution lists, and aliases.  
- Conducting performance benchmarks comparing mail throughput and sync efficiency across protocols.

## Contributing
Contributions and testing feedback are welcome. Please open an issue or pull request if you’d like to participate in development, documentation, or testing.

## License
This project is licensed under the **MIT License**.
