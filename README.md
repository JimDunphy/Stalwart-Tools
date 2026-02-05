# Stalwart-Tools — Zimbra → Stalwart Migration + Operations

## Overview
This repository is a toolkit for administrators and developers transitioning from **Zimbra Collaboration Suite (FOSS Edition)** to **Stalwart Mail Server**.

It focuses on:
- Migration and operational scripts (Sieve, config parsing, folder discovery, spam tooling).
- Documentation that maps “Zimbra concepts” to Stalwart’s architecture (JMAP, Sieve, CalDAV/CardDAV, etc.).
- Mailbox cloning: `smmailbox/` (Zimbra → Stalwart mail/folders/flags/tags + filters/contacts/calendars).
- Client strategy while migrating: keep the **same Zimbra Classic Web Client (ZWC) UI** while replacing the backend with Stalwart using **Project-Z-Bridge** (Zimbra SOAP → JMAP), and/or rely on standard MUAs (IMAP/SMTP + CalDAV/CardDAV).

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

We have been running Stalwart in parallel with our commercial Zimbra deployment since August 2025, and testing Project Z-Bridge since December 2025. We have not switched — both systems run side-by-side to verify behavioral parity.

This project started as a contingency plan. As commercial Zimbra customers, our fallback if Zimbra ceased operations would be the FOSS edition — but when Zimbra stopped providing timely security patches for FOSS, we began exploring alternatives. Stalwart is pre-1.0 but has proven more stable and maintainable than Zimbra's Java-based architecture for our use case.

Some of our users already prefer Project Z-Bridge for features not present in stock Zimbra, running the Docker container on their desktops alongside our production Zimbra environment. This project exists to help others evaluate a similar migration or mitigation strategy.

## Zimbra vs Stalwart (Comparison Overview)

| Feature / Aspect                | Zimbra (FOSS Edition)                     | Stalwart Mail Server                       |
|---------------------------------|-------------------------------------------|--------------------------------------------|
| **Language / Platform**         | Java (Jetty, Lucene, OpenLDAP)            | Rust (high performance, memory safe)       |
| **Web Protocols**               | SOAP, partial REST, proprietary endpoints  | Full JMAP + IMAP + SMTP + LMTP             |
| **Architecture**                | Monolithic services, multiple daemons     | Modular microservices, unified configuration |
| **Database / Storage**          | MySQL / MariaDB, file blobs               | Embedded key-value store (RocksDB) or external DB |
| **Build & Patch Model**         | FOSS releases no longer maintained        | Fully open-source with optional paid license |
| **Extensibility**               | SOAP/Java extensions                      | JSON/TOML configs, modular backend APIs     |
| **Webmail / Mobile Client**     | Zimbra Web Client (legacy, Zimbra backend) | Project-Z-Bridge (ZWC UI) + zpush-jmap (ActiveSync) + standard MUAs |
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
- **Project-Z-Bridge:** A middleware layer written in Rust that serves the **classic Zimbra web client UI** (ZWC) against a Stalwart backend by translating Zimbra SOAP → Stalwart JMAP.
  - Mental model: `ZWC (static assets) ↔ Project‑Z‑Bridge (SOAP→JMAP) ↔ Stalwart (JMAP)`
  - No Zimbra server is required (ZWC is just static content; the backend is Stalwart via JMAP).
  - Status: ~95% feature complete (mail, calendar, contacts, sharing, filters, tags). Targeting public release Q1 2026.
- **zpush-jmap (related project):** ActiveSync support for Stalwart using Z-Push with a JMAP backend (PHP + Rust via ext-php-rs). Enables native iOS, Android, and Outlook synchronization.
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
5. For client options (separate repos):
   - **Project-Z-Bridge**: keep the classic Zimbra UI (ZWC) while replacing the backend with Stalwart (SOAP → JMAP; no Zimbra server).
   - **zpush-jmap**: ActiveSync support for native iOS/Android/Outlook sync via Z-Push + Stalwart JMAP.

## Roadmap
- [x] Mailbox cloning via `smmailbox` (mail/folders/flags/tags + filters/contacts/calendars)
- [x] Project Z-Bridge: ZWC UI on Stalwart JMAP (~95% feature complete)
- [x] zpush-jmap: ActiveSync support via Z-Push + Stalwart JMAP
- [ ] Expanded migration tooling (shared folders, distribution lists, aliases)  

## Future Directions
The long-term focus of this project is on **fully open systems**, not on extending or maintaining Zimbra.  
Since reliable FOSS builds of Zimbra are no longer sustainable, all future work will center on **Stalwart** as the foundation.

While JMAP is a modern standard and well supported by Stalwart, there are still gaps in “drop-in replacement” client coverage. The current approach is:

- Use **Project-Z-Bridge** as the primary web client (familiar ZWC interface backed by Stalwart JMAP) for incremental migration and user familiarity, while supporting CalDAV/CardDAV clients for calendar/contacts interoperability.
- Use **zpush-jmap** for ActiveSync support (iOS/Android/Outlook native clients) via Z-Push with a Stalwart JMAP backend.

This approach allows:
- Native integration with default **iOS** and **Android** mail clients (via ActiveSync or CalDAV/CardDAV).
- Continued compatibility with **ActiveSync-capable clients** like Outlook.
- A complete migration path without depending on Zimbra's REST or SOAP APIs.

Long-term goals include:
- Improving client interoperability for calendars/contacts (CalDAV/CardDAV) and filters (Sieve).
- Expanding migration tools for shared folders, distribution lists, and aliases.

## Contributing
Contributions and testing feedback are welcome. Please open an issue or pull request if you’d like to participate in development, documentation, or testing.

## License
This project is licensed under the **MIT License**.
