# Native Apollo fingerprint integration — source checkpoint

**4 November 2026 · experimental, one Mi 10T Pro.** Real capture, first enrollment,
authenticated encrypted persistence, matching the enrolled finger and rejecting
a different finger passed on the handset. Standard fprintd/PAM login and unlock
are **prepared on the PC, not installed or accepted on the handset**.
[Current results](../../docs/milestone-2026-11-04.md) · [Acceptance plan](../../docs/pruebas-pendientes.md).

## What is exported

- Apollo FPC BIO codec and enrollment/verification backend; Gatekeeper wire,
  private-store helpers, time/RPMB transport and synthetic tests.
- Native root bridge/session supervisor, the libfprint Apollo socket adapter,
  existing-print metadata adoption helper and normal fprintd D-Bus client.
- Huellas, SDDM and polkit UI sources, a PAM method selector and reversible
  service-scoped configuration. The first-run wizard is not replaced.
- Exact source hashes and pinned upstream revisions in [SOURCEPINS.json](SOURCEPINS.json).

The initial profile supports the primary local owner (UID1000), one right-index
enrollment. Multiple fingers, deletion and fingerprint-only wake from full suspend
are not exposed by this first integration. GPIO/interrupt activity is never a match.

## Authentication boundary

The selector chooses a conversation, not a biometric verdict. Typed passwords
use the original service auth stack; an explicit empty response selects the
mandatory pam_fprintd branch. Existing account/password/session rules are kept.
The root bridge accepts a match only from the native secure backend after cleanup,
for the same stored record, and with no cancellation. A user-editable status file
or a UI signal cannot grant access. sudoers and global system-auth are unchanged.

The configuration tool requires root-owned provider acceptance bound to the
installed library, selector and record metadata. It saves originals locally,
restores partial writes and refuses to overwrite later administrator edits.
Fingerprint authentication does not supply the password for encrypted keyrings.

## Validation scope

The development build passed 340 cases using real ARM64 Linux-PAM under QEMU,
32 libfprint adapter cases against a fake bridge, and 1,732 native decision-gate
cases. Eleven disposable-filesystem activation/restore cases and actual ARM64
Qt UI checks passed. These are software fixtures, not physical lock acceptance.

The exported Python tests use synthetic records and temporary directories.
`test_auth_policy.py` needs a disposable Linux environment with UID0 semantics;
it never points its policy at the real root. C tests are source-level codec/storage
fixtures. No test module or synthetic match implementation is installed on the phone.

## Build and deployment limits

This is a source snapshot for review, not a generic installer or a firmware bundle.
The daemon's surrounding upstream QSEE services, their UAPI, matching R15 kernel,
trusted storage guard, signed native package cohort and board's existing secure
firmware are prerequisites. Development-host signing keys, host control scripts,
private sysroots and boot bindings are deliberately excluded. Do not copy these
files into PAM or run the RPMB/backend code directly on an unverified device.

The selected credential store is for the native Linux authority, not a copy of
an Android credential. Images stay inside the TEE; only its authenticated encrypted
database is persisted locally with root-only permissions. No credential, token,
template, biometric image, raw device log or firmware binary is published.
The actual enrolled record must be preserved, not re-enrolled or overwritten.

Names such as rpmb-ufs-readonly retain their implementation history: the current
transport also serves the narrowly validated authenticated-write operation.
Key programming is rejected, uncertain writes are not retried, and MAC/counter
checks remain in the secure services/UFS. This is not a universal RPMB service.

## Licenses and provenance

Original Apollo files retain MIT notices under the [root license](../../LICENSE).
The libfprint adapter derives from Derek Ross / Omarchy Mobile and retains its
LGPL-2.1-or-later header and [license](../../LICENSES/LGPL-2.1-or-later.txt).
The QSEE transport retains LGPL-2.1-or-later. The ioctl UAPI header retains
GPL-2.0 WITH [Linux-syscall-note](../../LICENSES/Linux-syscall-note.txt), with
[GPLv2](../../LICENSES/GPL-2.0.txt). The Omarchy UI retains the original
David Heinemeier Hansson MIT attribution; the fprintd client retains the
[Omarchy Mobile MIT notice](../../LICENSES/MIT-Omarchy-Mobile.txt).

Protocol/transport references: [libfprint](https://gitlab.freedesktop.org/libfprint/libfprint),
[fprintd](https://gitlab.freedesktop.org/libfprint/fprintd),
[Omarchy Mobile](https://github.com/derekross/omarchy-mobile), and
[Qualcomm MinkIPC](https://github.com/qualcomm/minkipc/tree/939259cc69ee6358343a4968f732938b864799a6/listeners/librpmbservice).
