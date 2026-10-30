# Security and privacy

This is a development port with authorized maintenance access. It is not a hardened consumer phone release. A graphical lock is not disk encryption, and the inherited ext4 development installation is not encrypted.

Do not report a vulnerability by publishing credentials, a PIN, password hashes, SSH keys, biometrics, modem identifiers or private logs in an issue. Describe the component and reproduction using disposable data. Use GitHub's private vulnerability reporting when it is available for this repository.

The repository contains source, sanitized validation and reviewed captures. Personal device state, firmware dumps, partition backups, local build caches and credentials must stay outside it. Package downloads require their normal upstream signatures; locally built integration packages are identified separately.

PIN authentication must remain in the trusted lock path, enforce retry limits, keep its verifier private and preserve the Unix account password. Ordinary desktop plugins must never receive authentication services or entered secrets. Automatic locking must not be enabled until setup and unlock have been tested on the device.

The APK system helper must retain its narrow descriptor-based interface and match callers to the active Waydroid session. Do not add arbitrary host paths, shell commands or general root execution to it. Android installation runs as Android shell UID/GID 2000 and returns a confirmed package-manager result; the helper exits before the client restarts Android. This boundary does not make privileged Android containers equivalent to isolated virtual machines. Report installer problems with disposable APKs and sanitized result codes, not raw application paths or private Android logs.
