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

Not yet acceptance-tested: physical touch navigation and typing, screen PIN, suspend while locked, repeated Android application launch and close from the physical screen, Android physical audio outputs/cameras, and cold-boot persistence of the new session. The later transport test below verifies a narrower digital-audio path. These results do not establish general APK compatibility or full phone hardware support.

## Confirmed APK installation and Android restart

- The published `tests/check_android_lifecycle.py` was actually run on the phone and passed 31 checks on a separate headless Wayland display. It does not capture the physical screen or use an owner credential.
- A malformed APK is rejected by Android and the client reports failure. A signature-verified F-Droid 2.0.2 APK returns confirmed success. Write-only, pipe, path-only, empty and oversized inputs are rejected; root and another desktop UID cannot install in or release the owner's installer session.
- Android stops, starts again, retains F-Droid 2.0.2 and reports Freedreno FD650 in both successful boots. A second stop is harmless. The APK helper has exited before shutdown, no private APK snapshot remains and the user fixture's owner, permissions and contents are unchanged.
- During development, keeping the hardened APK helper alive retained container mounts and caused a restart failure. The desktop client now explicitly releases the helper and waits for process exit. The production lifecycle test passes with its private mount namespace and read-only host protections retained, without a manual root-service stop inside the tested cycle.
- The APK desktop entry passes validation and is the registered MIME handler. Existing associations were backed up privately. Physical file-manager interaction and notification delivery remain pending.
- The suite tested Android integration revision `0.1.0-5`. Installed revision `0.1.0-6` adds the explicit `xdg-utils` dependency; all eight client/helper/service files match both package revisions and the installed files byte for byte. Package files and the native package database validate successfully. The main compositor configuration is clean and shell IPC responds; the PIN-setup process was not interrupted.

See the [sanitized 31-check record](evidence/android-apk-lifecycle-2026-10-30.json) and [reproduction guide](android.md). Stop/start persistence is demonstrated; cold-boot and physical application acceptance are separate pending tests.

## Android stereo audio transport

The real Android `AudioTrack` framework played 144,000 stereo frames at 48 kHz through AudioFlinger and the image's audio HAL to an isolated Linux PulseAudio/PipeWire server. Distinct 997 Hz and 1499 Hz signals were recovered from the correct monitor channels. The fixture runs as Android shell UID 2000; it is not an installed application compatibility test.

The temporary server used WirePlumber's policy-only profile and had no physical audio devices. Android had no `/dev/snd`; only synthetic monitor samples were analyzed in RAM. No room microphone or physical speaker was used. Android stopped afterwards, and the existing desktop audio processes, default sink and PIN-setup process were unchanged. The [result and source hashes](evidence/android-audio-transport-2026-10-30.json) and [reproduction procedure](android.md#android-audio-transport) retain these limits. Physical output, microphone quality, latency, long sessions and suspend remain pending.

The separate [six-check phase-acknowledgement record](evidence/test-phase-ack-2026-10-30.json) covers a descriptor-based ownership fix in the root developer-test controller. It does not change the installed APK service or retrospectively rerun the original lifecycle suite.

## Touch PIN implementation

- The verifier uses libxcrypt yescrypt and keeps a per-user verifier and retry state in root-only storage. Enrollment requires root authorization; the secret travels over stdin rather than process arguments.
- The published `tests/check_pin_auth.py` compiles the real verifier against an isolated data directory and uses a temporary account with a non-login shell. Its 15 checks passed on the phone, including correct and incorrect PIN, caller/user restrictions, private-verifier access, retry delay, lockout, and the real PAM conversation with an independent Unix-password fallback. The temporary service and account were removed; no owner credential was used.
- The keypad is part of the trusted first-party lock surface. The fallback keyboard is embedded in that surface too, avoiding a separate external keyboard above a locked screen. The actual empty-keypad preview has been visually inspected on the phone.
- The local enrollment application has compiled and its empty setup screen has been inspected on the phone. It asks the owner to create and confirm a PIN locally; the administration password is preserved.
- Automatic locking and suspend locking remain disabled until the owner completes setup and the real lock/unlock flow is verified. A rendered preview and automated PAM checks are not a substitute for that acceptance test.

## Display controls and orientation

Mobile profile `0.1.0-8` introduced a GTK display-settings application and an event-driven desktop-user controller. The [23 actual device checks](evidence/display-controls-2026-10-30.json) run the real implementation on a private nested Hyprland compositor, including all four monitor/touch transform pairs, real accelerometer claim/release, a failed preference write and rollback, compositor reload, service restart, keyboard dimensions and GTK window creation. Sensor authorization succeeds in the normal desktop-user service context; no sensor policy was changed to accommodate the test.

The installed executable matches the tested digest. All 15 package payload files, the prior 15-file payload, package-file checks and the native package database were verified. The installed PIN-setup guard rejected an actual change request without altering the physical panel, and the PIN and main audio processes were preserved. The keyboard was restarted while hidden with the new landscape height. Physical touch mapping, actual motion through all orientations, refresh changes, battery impact and cold boot remain pending. See the [procedure and limits](display.md).

## Native keyboard input and session locking

Installed mobile profile `0.1.0-9` and wvkbd `0.20-2` pass [19 candidate checks and 19 installed-binary checks](evidence/keyboard-lifecycle-2026-10-30.json). Both runs use byte-identical native executables and include 12 actual write/hide/show cycles, three GTK text-focus cycles, two real nested session locks, Ctrl-latch cleanup and three native service starts followed immediately by show signals. The repeated input test exposed a pending popup frame callback during hiding; the patch cancels both drawing-surface callbacks and releases the popup viewport before reuse.

The public reproduction runner was actually executed against the installed binary. Its virtual-pointer and lock fixtures refuse the physical output and ordinary desktop runtime. Only synthetic fixture text is used. Installation checked all 23 new package payload files against the reviewed archives, all 17 prior files, package-file consistency and the native package database. The desktop, audio, display controller and owner PIN-setup processes were preserved.

Automatic text-input mode is selected only after a root-owned public enrollment marker exists and the setup surface has finished. The installed keyboard remains hidden in manual mode while enrollment is open. Its button guard and setup-success-hook guard were actually exercised in that state. Real enrollment completion, the automatic transition, physical finger typing, owner PIN unlocking, Android/toolkit compatibility, suspend and cold boot remain pending. See the [keyboard guide](keyboard.md).

## Native camera application stack and EGL lifecycle

- The PipeWire GStreamer plugin and GNOME Camera / Snapshot 51.0 were installed with required repository signature verification. No existing package version changed during those dependency installations. The camera application's isolated launch reached its access-permission dialog; it did not become an accepted graphical preview test.
- The mobile camera policy now exposes four distinct sensor descriptions. The original configuration produced only two distinct descriptions for four sources. Actual PipeWire properties confirm the new descriptions and priorities.
- `tests/check_camera_streams.py` was run against the installed old library and the candidate using the same source bytes. The control completed seven of 12 planned opens, then failed. The test-only EGL interposer counted seven successful context creations and zero context destructions before the policy service stopped. DMA-heap allocation errors were observed in the failed reopen.
- Corrected candidate `libcamera-apollo 0.7.2-3` completed 40 opens in one continuous WirePlumber process: 10 per sensor and 30 complete 640×480 RGBA buffers per open, with advancing timestamps. The real EGL counters were 40 created and 40 destroyed; FD650 rendering was observed. The interposer does not alter EGL results. No frames were saved.
- Candidate and audit overrides were removed and the ordinary installed library restored before the reviewed package transaction. The retained old archive matched 58 installed files/links. The update changed only the camera-library package; all new installed files match the reviewed candidate archive. The kernel remains version 23 and the normal device-stack guard and its configuration are unchanged.
- The installed revision then passed 12 more opens / 360 frames in its ordinary environment. Package/database validation, live shell IPC and compositor checks pass. PipeWire/Pulse and owner PIN-setup processes were preserved. Mobile revision 6 adds the minimum fixed-camera dependency, with its 11 payload files compared byte for byte against tested revision 5.
- The package build passed all three existing Samsung gain-helper checks. No exported camera or camera-base symbol was removed. This test does not establish physical picture quality, camera permission acceptance, saved photos/video, orientation, Android camera access or cold-boot reliability.

See the [camera procedure](cameras.md) and [sanitized before/candidate/installed evidence](evidence/camera-egl-lifecycle-2026-10-30.json). The historical sensor-power and focus tests remain evidence for their original kernel/base versions.

## Package update boundaries

- `omarchy-apollo 0.1.0-7` is installed. The generic Omarchy full update, system-package update and availability check were exercised as the desktop user. They identify the Apollo policy before package updates or PC migrations can begin.
- `tests/check_update_guard.py` passes 24 checks with real pacman transactions in disposable roots. Ordinary application installation, upgrade and removal succeed. Kernel, camera, firmware, PC settings and protected file-path transactions are rejected before extraction; rejected kernel upgrade/removal preserves the old files and installed version. The test also checks privileged Bash startup boundaries, including decoy `-p` arguments. It never changes the live package database.
- Native package-database and package-file checks pass after installation; the kernel remains `linux-apollo 7.1.0-23`.
- A transient missing Lua module was observed when Hyprland's file watcher reloaded during package extraction. The module was present after the transaction. A new post-transaction hook was then installed and actually exercised by the next runtime-package upgrade: compositor diagnostics are clean without a manual reload or shell restart, and the local PIN-setup process remains running with the same PID.
- This is protection for the development image. Coherent full-system upgrade, rollback and replacement boot-image validation remain pending.

The [sanitized device record](evidence/update-guard-2026-10-30.json) contains the individual check names, installed runtime version and package checksum.

## Publishing evidence

Use actual device captures only. Review every capture for network names, notifications, account names, terminal history and secrets. Earlier KDE captures establish the old baseline and must not be presented as Omarchy screenshots. Private source images and raw diagnostics are not public release assets.
