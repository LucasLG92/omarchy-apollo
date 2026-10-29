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

Not yet acceptance-tested: physical touch navigation and typing, screen PIN, suspend while locked, repeated Android application launch and close, Android audio/camera integration, and cold-boot persistence of the new session. These results do not establish general APK compatibility or full phone hardware support.

## Publishing evidence

Use actual device captures only. Review every capture for network names, notifications, account names, terminal history and secrets. Earlier KDE captures establish the old baseline and must not be presented as Omarchy screenshots. Private source images and raw diagnostics are not public release assets.
