<p align="center"><img src="media/hero.svg" alt="Omarchy Apollo — native Linux, made for a phone" width="100%"></p>

<p align="center">
  <a href="docs/status.md"><img src="https://img.shields.io/badge/status-experimental-f3c46b?style=flat-square" alt="Experimental"></a>
  <a href="https://github.com/omacom/omarchy/releases/tag/v4.5.0-rc2"><img src="https://img.shields.io/badge/target-Omarchy%204.5%20RC2-87c8ff?style=flat-square" alt="Omarchy 4.5 RC2 target"></a>
  <a href="docs/validation-2026-11-02.md"><img src="media/r20-root.svg" alt="R20: native installation and normal boot verified on one Pro unit"></a>
  <a href="docs/evidence/2026-11-01-r19.json"><img src="media/r19-call.svg" alt="One outgoing call and audible voicemail confirmed in R19"></a>
  <a href="LICENSES/README.md"><img src="https://img.shields.io/badge/licenses-MIT%20%2B%20upstream-c7b5ff?style=flat-square" alt="MIT and upstream licenses"></a>
</p>

<p align="center"><a href="docs/es/README.md">Español</a> · <a href="docs/status.md">Hardware status</a> · <a href="docs/validation-2026-11-02.md">Latest lab notes</a> · <a href="docs/roadmap.md">Roadmap</a> · <a href="CONTRIBUTING.md">Contribute</a></p>

**An independent effort to bring native Omarchy to the Xiaomi Mi 10T Pro (`apollo`).** A touch interface, the normal Linux desktop and a GPU camera pipeline on a Snapdragon phone — with the results and the gaps documented together.

> **R20 · native installation completed on the development unit.** **Omarchy 4.5 RC2 now boots normally from its flashed native boot and internal ext4 root**, including a repeated boot after Android cleanup. The user entered the local credential and reached the desktop. HOME and hold-for-recents gestures work; one automatic cellular IPv4 connection returned HTTPS 204 with Wi-Fi off. **This is still an experimental phone:** Polkit, microphone/uplink, incoming calls, SMS, IPv6, battery/suspend and several sensors remain unverified. The latest logo was not observed by the user; gesture/keyboard polish continues. [Evidence and exact limits](docs/validation-2026-11-02.md).

## On the device

<p align="center"><a href="media/apollo-home-r11.png"><img src="media/apollo-home-r11.png" width="200" alt="Actual R11 home-screen capture"></a> <a href="media/apollo-boot-r16.png"><img src="media/apollo-boot-r16.png" width="200" alt="Actual R16 native Plymouth KMS capture"></a> <a href="experiments/original-boot-v2/README.md"><img src="experiments/original-boot-v2/previews/login-initial-432.png" width="200" alt="V2 SDDM Qt preview; later successful phone login is recorded separately"></a></p>

<p align="center"><em>Left: actual R11 desktop. Center: actual R16 native splash. Right: a Qt render of the original-style V2 SDDM theme, not a successful phone login. The header is an illustration. No personal notifications or credentials are published.</em></p>

[Original Omarchy V2 sources, touch-keyboard preview and validation boundaries](experiments/original-boot-v2/README.md). The official MIT assets and `#1a1b26` background are retained; the initial 432×960 QML render matches the upstream reference pixel for pixel.

## What is demonstrated

- **Installed native boot (R20).** Internal ext4 root, systemd and the native hardware target boot through the flashed native boot path, without `fastboot boot`. Repeated normal boot passed after Android cleanup, with firmware/calibration guards and expected boot/recovery image-prefix readback checked.
- **Local owner login.** The user accepted the mobile setup layout, saved a credential and later logged in after normal boot. Autologin is empty and the original theme is selected. [Owner form r5 and its isolated test](experiments/owner-setup/README.md); Polkit authentication and human acceptance of the setup auto-close remain pending.
- **Touch navigation.** The user confirmed HOME and hold-for-recents. Gesture thresholds and unwanted keyboard popups still need refinement.
- **Native desktop and touch.** ARM64, systemd, Hyprland and Quickshell on the internal display. Touch input, applications and the on-screen keyboard have been exercised.
- **Outgoing voice and downlink (R19).** GNOME Calls 51.1 was opened without a dial target. The user manually called their voicemail, the backend observed DIALING→ACTIVE / OUTGOING, and the user confirmed audible voicemail. No number or audio recording is published; the agent placed no call.
- **Adreno GPU processing.** Freedreno reports **FD650**. All four camera sensors delivered 640×480 images; the main and ultrawide also passed larger RGB captures.
- **Ordinary phone permissions (R11).** The local user queried calls without the startup OS authentication prompt. Daemon administration and firmware changes still require administrator authentication. R18's PIN UI ran as root only in supervised RAM; ordinary-user integration is still pending.
- **Measured changes.** Increasing CMA from 32 to **256 MiB** resolved the main-camera DMA allocation failure. Normal EFS service stop/restart and original boot/DTBO restoration were checked separately.
- **Physical haptics.** R12 exercised AW8697 rumble for **120 ms at 8192/65535 magnitude** (about 12.5%). The user confirmed a **very low-strength vibration**; normal-session access and feedbackd discovery were also checked.
- **Cellular IPv4 on the internal root.** Automatic profile candidate r2 created a fresh profile after normal boot and selected an active cellular route; the bound request returned **HTTPS 204 with Wi-Fi off**. This is one network test, not universal SIM/APN support or a speed result. The latest cold boot was waiting for local SIM-PIN entry; IPv6, sustained transfer and reconnection remain unvalidated. No operator, APN, address or browser screenshot is published.
- **Connected Wi-Fi.** In R13, the user connected on the phone screen and an HTTPS request bound to the Wi-Fi interface returned **200**. No network identity or credentials are published.
- **Sensor scratch-file fix.** Runtime `20261101-6` completed a RAM boot, created the allowed private scratch file and exposed accelerometer/light. The specific missing-file error was absent in the collected boot log and a **20.97-second observation**; this is not a general speed benchmark.
- **Original boot appearance.** R16 ran Plymouth through native DRM/active VT and produced the reviewed KMS capture above. V2 SDDM loads in actual ARM64 test mode and adds touch input to the original layout; **later R20 normal-boot login passed**, while the latest splash logo still lacks human confirmation.
- **SIM UI version boundary.** The installed app is **0.2.1-1**, compact, with masked button fields and its own keypad instead of a text-input/OSK surface. The controller reports unchanged radio core/13 flow methods, 18 classification checks and 17 ARM64 GTK synthetic checks. **Human PIN entry in 0.2.1 is not yet confirmed:** the latest cold boot reports primary access PIN `SIM_PIN` (2) and no user Wayland session yet. The [published 0.1.3 source](experiments/sim-unlock/README.md) and R18/R19 registration remain historical; no new UI source is included.

| Component | Latest observed result | Still needed |
| --- | --- | --- |
| Display / GPU / touch | Native desktop, FD650, touch and keyboard | Wider app, accessibility and power testing |
| Main camera | 24 RGB frames at **3000×2256**; GPU pipeline; autofocus reported focused in a separate illuminated sequence | Optical quality, color, video and full-resolution support; **108 MP is unavailable** in this driver |
| Ultrawide / other cameras | Ultrawide: 24 RGB frames at **4200×3120**; all four sensors at 640×480 | Front high-resolution capture, macro focus, orientation and quality |
| Torch | Normal-user one-second on/off control passed | Visible-light confirmation |
| Modem / SIM | R18/R19 registration is historical; latest cold boot requires primary access PIN `SIM_PIN` (2), with no user Wayland session yet | Local PIN completion/current registration and physical/logical slot mapping; PIN2 is not a second SIM |
| SIM UI | Installed 0.2.1-1: compact button/password-buffer keypad; controller reports 18 classification + 17 ARM GTK synthetic checks | Human cold-boot PIN entry not confirmed; repository source 0.1.3 retains its historical scope |
| Voice / cellular data | R19: outgoing call and audible voicemail. R20: automatic r2 cellular IPv4 route + HTTPS 204 with Wi-Fi off on one network | Microphone/uplink, incoming calls, SMS, IPv6, other SIMs/networks, latest cold-boot PIN completion, throughput, AEC and VoLTE path |
| Wi-Fi | R13: connected on screen; Wi-Fi-bound HTTPS request returned 200 | Reconnection, both bands, sustained transfer and suspend/resume |
| Bluetooth | Service active | Pairing and audio |
| Sensors / NFC | R13: accelerometer/light available after scratch-file fix; R11: NFC adapter registered | Proximity, NFC tag read and broader sensor acceptance |
| Haptics | R12: very soft physical AW8697 rumble; R13: local access and feedbackd opening from a fresh runtime v6 RAM boot | Strength and wider app feedback |
| Infrared | R12: LIRC detected, capabilities `0x302` queried | **No signal transmitted:** optical emission and remote control untested |
| GPS / fingerprint | Unverified | Native end-to-end support and physical tests |
| Native boot / local login | R20: native installation completed, repeated normal internal-root boot and human credential→desktop login | Polkit authentication, extended boot/recovery coverage and a reproducible public installer |
| Original boot / touch | R16 native splash capture; R20 original-theme login, HOME and hold-for-recents confirmed | Latest splash logo not human-confirmed; gesture/keyboard polish, no touch LUKS unlock |
| Updates / battery | Native boot persists; earlier Android-return results are historical | Upgrade/rollback, unplugged power behavior, suspend and battery life |

See the [full status and evidence links](docs/status.md). A detected device, an authorization check or a passing fixture is not a completed hardware feature.

## Start here

This repository contains the earlier integration, a [clearly separated 4.5 rebase record](docs/rebase-4.5.md), and [reviewable source patches](patches/rebase-4.5/README.md). The public build and recovery path for the new track is incomplete. **Do not flash these files or run a PC Omarchy installer on the phone.**

You can review the source and run the publication checks without connecting a phone:

```sh
git clone https://github.com/LucasLG92/omarchy-apollo.git
cd omarchy-apollo
python3 tests/check_public_docs.py
```

[Rebase and source pins](docs/rebase-4.5.md) · [R20 internal-root record](docs/validation-2026-11-02.md) · [Earlier hardware trials](docs/validation-2026-11-01.md) · [Transfer verification lesson](docs/internal-root-transfer.md) · [Historical recipes](docs/build.md)

## Does it work on the regular Mi 10T 5G?

The base is reusable, but **this adaptation is tested only on the Pro development unit**. The regular model needs its main-camera path, RAM/storage provisioning and own calibration validated. The private development image is not a generic direct-flash image, even for another Pro. See the [model matrix and compatibility FAQ](docs/compatibility.md).

## Help move it forward

The most useful contributions are small and reproducible: camera quality/orientation, sensor and device-driver work, phone UI/translation, audio and power measurements, and a reliable native update/recovery path. See the [roadmap](docs/roadmap.md) and [contribution guide](CONTRIBUTING.md) before testing on hardware.

If you want to follow the port, **star the repository**. Bug reports, careful reviews and real device evidence are especially welcome.

## Built on other people's work

This port depends on [Omarchy](https://github.com/omacom/omarchy), [Omarchy Mobile](https://github.com/derekross/omarchy-mobile), [Arch Linux ARM](https://archlinuxarm.org/), [Hyprland](https://github.com/hyprwm/Hyprland), [Quickshell](https://github.com/quickshell-mirror/quickshell), [libcamera](https://libcamera.org/) and the [Apollo hardware packages by royka1](https://github.com/royka1/Xiaomi-Apollo-pmOS-packages). Earlier Android-container work uses [Waydroid](https://github.com/waydroid/waydroid). This is an independent community project, not an official Xiaomi or Omarchy release.

Project integration is MIT licensed; imported components and patches retain their own licenses. See [license and attribution details](LICENSES/README.md) and [media provenance](media/README.md). Proprietary firmware, partition images, per-device calibration and credentials are not distributed. [Security and privacy](SECURITY.md).
