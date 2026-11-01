# Local SIM access-PIN UI — 0.1.3 candidate

An MIT GTK 4 / libadwaita source experiment for **local entry of the SIM access PIN** through ModemManager. The user enters it on the handset. There is no hardcoded PIN, credential file, PIN command-line option or credential logging. This is separate from the Linux account/SDDM/PAM login.

**Version boundary:** R18 physically used **`apollo-sim-unlock 0.1.2-1`**, launched as root only in the supervised RAM session because the Linux account remained locked. The modem accepted the access PIN and registered, but that UI showed a confusing message when the remaining lock reason was PIN2. The source published here is the corrected **`0.1.3-1` candidate**. It passed synthetic ARM64 GTK/GIO tests and normal GPG/ALPM verification in the PC builder, with 12 checked entries / zero altered entries. **It has not been tested on the phone.** No general authorization policy or local account/PAM settings were relaxed in R18.

## The correction

ModemManager distinguishes [SIM PIN, PIN2, PUK and PUK2 lock reasons](https://www.freedesktop.org/software/ModemManager/doc/latest/ModemManager/ModemManager-Flags-and-Enumerations.html). R18 moved from access-PIN required to PIN2 while ordinary network registration succeeded. PIN2/PUK2 concern a separate SIM restriction; they must not be submitted as the ordinary access PIN.

The candidate's `refresh()` enables the access-PIN form only for `SIM_PIN` (2), subject to its error/retry guards. `NONE` (1), `SIM_PIN2` (3) and `SIM_PUK2` (5) disable that form. PUK-required or a reported zero-retry count also block sending. No PIN2/PUK was entered in R18.

## Source behavior and review

- Local masked input uses `Gtk.PasswordEntryBuffer`, disables undo and password hints, and preserves leading zeroes.
- A bounded keypad accepts 4–8 digits. Submission is manual, disabled while pending, and clears the entry before the asynchronous SendPin request.
- Closing while pending is blocked. An error prevents another submission in that window; there is no automatic retry after an error or a transient post-send read failure.
- Only modem discovery, the current SIM object, lock reason and retry count are read. Subscriber identity, operator, numbers and APN properties are not queried by this source.
- The program disables its own core dumps. R18 additionally disabled modem/GUI core dumps and debug tracing and skipped later journal collection after sensitive input. No credential screenshot is published.

[Candidate/source hash](candidate.json) · [ARM64 synthetic GTK/GIO report](arm64-synthetic-review.json) · [R18 physical result](../../docs/evidence/2026-11-01-r18.json) · [Source](apollo-sim-unlock.py) · [MIT license](LICENSE).

The ARM64 report used a **synthetic modem only, with zero radio PIN attempts**. It covers masked input, leading zeroes, keypad bounds, clearing, pending/error behavior and the PIN2/PUK2 distinction. The repository's offline check also exercises the source's `refresh()` method against fake lock/retry values without importing GTK or contacting a bus. These tests do not establish that 0.1.3 works on the phone.

## What R18 establishes

The phone reported ordinary **home registration**, LTE and NR5G access-technology flags, and packet-service attachment. Voice and Messaging interfaces were present. **Cellular IP Internet, throughput, calls, call audio and SMS remain unverified.** There was no confirmed external incoming-call attempt; zero call objects in bounded observations do not establish a failed call. The agent placed no call or message and received no PIN.

R18 returned automatically to Android and original boot/DTBO readbacks matched. R17's button-assisted recovery remains part of the record; general automatic-return reliability is unproven. No permanent installation, physical/logical slot mapping, ordinary-user authorization integration or phone PAM login is validated by this source release.

This directory provides source and reviewed summaries, not a signed package, installer, policy override or root launcher. PyGObject, GTK 4, libadwaita and ModemManager are external dependencies. Further phone validation must retain local-only PIN entry and normal system authorization boundaries.
