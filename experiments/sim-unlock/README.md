# Historical SIM access-PIN UI source — 0.1.3

An MIT GTK 4 / libadwaita source experiment for **local entry of the SIM access PIN** through ModemManager. The user enters it on the handset. There is no hardcoded PIN, credential file, PIN command-line option or credential logging. This is separate from the Linux account/SDDM/PAM login.

**Current installed version is `0.2.1-1`, not the source in this directory.** It has a compact masked-button/password-buffer keypad without a Gtk.Editable/OSK surface. The controller reports a byte-identical radio core and 13 AST-identical flow methods, 18 classification tests and 17 ARM64 GTK synthetic checks. Later **human cold-boot access-PIN entry passed**, entered only on the handset: connected/home, primary PIN no longer required, secondary PIN2 enum3. A cellular-bound IPv4 HTTPS204 request passed with Wi-Fi connected/preferred. A recurrent black desktop center after login recovered by official shell restart remains an open startup issue. No new UI source is published here. See [the latest reviewed scope](../../docs/evidence/2026-11-02-cold-boot-sim-desktop.json).

**Historical version boundary:** R18 physically used **`apollo-sim-unlock 0.1.2-1`**, launched as root only in supervised RAM because the Linux account remained locked. The modem accepted the access PIN and registered, but the UI's remaining PIN2 message was confusing. The published source is **`0.1.3-1`**: it passed PC/synthetic checks, then **loaded as a native process/window in R19 with normal GPG/ALPM integrity verified**. The user closed a notice without confirming its origin or PIN2/SIM2 meaning. **Human UI-fix acceptance and a new access-PIN submission are not verified.** No later replacement-UI source is included here.

The [candidate snapshot](candidate.json) preserves its historical **R18** `phone_tested: false` status. The later [R19 phone-load record](phone-load-r19.json) describes the limited physical test separately. This prevents the source/synthetic review from being mistaken for full phone acceptance.

## The correction

ModemManager distinguishes [SIM PIN, PIN2, PUK and PUK2 lock reasons](https://www.freedesktop.org/software/ModemManager/doc/latest/ModemManager/ModemManager-Flags-and-Enumerations.html). R18 moved from access-PIN required to PIN2 while ordinary network registration succeeded. PIN2/PUK2 concern a separate SIM restriction; they must not be submitted as the ordinary access PIN.

The candidate's `refresh()` enables the access-PIN form only for `SIM_PIN` (2), subject to its error/retry guards. `NONE` (1), `SIM_PIN2` (3) and `SIM_PUK2` (5) disable that form. PUK-required or a reported zero-retry count also block sending. No PIN2/PUK was entered in R18.

## Source behavior and review

- Local masked input uses `Gtk.PasswordEntryBuffer`, disables undo and password hints, and preserves leading zeroes.
- A bounded keypad accepts 4–8 digits. Submission is manual, disabled while pending, and clears the entry before the asynchronous SendPin request.
- Closing while pending is blocked. An error prevents another submission in that window; there is no automatic retry after an error or a transient post-send read failure.
- Only modem discovery, the current SIM object, lock reason and retry count are read. Subscriber identity, operator, numbers and APN properties are not queried by this source.
- The program disables its own core dumps. R18 additionally disabled modem/GUI core dumps and debug tracing and skipped later journal collection after sensitive input. No credential screenshot is published.

[Historical candidate/source hash](candidate.json) · [ARM64 synthetic GTK/GIO report](arm64-synthetic-review.json) · [R18 result](../../docs/evidence/2026-11-01-r18.json) · [R19 load/result](../../docs/evidence/2026-11-01-r19.json) · [Source](apollo-sim-unlock.py) · [MIT license](LICENSE).

The ARM64 report used a **synthetic modem only, with zero radio PIN attempts**. It covers masked input, leading zeroes, keypad bounds, clearing, pending/error behavior and the PIN2/PUK2 distinction. The repository's offline check also exercises `refresh()` against fake lock/retry values without GTK or a bus. R19 adds physical loading, but these tests still do not establish complete phone UI acceptance.

## What R18 establishes

The phone reported ordinary **home registration**, LTE and NR5G access-technology flags, and packet-service attachment. Voice and Messaging interfaces were present. **Cellular IP Internet, throughput, calls, call audio and SMS remain unverified.** There was no confirmed external incoming-call attempt; zero call objects in bounded observations do not establish a failed call. The agent placed no call or message and received no PIN.

R18 returned automatically to Android and original boot/DTBO readbacks matched. R17's button-assisted recovery remains part of the record; general automatic-return reliability is unproven. No permanent installation, physical/logical slot mapping, ordinary-user authorization integration or phone PAM login is validated by this source release.

## R19 physical load and call result

R19 reported the modem registered with LTE/NR5G, access PIN not required and secondary lock 3 (PIN2). Two slot entries were reported: one occupied, one empty and one active SIM. The current SIM proxy did not match the slot array. These are interface observations, **not a verified physical card count or slot mapping**. In particular, PIN2 is not evidence of a second card.

GNOME Calls 51.1 was opened without a number or dial URI. The user manually called voicemail and confirmed connection plus audible downlink; the backend observed one OUTGOING call reaching ACTIVE. This is a separate telephony result, not acceptance of the SIM UI message. Microphone/uplink, incoming calls, SMS, cellular IP data, speed, AEC and VoLTE path remain unverified. The agent placed no call or message and did not read Number/Name or export numbers, subscriber/operator/APN data, object paths, audio or screenshots.

R19 returned automatically to Android with original boot/DTBO readbacks matched. General reliability and permanent installation remain unproven; R17's manual recovery is preserved. [R19 evidence](../../docs/evidence/2026-11-01-r19.json).

This directory provides source and reviewed summaries, not a signed package, installer, policy override or root launcher. PyGObject, GTK 4, libadwaita and ModemManager are external dependencies. Further phone validation must retain local-only PIN entry and normal system authorization boundaries.
