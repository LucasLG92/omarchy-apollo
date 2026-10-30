# Clean Omarchy installation

The clean installation is **permanently installed and cold-boot accepted**. The owner shut down completely, disconnected the PC, powered on the Xiaomi and unlocked the native Omarchy desktop with the local numeric PIN. Maintenance USB reconnected afterward. The [permanent-boot evidence](evidence/clean-permanent-boot-2026-10-30.json) distinguishes this from the earlier temporary trial.

The root was built from a newly extracted, signature-verified official Arch Linux ARM bootstrap and signed repository packages, with pinned native Omarchy and reviewed Apollo components. No previous system, home, passwords, saved Wi-Fi profiles or Android userdata was imported. KDE/Plasma and CachyOS packages are absent.

## Installation and recovery

The image occupies its own persistent slot on internal ext4 storage. Its SquashFS base has SHA-256 `5c1ce3351484abf8be168b69e72096a8b7eec3863be9d5324f1e06ecf785a781`; later changes live in that slot's overlay. The initializer verifies the image checksum and hands over to systemd. USB maintenance starts after that handoff.

The installed boot image was read back and matched SHA-256 `5cef1894ac6fefdd3b42f36b21c5cf38e43e39fadbfedb32f415610a75733e65`. This step replaced only the boot partition. It did not format, repartition, replace recovery or flash firmware. The complete prior boot partition and previous slot remain private recovery assets.

The running kernel remains `linux-apollo 7.1.0-23`. Acceptance of this base permits isolated kernel experiments; it does not establish compatibility with a generic newer kernel.

## Numeric authentication and power key

The owner creates a 6–12 digit PIN on the phone. No mandatory long-password step is shown. The enrolled PIN and verifier are never exported. Unlocking with the redesigned keypad has been physically confirmed, including after unplugged cold boot.

The owner selected the same PIN for administration. Sudo/polkit preserve account/session policies and authenticate through the PIN verifier. Revision 4 fixes real-root PAM account resolution. Thirteen isolated cases cover both caller contexts and actual harmless sudo commands. The owner separately reported successful touch-popup acceptance; that report is distinct from a captured completed-command receipt. See [authentication evidence](evidence/pin-administration-2026-10-30.json).

The short power key locks before blanking, suppresses the keypad flash and presents the PIN on wake. The owner confirmed this cycle. Nineteen helper fixtures also cover startup races, failed locking, touch cancellation, idle behavior and enrollment guards. See [power-key evidence](evidence/phone-power-key-2026-10-30.json).

## Desktop and Android

Hyprland/Quickshell uses the 1080 × 2400 panel at scale 2.5. Live configuration diagnostics are clean and native OpenGL ES reports FD650. A dedicated bar button opens the actual responsive app grid. Keyboard and orientation controls have their own tests and remaining physical acceptance items.

Fresh VANILLA Android system/vendor images use new data in this slot. Thirty-one isolated APK/lifecycle checks confirm F-Droid installation, persistence and FD650 before/after container restart. After host cold boot, Android was separately observed in a native window with FD650. An already open application was preserved. Physical stopped-state icon launch, input, notifications and Android hardware access remain separate tests.

New Android installs offer VANILLA or GAPPS, defaulting to VANILLA. The 27-case initializer fixture covers choice and permissions; actual GAPPS/Google Play acceptance remains pending. Read the [Android guide](android.md).

## Subsequent updates and limits

Runtime revision 12 updates the pinned upstream source without changing the accepted lock service, power helper or kernel. The three affected upstream test suites and installed package checks pass; open windows are preserved. The graphics resource-wait correction is active in the compositor.

Device revision 6 adds calibrated read-only clock restoration. Its service succeeded in the current boot; counter continuity after the next complete power-off is pending. This later update must not be confused with the earlier accepted cold boot. See [clock behavior](clock.md).

This is a development installation for this device, not an accepted public installer from stock Android. Firmware inputs, operator/host keys, personalized images, backups and private diagnostics stay outside the repository. Camera, audio, cellular, GPS, fingerprint and external-display support retain the limits in the main status table.
