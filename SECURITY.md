# Security and privacy

This is a development port, not a hardened consumer phone release. The current 4.5 RC2 track is a supervised RAM system, not a permanent installation. Earlier ext4/PIN results are historical. A graphical lock is not disk encryption; a final encrypted installation and first-PIN profile remain unvalidated. See [current status](docs/status.md).

R17 required hardware-button recovery through the full bootloader. R18 returned automatically with original readbacks verified, but general return reliability remains unproven. The experimental Linux account stayed locked: the R18 SIM UI ran as root only in supervised RAM, without changing modem authorization policy, local credentials or PAM. Ordinary-user integration and administrative Polkit setup remain pending. SIM access-PIN unlock and network registration do not establish phone PAM login, calls or cellular IP Internet.

PIN entry in R18 was confined to the handset; the agent did not receive/log it or capture the entry screen. GUI/modem core dumps and debug traces were disabled for entry, and later journal collection was skipped. The published SIM UI 0.1.3 candidate is MIT source tested against a synthetic ARM64 GTK/GIO modem with zero radio attempts; the phone used 0.1.2. Do not treat the candidate as phone-validated or relax general authorization policy to deploy it.

Do not report a vulnerability by publishing credentials, a PIN, password hashes, SSH keys, biometrics, modem identifiers or private logs in an issue. Describe the component and reproduction using disposable data. Use GitHub's private vulnerability reporting when it is available for this repository.

The repository contains source, sanitized validation and reviewed captures. Personal device state, firmware dumps, partition backups, local build caches and credentials must stay outside it. Package downloads require their normal upstream signatures; locally built integration packages are identified separately.

PIN authentication must remain in the trusted lock path, enforce retry limits, keep its verifier private and preserve the Unix account password. Ordinary desktop plugins must never receive authentication services or entered secrets. Automatic locking must not be enabled until setup and unlock have been tested on the device.

The APK system helper must retain its narrow descriptor-based interface and match callers to the active Waydroid session. Do not add arbitrary host paths, shell commands or general root execution to it. Android installation runs as Android shell UID/GID 2000 and returns a confirmed package-manager result; the helper exits before the client restarts Android. This boundary does not make privileged Android containers equivalent to isolated virtual machines. Report installer problems with disposable APKs and sanitized result codes, not raw application paths or private Android logs.
