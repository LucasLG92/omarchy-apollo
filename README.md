<p align="center"><img src="media/hero.svg" alt="Omarchy Apollo — native Linux, made for a phone" width="100%"></p>

<p align="center">
  <a href="docs/status.md"><img src="https://img.shields.io/badge/status-experimental-f3c46b?style=flat-square" alt="Experimental"></a>
  <a href="https://github.com/omacom/omarchy/releases/tag/v4.5.0-rc2"><img src="https://img.shields.io/badge/target-Omarchy%204.5%20RC2-87c8ff?style=flat-square" alt="Omarchy 4.5 RC2 target"></a>
  <a href="docs/validation-2026-11-01.md"><img src="https://img.shields.io/badge/evidence-physical%20device-8cf4ce?style=flat-square" alt="Physical-device evidence"></a>
  <a href="docs/evidence/2026-11-01-r19.json"><img src="media/r19-call.svg" alt="One outgoing call and audible voicemail confirmed in R19"></a>
  <a href="LICENSES/README.md"><img src="https://img.shields.io/badge/licenses-MIT%20%2B%20upstream-c7b5ff?style=flat-square" alt="MIT and upstream licenses"></a>
</p>

<p align="center"><a href="docs/es/README.md">Español</a> · <a href="docs/status.md">Hardware status</a> · <a href="docs/validation-2026-11-01.md">Lab notes</a> · <a href="docs/roadmap.md">Roadmap</a> · <a href="CONTRIBUTING.md">Contribute</a></p>

**An independent effort to bring native Omarchy to the Xiaomi Mi 10T Pro (`apollo`).** A touch interface, the normal Linux desktop and a GPU camera pipeline on a Snapdragon phone — with the results and the gaps documented together.

> **Omarchy 4.5 RC2 rebase:** **R19 verified one manually dialed outgoing call and audible voicemail downlink.** The backend reached ACTIVE/OUTGOING and the user confirmed hearing the service. **Microphone/uplink, incoming calls, SMS, cellular IP data, throughput, AEC and the VoLTE path remain unverified.** R19 returned automatically to Android with original readbacks matched; R17 needed buttons, so general recovery reliability is still unproven. **Permanent installation is not completed, and no complete daily-driver phone or validated public installer is claimed.** Earlier results retain their trial scope.

## On the device

<p align="center"><a href="media/apollo-home-r11.png"><img src="media/apollo-home-r11.png" width="200" alt="Actual R11 home-screen capture"></a> <a href="media/apollo-boot-r16.png"><img src="media/apollo-boot-r16.png" width="200" alt="Actual R16 native Plymouth KMS capture"></a> <a href="experiments/original-boot-v2/README.md"><img src="experiments/original-boot-v2/previews/login-initial-432.png" width="200" alt="V2 SDDM Qt render preview; phone PAM login remains untested"></a></p>

<p align="center"><em>Left: actual R11 desktop. Center: actual R16 native splash. Right: a Qt render of the original-style V2 SDDM theme, not a successful phone login. The header is an illustration. No personal notifications or credentials are published.</em></p>

[Original Omarchy V2 sources, touch-keyboard preview and validation boundaries](experiments/original-boot-v2/README.md). The official MIT assets and `#1a1b26` background are retained; the initial 432×960 QML render matches the upstream reference pixel for pixel.

## What is demonstrated

- **Native desktop and touch.** ARM64, systemd, Hyprland and Quickshell on the internal display. Touch input, applications and the on-screen keyboard have been exercised.
- **Outgoing voice and downlink (R19).** GNOME Calls 51.1 was opened without a dial target. The user manually called their voicemail, the backend observed DIALING→ACTIVE / OUTGOING, and the user confirmed audible voicemail. No number or audio recording is published; the agent placed no call.
- **Adreno GPU processing.** Freedreno reports **FD650**. All four camera sensors delivered 640×480 images; the main and ultrawide also passed larger RGB captures.
- **Ordinary phone permissions (R11).** The local user queried calls without the startup OS authentication prompt. Daemon administration and firmware changes still require administrator authentication. R18's PIN UI ran as root only in supervised RAM; ordinary-user integration is still pending.
- **Measured changes.** Increasing CMA from 32 to **256 MiB** resolved the main-camera DMA allocation failure. Normal EFS service stop/restart and original boot/DTBO restoration were checked separately.
- **Physical haptics.** R12 exercised AW8697 rumble for **120 ms at 8192/65535 magnitude** (about 12.5%). The user confirmed a **very low-strength vibration**; normal-session access and feedbackd discovery were also checked.
- **Connected Wi-Fi.** In R13, the user connected on the phone screen and an HTTPS request bound to the Wi-Fi interface returned **200**. No network identity or credentials are published.
- **Sensor scratch-file fix.** Runtime `20261101-6` completed a RAM boot, created the allowed private scratch file and exposed accelerometer/light. The specific missing-file error was absent in the collected boot log and a **20.97-second observation**; this is not a general speed benchmark.
- **Original boot appearance.** R16 ran Plymouth through native DRM/active VT and produced the reviewed KMS capture above. V2 SDDM loads in actual ARM64 test mode and adds touch input to the original layout; **PAM login on the phone remains untested**.
- **Network and SIM UI.** R18 verified local access-PIN unlock and home registration; R19 reported registration and LTE/NR5G again. UI [0.1.3](experiments/sim-unlock/README.md) loaded on the phone in R19, but human acceptance of its PIN2 message remains unconfirmed. PIN2 is not evidence of a second SIM card; slot mapping remains unresolved.

| Component | Latest observed result | Still needed |
| --- | --- | --- |
| Display / GPU / touch | Native desktop, FD650, touch and keyboard | Wider app, accessibility and power testing |
| Main camera | 24 RGB frames at **3000×2256**; GPU pipeline; autofocus reported focused in a separate illuminated sequence | Optical quality, color, video and full-resolution support; **108 MP is unavailable** in this driver |
| Ultrawide / other cameras | Ultrawide: 24 RGB frames at **4200×3120**; all four sensors at 640×480 | Front high-resolution capture, macro focus, orientation and quality |
| Torch | Normal-user one-second on/off control passed | Visible-light confirmation |
| Modem / SIM | R19: registered, LTE/NR5G reported, access PIN not required; secondary PIN2 remains | Physical/logical slot mapping and human acceptance of UI 0.1.3; two slot entries do not establish two physical cards |
| Voice / cellular data | R19: one manual outgoing call ACTIVE, user heard voicemail | Microphone/uplink, incoming calls, SMS, cellular IP Internet, throughput, AEC and VoLTE path |
| Wi-Fi | R13: connected on screen; Wi-Fi-bound HTTPS request returned 200 | Reconnection, both bands, sustained transfer and suspend/resume |
| Bluetooth | Service active | Pairing and audio |
| Sensors / NFC | R13: accelerometer/light available after scratch-file fix; R11: NFC adapter registered | Proximity, NFC tag read and broader sensor acceptance |
| Haptics | R12: very soft physical AW8697 rumble; R13: local access and feedbackd opening from a fresh runtime v6 RAM boot | Strength and wider app feedback |
| Infrared | R12: LIRC detected, capabilities `0x302` queried | **No signal transmitted:** optical emission and remote control untested |
| GPS / fingerprint | Unverified | Native end-to-end support and physical tests |
| Original boot / V2 login | R16: native Plymouth in minimal RAM rescue; ARM64 SDDM test-mode load | Full-desktop handoff, physical greeter interaction, first local credential and PAM login; no touch LUKS unlock |
| Boot / updates / battery | R18/R19 returned automatically; R17 needed buttons; Android/original readbacks verified | **Reliable repeated return**, permanent installation, first local credential/admin setup, standalone boot, updates, suspend and battery life |

See the [full status and evidence links](docs/status.md). A detected device, an authorization check or a passing fixture is not a completed hardware feature.

## Start here

This repository contains the earlier integration, a [clearly separated 4.5 rebase record](docs/rebase-4.5.md), and [reviewable source patches](patches/rebase-4.5/README.md). The public build and recovery path for the new track is incomplete. **Do not flash these files or run a PC Omarchy installer on the phone.**

You can review the source and run the publication checks without connecting a phone:

```sh
git clone https://github.com/LucasLG92/omarchy-apollo.git
cd omarchy-apollo
python3 tests/check_public_docs.py
```

[Rebase and source pins](docs/rebase-4.5.md) · [How results are recorded](docs/validation-2026-11-01.md) · [Architecture and boundaries](docs/architecture.md) · [Historical recipes](docs/build.md)

## Does it work on the regular Mi 10T 5G?

The base is reusable, but **this adaptation is tested only on the Pro development unit**. The regular model needs its main-camera path, RAM/storage provisioning and own calibration validated. The private development image is not a generic direct-flash image, even for another Pro. See the [model matrix and compatibility FAQ](docs/compatibility.md).

## Help move it forward

The most useful contributions are small and reproducible: camera quality/orientation, sensor and device-driver work, phone UI/translation, audio and power measurements, and a reliable native update/recovery path. See the [roadmap](docs/roadmap.md) and [contribution guide](CONTRIBUTING.md) before testing on hardware.

If you want to follow the port, **star the repository**. Bug reports, careful reviews and real device evidence are especially welcome.

## Built on other people's work

This port depends on [Omarchy](https://github.com/omacom/omarchy), [Omarchy Mobile](https://github.com/derekross/omarchy-mobile), [Arch Linux ARM](https://archlinuxarm.org/), [Hyprland](https://github.com/hyprwm/Hyprland), [Quickshell](https://github.com/quickshell-mirror/quickshell), [libcamera](https://libcamera.org/) and the [Apollo hardware packages by royka1](https://github.com/royka1/Xiaomi-Apollo-pmOS-packages). Earlier Android-container work uses [Waydroid](https://github.com/waydroid/waydroid). This is an independent community project, not an official Xiaomi or Omarchy release.

Project integration is MIT licensed; imported components and patches retain their own licenses. See [license and attribution details](LICENSES/README.md) and [media provenance](media/README.md). Proprietary firmware, partition images, per-device calibration and credentials are not distributed. [Security and privacy](SECURITY.md).
