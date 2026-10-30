# Omarchy Apollo

**A native Omarchy desktop, adapted for a phone.**

<p><img src="media/omarchy-desktop.png" width="240" alt="Actual Omarchy Apollo desktop on the phone, with touch keyboard, Wi-Fi, audio and power controls"> <img src="media/touch-lock-preview.png" width="240" alt="Actual device preview of the trusted touch PIN keypad, with an empty field"></p>

Actual device captures: the native desktop and the touch-lock preview. Owner PIN setup and real screen unlocking are still awaiting validation.

Omarchy Apollo brings the Omarchy workflow to the Xiaomi Mi 10T Pro (`apollo`, M2007J3SG): a touch-friendly Linux desktop, phone-style locking and an optional Android environment for APKs without Google services.

APK installation is confirmed with Android's package manager, with 31 device checks covering installation and the on-demand lifecycle. Native camera work now includes a reproducible fix for retained GPU contexts: the old library failed after seven completed opens, while the corrected candidate completed 40 opens and 1,200 frames across all four cameras. The installed package then passed another 12 opens. Physical photo and video acceptance remains pending.

This is an independent experimental port. It is not an official Omarchy image or a finished daily-driver release. The aim is full hardware support; the status below records what has actually been demonstrated.

## The approach

- Run on the phone's internal storage using the existing Apollo kernel and Android boot chain.
- Adapt upstream Omarchy for `aarch64-apollo`, preserving GPU, camera and other device-specific work.
- Keep a recoverable desktop during migration.
- Run ARM Android applications through Waydroid VANILLA, on demand.
- Add a touch PIN without publishing or collecting the owner's secret.

Omarchy now has ARM development builds. Apollo still needs its own integration: a Snapdragon phone is not a Snapdragon X laptop, and its boot layout is not a UEFI PC layout.

## Current progress

| Area | Evidence / current limit |
| --- | --- |
| Native Linux boot | Installed to internal storage; owner verified a cold boot without a PC on the inherited Apollo base |
| GPU | Native Omarchy compositor renders through Freedreno FD650; Waydroid reports FD650 OpenGL ES 3.2 |
| Cameras | All four stream through PipeWire in Omarchy; EGL cleanup fix passes 40 candidate opens and 12 installed-package opens; distinct sensor names and GNOME Camera installed; physical photo/video acceptance pending |
| Wi-Fi | 2.4 and 5 GHz scans and a 5 GHz connection verified on the inherited base; new shell interaction pending |
| Desktop | Native Hyprland 0.57.0 + Omarchy Quickshell session running on the internal panel; live configuration check is clean |
| Touch interface | Portrait scaling and simplified bar; native keyboard integration passes 19 candidate and 19 installed checks, including actual text entry and session-lock recovery; physical touch acceptance pending |
| Display controls | Orientation, auto-rotation and refresh controls installed; 23 isolated device checks include the actual accelerometer and keyboard; physical motion/touch/refresh acceptance pending |
| Android | Confirmed APK installer and on-demand stop/start lifecycle pass 31 device checks, with F-Droid persistence and FD650 rendering; file association registered; physical file-manager, input and cold-boot checks pending |
| Android audio | Stereo AudioTrack reaches an isolated Linux audio sink with both channels verified; physical speaker and microphone acceptance pending |
| Touch lock | PIN verifier and real PAM conversation pass 15 device-local checks; trusted keypad rendered on device; owner PIN setup and real unlocking pending |
| Update safety | Device-stack protection passes 24 isolated ALPM/boundary checks; PC update entrypoints stop before changes; a validated full-system updater remains unfinished |
| Fingerprint | Contact detected previously; enrollment and unlock not implemented |
| Mobile network | No SIM available for calls, SMS or data tests |
| GPS | Service integration exists; outdoor accuracy and reliability remain to be validated |
| USB-C video | Direct cable test produced no image; display output is not supported by this port today |

See [keyboard integration](docs/keyboard.md), [display controls](docs/display.md), [native cameras](docs/cameras.md), [Android usage and tests](docs/android.md), [validation](docs/validation.md), [architecture](docs/architecture.md), [development update policy](docs/updates.md) and [roadmap](docs/roadmap.md). A feature moves to “working” only with device evidence. Inherited results do not imply that a new Omarchy application has passed the same test.

## Source layout

`PKGBUILD` and `packaging/` contain the desktop, keyboard, lock and Android recipes. `patches/` contains the small Apollo changes against a pinned upstream commit. `platform/` owns phone-specific lifecycle boundaries and the APK installer. `config/` contains the touch profile. `lock/` contains local PIN setup and verification; `tests/` contains authentication, package-boundary and Android integration checks. `hardware/apollo-base/` preserves the earlier kernel patches, system services, tests and recovery work, with its original licensing and provenance.

This repository intentionally excludes firmware binaries, partition images, device backups, private diagnostics, network names, account information and credentials. Do not flash a generic Omarchy ARM ISO onto this phone.

[Español](docs/es/README.md) · [Contributing](CONTRIBUTING.md) · [Security and privacy](SECURITY.md)

## Credits

[Omarchy](https://github.com/omacom/omarchy), [Omarchy packages](https://github.com/omacom/omarchy-pkgs), [Arch Linux ARM](https://archlinuxarm.org/), [Hyprland](https://github.com/hyprwm/Hyprland), [Quickshell](https://git.outfoxxed.me/quickshell/quickshell), [Waydroid](https://github.com/waydroid/waydroid), Linux and the Apollo device-port contributors make this work possible. Omarchy is MIT licensed; Linux and individual dependencies retain their respective licenses. This project does not redistribute proprietary Xiaomi firmware.
