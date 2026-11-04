# Security and privacy

**Current scope · 4 November 2026:** Linux 7.3.1 R15 is the installed native
kernel. Existing-owner local login and authenticated administration/password
change have device evidence; clean-first-user installation, disk-encryption
unlock and broad security acceptance remain incomplete. A graphical lock is
not disk encryption. [Current state](docs/status.md).

The new [gallery](docs/gallery.md) contains manually reviewed real-device
captures. App captures used disposable data and a dummy voice provider, with
no call placed. No credentials, biometrics, account names, network names,
subscriber identifiers, personal notifications/conversations or private photos
are included. Screenshots do not certify fingerprint or call functionality.

Boot images, storage bindings, authentication material, proprietary firmware,
partition backups and per-unit calibration stay private. Public evidence is
an explicit field selection, not an upload of device logs or controller state.

## Fingerprint security boundary

Real enrollment, authenticated encrypted persistence/reload, a matching finger
and a different-finger rejection passed. The standard libfprint/fprintd/PAM
cohort is prepared on the PC, **not active on the handset**. Its method selector
only selects a mandatory authentication branch; neither GPIO events, UI JSON
nor an ordinary plugin can grant access. Account rules and password fallback
remain in the trusted PAM path. Whole-disk/keyring decryption is separate.

Capture images stay in the trusted application. Its authenticated encrypted
database and Gatekeeper credential stay root-only on the phone; no such bytes
are published. Verification uses a fresh challenge and a secure-world result.
The host checks result structure/freshness; it does not claim independent HAT
MAC verification outside the TEE. The UFS transport rejects key programming and
uncertain-write retries. This is not a universal secure-storage implementation.

The initial profile supports one owner and one finger. Provider acceptance,
actual initial login/lock/admin, cancellation, suspend and energy tests must
precede broader functionality claims. See the [current source boundary](experiments/native-fingerprint/README.md).

## Historical security observations

The following dated trial/provisioning observations retain their original
scope. Pending states in those checkpoints are not current acceptance claims.

This is a development port, not a hardened consumer phone release. R20 completed native installation on the development unit: flashed native boot and the internal ext4 root passed repeated normal boot, including after Android cleanup. The owner entered the local credential and reached the desktop after normal boot; autologin is empty and the original theme is selected. Android userdata was repurposed for the root; super/metadata/cache were cleared. A graphical lock is not disk encryption. Polkit authentication, encrypted-storage unlock, broad hardware acceptance and a public end-to-end installer remain unvalidated. See [current status](docs/status.md).

R17 required hardware-button recovery through the full bootloader. R18/R19 returned automatically with original readbacks verified, but general return reliability remains unproven. The experimental Linux account stayed locked in R18: its SIM UI ran as root only in supervised RAM, without changing modem authorization policy, local credentials or PAM. That locked-account state describes R18. R20 later configured a local credential and verified actual login, including after normal boot; administrative Polkit authentication remains pending. R19's manual outgoing call/downlink result does not establish microphone/uplink, incoming calls, SMS, cellular IP Internet or phone PAM login.

PIN entry in R18 was confined to the handset; the agent did not receive/log it or capture the entry screen. GUI/modem core dumps and debug traces were disabled for entry, and later journal collection was skipped. R18 used SIM UI 0.1.2; 0.1.3 passed synthetic ARM64 GTK/GIO checks and its native process/window loaded in R19. Human acceptance of the PIN2 message and a new access-PIN submission remain unconfirmed. Do not treat physical loading as complete UI acceptance or relax general authorization policy to deploy it. R19 call observation read state/direction/reason and listed objects, without Number/Name reads, subscriber/network identity exports, screenshots or audio files.

Installed SIM UI 0.2.1-1 later accepted the human access PIN entered only on the phone after cold boot. The modem reached connected/home, primary access PIN was no longer required and secondary PIN2 remained; no PIN/subscriber/network identity or credential capture is exported. Earlier synthetic checks and public 0.1.3 source retain their historical scope. This successful authentication does not resolve the recurrent black desktop center after login: shell .8/official Quickshell restart recovered Home, but a definitive startup fix remains unverified. No new private UI/shell source or recovery capture is published.

Do not report a vulnerability by publishing credentials, a PIN, password hashes, SSH keys, biometrics, modem identifiers or private logs in an issue. Describe the component and reproduction using disposable data. Use GitHub's private vulnerability reporting when it is available for this repository.

The repository contains source, sanitized validation and reviewed captures. Personal device state, firmware dumps, partition backups, local build caches and credentials must stay outside it. Package downloads require their normal upstream signatures; locally built integration packages are identified separately.

The [R20 owner form](experiments/owner-setup/README.md) sets the normal local account credential through `chpasswd`, without sending the value as a command argument or saving plaintext. Success also writes SDDM theme/autologin configuration and a readiness marker; those writes alone do not prove authentication; a separate R20 human login test later passed. Only marker/account-status booleans were inspected, without reading the credential or account hash. The public synthetic harness overrides the real credential sink and performs no PAM/shadow or radio operation. The real setup source is privileged provisioning code, not a general desktop plugin or install command.

Authentication must remain in the trusted account/lock path, enforce the relevant backend retry policy and keep verifiers private. Ordinary desktop plugins must never receive authentication services or entered secrets. Automatic locking must not be enabled until setup and unlock have been tested on the device.

The APK system helper must retain its narrow descriptor-based interface and match callers to the active Waydroid session. Do not add arbitrary host paths, shell commands or general root execution to it. Android installation runs as Android shell UID/GID 2000 and returns a confirmed package-manager result; the helper exits before the client restarts Android. This boundary does not make privileged Android containers equivalent to isolated virtual machines. Report installer problems with disposable APKs and sanitized result codes, not raw application paths or private Android logs.
