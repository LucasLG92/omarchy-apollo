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

> **Native installation works; desktop startup has an open regression.** Omarchy 4.5 RC2 boots from flashed native boot and internal ext4. After the latest cold boot, local login passed and SIM UI **0.2.1 accepted the access PIN entered only on the handset**; a cellular-bound IPv4 request returned HTTPS 204 with Wi-Fi connected. **The desktop center turned black again after login while the bar/search pill remained visible.** An official Quickshell restart on installed shell .8 restored the home screen, and the user accepted basic r2 HOME/recents/keyboard closing. **The recurring startup cause/fix is unresolved.** Polkit, broader phone hardware and daily-driver acceptance remain unverified. [Evidence and exact limits](docs/validation-2026-11-02.md).

## On the device

<p align="center"><a href="media/apollo-home-r11.png"><img src="media/apollo-home-r11.png" width="200" alt="Actual R11 home-screen capture"></a> <a href="media/apollo-boot-r16.png"><img src="media/apollo-boot-r16.png" width="200" alt="Actual R16 native Plymouth KMS capture"></a> <a href="experiments/original-boot-v2/README.md"><img src="experiments/original-boot-v2/previews/login-initial-432.png" width="200" alt="V2 SDDM Qt preview; later successful phone login is recorded separately"></a></p>

<p align="center"><em>Left: actual R11 desktop. Center: actual R16 native splash. Right: a Qt render of the original-style V2 SDDM theme, not a successful phone login. The header is an illustration. No personal notifications or credentials are published.</em></p>

[Original Omarchy V2 sources, touch-keyboard preview and validation boundaries](experiments/original-boot-v2/README.md). The official MIT assets and `#1a1b26` background are retained; the initial 432×960 QML render matches the upstream reference pixel for pixel.

## What is demonstrated

- **Installed native boot (R20).** Internal ext4 root, systemd and the native hardware target boot through the flashed native boot path, without `fastboot boot`. Repeated normal boot passed after Android cleanup, with firmware/calibration guards and expected boot/recovery image-prefix readback checked.
- **Local owner login.** The user accepted the mobile setup layout, saved a credential and later logged in after normal boot. Autologin is empty and the original theme is selected. [Owner form r5 and its isolated test](experiments/owner-setup/README.md); Polkit authentication and human acceptance of the setup auto-close remain pending.
- **Touch navigation.** After shell .8/r2 installation, the user confirmed basic HOME, hold-for-recents and keyboard closing. Wider refinement remains open; returning Home when the final recent app is closed is still pending.
- **Native desktop and touch.** ARM64, systemd, Hyprland and Quickshell run on the internal display. The latest cold-boot login reproduced a black home-screen center, recovered by an official shell restart. This recurrence remains an open startup/rendering issue.
- **Outgoing voice and downlink (R19).** GNOME Calls 51.1 was opened without a dial target. The user manually called their voicemail, the backend observed DIALING→ACTIVE / OUTGOING, and the user confirmed audible voicemail. No number or audio recording is published; the agent placed no call.
- **Adreno GPU processing.** Freedreno reports **FD650**. All four camera sensors delivered 640×480 images; the main and ultrawide also passed larger RGB captures.
- **Ordinary phone permissions (R11).** The local user queried calls without the startup OS authentication prompt. Daemon administration and firmware changes still require administrator authentication. R18's PIN UI ran as root only in supervised RAM; ordinary-user integration is still pending.
- **Measured changes.** Increasing CMA from 32 to **256 MiB** resolved the main-camera DMA allocation failure. Normal EFS service stop/restart and original boot/DTBO restoration were checked separately.
- **Physical haptics.** R12 exercised AW8697 rumble for **120 ms at 8192/65535 magnitude** (about 12.5%). The user confirmed a **very low-strength vibration**; normal-session access and feedbackd discovery were also checked.
- **Cellular IPv4 on the internal root.** Automatic profile r2 was active after the latest local SIM-PIN entry; a request **bound to cellular returned HTTPS 204 while Wi-Fi was connected/preferred**. Earlier Wi-Fi-off results keep their scope. One network is tested; other SIMs/networks, IPv6, sustained transfer and throughput remain unvalidated. No operator, APN, address or screenshot is published.
- **Connected Wi-Fi.** In R13, the user connected on the phone screen and an HTTPS request bound to the Wi-Fi interface returned **200**. No network identity or credentials are published.
- **Sensor scratch-file fix.** Runtime `20261101-6` completed a RAM boot, created the allowed private scratch file and exposed accelerometer/light. The specific missing-file error was absent in the collected boot log and a **20.97-second observation**; this is not a general speed benchmark.
- **Original boot appearance.** R16 ran Plymouth through native DRM/active VT and produced the reviewed KMS capture above. V2 SDDM loads in actual ARM64 test mode and adds touch input to the original layout; **later R20 normal-boot login passed**, while the latest splash logo still lacks human confirmation.
- **SIM UI version boundary.** The installed app is **0.2.1-1**, compact, with masked button fields and its own keypad instead of a text-input/OSK surface. The controller reports unchanged radio core/13 flow methods, 18 classification checks and 17 ARM64 GTK synthetic checks. **Human local access-PIN entry in 0.2.1 passed after cold boot:** the modem reached connected/home, primary PIN was no longer required and remaining lock was secondary `SIM_PIN2` (3). This does not mean a second SIM card or complete UI acceptance. The [published 0.1.3 source](experiments/sim-unlock/README.md) and R18/R19 registration remain historical; no new UI source is included.

| Component | Latest observed result | Still needed |
| --- | --- | --- |
| Display / GPU / touch | FD650/touch; recurrent black center after cold-boot login, bar/search pill visible; official shell restart recovered Home | **Startup/rendering cause and definitive fix open**, wider app/accessibility/power testing |
| Main camera | 24 RGB frames at **3000×2256**; GPU pipeline; autofocus reported focused in a separate illuminated sequence | Optical quality, color, video and full-resolution support; **108 MP is unavailable** in this driver |
| Ultrawide / other cameras | Ultrawide: 24 RGB frames at **4200×3120**; all four sensors at 640×480 | Front high-resolution capture, macro focus, orientation and quality |
| Torch | Normal-user one-second on/off control passed | Visible-light confirmation |
| Modem / SIM | Latest cold boot: local access PIN accepted, connected/home, primary PIN no longer required; remaining secondary PIN2 enum3 | Physical/logical slot mapping and wider stability; PIN2 is not a second SIM |
| SIM UI | Installed 0.2.1-1: human local access-PIN entry passed after cold boot; earlier synthetic checks retained | Broader UI/retry/error acceptance; repository source 0.1.3 remains historical |
| Voice / cellular data | R19 outgoing voicemail/downlink. Latest R20: active AUTO profile, cellular-bound IPv4 HTTPS204 with Wi-Fi connected/preferred | Microphone/uplink, incoming calls, SMS, IPv6, other SIMs/networks, throughput, AEC and VoLTE path |
| Wi-Fi | R13: connected on screen; Wi-Fi-bound HTTPS request returned 200 | Reconnection, both bands, sustained transfer and suspend/resume |
| Bluetooth | Service active | Pairing and audio |
| Sensors / NFC | R13: accelerometer/light available after scratch-file fix; R11: NFC adapter registered | Proximity, NFC tag read and broader sensor acceptance |
| Haptics | R12: very soft physical AW8697 rumble; R13: local access and feedbackd opening from a fresh runtime v6 RAM boot | Strength and wider app feedback |
| Infrared | R12: LIRC detected, capabilities `0x302` queried | **No signal transmitted:** optical emission and remote control untested |
| GPS / fingerprint | Unverified | Native end-to-end support and physical tests |
| Native boot / local login | R20: native installation completed, repeated normal internal-root boot and human credential→desktop login | Polkit authentication, extended boot/recovery coverage and a reproducible public installer |
| Original boot / touch | R16 splash capture; R20 login; shell .8/r2 basic HOME, recents and keyboard closing human-confirmed | Latest logo not human-confirmed, further polish and last-app→Home behavior pending; no touch LUKS unlock |
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
