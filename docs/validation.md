# Validation record

## Inherited Apollo baseline

The migration starts from the installed r5 base, `linux-apollo 7.1.0-23`. Physical cold boot without a cable and USB reconnection were confirmed by the owner. Existing automated evidence includes camera frame capture and front-camera cycling, GPU rendering, RTC wake and USB maintenance reconnection. The migration must repeat relevant checks inside the new session.

## Omarchy bootstrap

- Official repository metadata retrieved over HTTPS, with ARM dependencies resolved by native pacman.
- Omarchy public key checked against the source recipe checksum; detached package signature verified before trusting it.
- 44 new packages installed; no existing package version changed.
- A staging database-path problem was reconciled from the package manager's generated records. `pacman -Dk` reports no database errors; `pacman -Qk` finds no missing files in the 44 new packages.
- Hyprland reports matching system library versions; Quickshell reports the Omarchy build.
- Waydroid VANILLA ARM system/vendor image initialization completed.

## First native Omarchy session

- SDDM starts the Omarchy uwsm session on the phone's internal panel.
- Hyprland reports the DRM backend, Freedreno FD650, 1080 × 2400 at scale 2.5; live `hyprctl configerrors` is empty.
- Omarchy shell IPC answers `ok`. The initial missing helper packages were installed and the shell restarted successfully. The upstream compositor currently reports two deprecated workspace-rule uses; these are tracked, not hidden.
- The touch keyboard process starts and a dedicated bar control is visible. Owner confirmation of physical touch input is pending.
- Omarchy's screenshot command completes successfully. The public desktop capture is a real full-panel capture reviewed for personal data.
- `Hyprland --verify-config` crashes outside a compositor session with this upstream build. This was not counted as a passing validation; the live session was checked instead.

## Android bootstrap

- Waydroid reaches `sys.boot_completed=1` using existing static binder devices; no new kernel was needed.
- SurfaceFlinger reports `freedreno, FD650, OpenGL ES 3.2 Mesa 26.0.8`.
- F-Droid 2.0.2 was downloaded from its official site, its detached GPG signature checked against the documented F-Droid key, and its APK installed. Android displayed its first-launch notification permission dialog. F-Droid logs record a completed repository update and database integrity check.
- The initial overlay-on-overlay mount was unsupported. Waydroid data was copied to the existing native ext4 storage and verified before enabling a dedicated bind mount. The original data copy is retained privately for recovery. Mount and app persistence across a cold boot remain to be tested.

Not yet acceptance-tested: physical touch navigation and typing, screen PIN, suspend while locked, repeated Android application launch and close from the physical screen, Android audio/camera integration, and cold-boot persistence of the new session. These results do not establish general APK compatibility or full phone hardware support.

## Confirmed APK installation and Android restart

- The published `tests/check_android_lifecycle.py` was actually run on the phone and passed 31 checks on a separate headless Wayland display. It does not capture the physical screen or use an owner credential.
- A malformed APK is rejected by Android and the client reports failure. A signature-verified F-Droid 2.0.2 APK returns confirmed success. Write-only, pipe, path-only, empty and oversized inputs are rejected; root and another desktop UID cannot install in or release the owner's installer session.
- Android stops, starts again, retains F-Droid 2.0.2 and reports Freedreno FD650 in both successful boots. A second stop is harmless. The APK helper has exited before shutdown, no private APK snapshot remains and the user fixture's owner, permissions and contents are unchanged.
- During development, keeping the hardened APK helper alive retained container mounts and caused a restart failure. The desktop client now explicitly releases the helper and waits for process exit. The production lifecycle test passes with its private mount namespace and read-only host protections retained, without a manual root-service stop inside the tested cycle.
- The APK desktop entry passes validation and is the registered MIME handler. Existing associations were backed up privately. Physical file-manager interaction and notification delivery remain pending.
- The suite tested Android integration revision `0.1.0-5`. Installed revision `0.1.0-6` adds the explicit `xdg-utils` dependency; all eight client/helper/service files match both package revisions and the installed files byte for byte. Package files and the native package database validate successfully. The main compositor configuration is clean and shell IPC responds; the PIN-setup process was not interrupted.

See the [sanitized 31-check record](evidence/android-apk-lifecycle-2026-10-30.json) and [reproduction guide](android.md). Stop/start persistence is demonstrated; cold-boot and physical application acceptance are separate pending tests.

## Touch PIN implementation

- The verifier uses libxcrypt yescrypt and keeps a per-user verifier and retry state in root-only storage. Enrollment requires root authorization; the secret travels over stdin rather than process arguments.
- The published `tests/check_pin_auth.py` compiles the real verifier against an isolated data directory and uses a temporary account with a non-login shell. Its 15 checks passed on the phone, including correct and incorrect PIN, caller/user restrictions, private-verifier access, retry delay, lockout, and the real PAM conversation with an independent Unix-password fallback. The temporary service and account were removed; no owner credential was used.
- The keypad is part of the trusted first-party lock surface. The fallback keyboard is embedded in that surface too, avoiding a separate external keyboard above a locked screen. The actual empty-keypad preview has been visually inspected on the phone.
- The local enrollment application has compiled and its empty setup screen has been inspected on the phone. It asks the owner to create and confirm a PIN locally; the administration password is preserved.
- Automatic locking and suspend locking remain disabled until the owner completes setup and the real lock/unlock flow is verified. A rendered preview and automated PAM checks are not a substitute for that acceptance test.

## Package update boundaries

- `omarchy-apollo 0.1.0-7` is installed. The generic Omarchy full update, system-package update and availability check were exercised as the desktop user. They identify the Apollo policy before package updates or PC migrations can begin.
- `tests/check_update_guard.py` passes 24 checks with real pacman transactions in disposable roots. Ordinary application installation, upgrade and removal succeed. Kernel, camera, firmware, PC settings and protected file-path transactions are rejected before extraction; rejected kernel upgrade/removal preserves the old files and installed version. The test also checks privileged Bash startup boundaries, including decoy `-p` arguments. It never changes the live package database.
- Native package-database and package-file checks pass after installation; the kernel remains `linux-apollo 7.1.0-23`.
- A transient missing Lua module was observed when Hyprland's file watcher reloaded during package extraction. The module was present after the transaction. A new post-transaction hook was then installed and actually exercised by the next runtime-package upgrade: compositor diagnostics are clean without a manual reload or shell restart, and the local PIN-setup process remains running with the same PID.
- This is protection for the development image. Coherent full-system upgrade, rollback and replacement boot-image validation remain pending.

The [sanitized device record](evidence/update-guard-2026-10-30.json) contains the individual check names, installed runtime version and package checksum.

## Publishing evidence

Use actual device captures only. Review every capture for network names, notifications, account names, terminal history and secrets. Earlier KDE captures establish the old baseline and must not be presented as Omarchy screenshots. Private source images and raw diagnostics are not public release assets.
