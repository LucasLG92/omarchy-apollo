# Build status and recipes

These are integration packages for an already provisioned Apollo Linux base. This repository does not yet provide a validated installer from stock Android. Do not use a generic Omarchy ISO or format phone partitions with PC installation instructions.

Build as an ordinary user in a clean checkout on aarch64 with the matching, signature-verified Omarchy ARM edge and Arch Linux ARM repositories. The runtime recipe is the root `PKGBUILD`. It fetches a pinned upstream git commit and applies `patches/`. The original Apollo kernel, camera and firmware packages remain separate and must be preserved.

The recipes in `packaging/` build additional components. Put each recipe at the root of a separate clean staging copy of this repository as `PKGBUILD`, then use `makepkg` there. The keyboard recipe pins upstream wvkbd v0.20; the mobile recipe installs interface templates and its keyboard service; the Android recipe installs the ext4 bind-mount dependency, on-demand launcher, confirmed APK installer, D-Bus policy and APK file handler. The Android recipe explicitly depends on `xdg-utils` for selecting that handler.

The lock recipe builds the local enrollment application and the narrowly scoped setuid verifier. Installing its package does not enroll an owner PIN or turn on automatic locking. PIN entry and confirmation happen on the device. Keep the Unix administration password separate.

Authentication checks can be run on the test device with `sudo python tests/check_pin_auth.py`. They require the compiler and PAM/libxcrypt development headers, create a temporary non-login account and an isolated verifier directory, then remove them. They do not enroll or use the owner's PIN. The source checks for the retained hardware archive remain under `hardware/apollo-base/tools/check_sources.py` and establish source integrity and syntax, not hardware functionality.

The Android integration checks use `sudo python -I tests/check_android_lifecycle.py --apk /path/to/verified/F-Droid-2.0.2.apk` on a provisioned development device with Android stopped and the optional Weston test tool installed. They install a known fixture into the existing Android environment and create a separate headless display. Follow the signature and fixture requirements in [Android usage and tests](android.md); the published result records 31 successful checks without using the physical screen or owner credentials.

The update boundary can be checked with `sudo python tests/check_update_guard.py`. It uses real pacman transactions against generated local packages in disposable roots, with no network access and no changes to the live package database. Read the [development update policy](updates.md) before changing any boot, kernel, firmware or camera package. The current generic PC full-system updater is deliberately stopped; an Apollo upgrade and rollback workflow still needs implementation and device validation.

Building a package does not install it, initialize Android, migrate existing Android data, seed a user's desktop or select a display-manager session. Those migration steps are being validated on the test device before becoming a public installer. The current development workflow retains the previous desktop configuration, original Android data directory and boot/recovery backups privately.

Record the upstream commit, resulting package checksums, dependencies changed and actual device tests for every release. Local integration builds and official signed repository packages must remain distinguishable. Do not disable signature verification to make a remote package install.
