> Historical Apollo r5 baseline. This is preserved implementation and recovery documentation, not an Omarchy acceptance report. See the repository root for current status.

# Apollo Linux

### From Android handset to a native Linux desktop

**Arch Linux ARM · KDE Plasma Wayland · Xiaomi Mi 10T Pro / Apollo**

Apollo Linux brings a desktop Linux environment to a phone you can hold in one hand. It boots from the phone’s own storage, runs a touch-friendly KDE desktop and uses the Adreno GPU through Freedreno and Turnip. The goal is a device you can use, inspect and develop directly on the phone.

**The r5 development base is installed and tested on real hardware.** The owner confirmed power-on to the desktop with no PC or USB cable attached. Reconnecting to the PC restored maintenance access with the new boot, installed kernel and persistent data verified.

[What changed in r5](docs/releases/r5.md) · [Hardware status](docs/STATUS.md) · [Test evidence](docs/TESTS.md) · [Español](docs/README.es.md)

<table>
<tr>
<td align="center"><img src="media/installed-desktop.png" width="270" alt="Real r5 desktop on Apollo with WiFi and keyboard controls"><br><b>KDE on the installed phone</b></td>
<td align="center"><img src="media/installed-status.png" width="270" alt="Real terminal showing installed r5, ARM64, kernel 23 and WiFi band without network identifiers"><br><b>Real system, verified state</b></td>
</tr>
</table>

Actual screenshots captured on the device, reviewed for visible private information and metadata. The theme and wallpaper are the owner’s choices. Earlier RAM-boot screenshots remain in the [Spanish overview](docs/README.es.md).

## What makes this milestone useful

- **A desktop that stays on the phone.** Internal installation, persistent files and settings, on-screen keyboard, larger touch controls and a graphical WiFi selector.
- **Hardware you can exercise.** Native GPU rendering, four cameras delivering frames and WiFi at 5 GHz. GPS fixes and hardware video decoding are documented with their original test versions.
- **Kernel work backed by tests.** 25 included patches, a clock regression reproduced with real KUnit tests, native checks before and after suspend, and explicit recovery handling for this upgrade.
- **A project you can inspect.** Package recipes, integration sources, test tools, known failures and remaining work are public. Device secrets, personal data and proprietary firmware stay out of the repository.

## New in r5 / kernel 23

The clock fix removes the observed DSI PLL startup failure and two clock reference warnings while preserving the 1080×2400 / 144 Hz display. Two separate SPMI warnings remain open.

USB setup now runs after the switch to the installed root filesystem. The service preserves a compatible active connection and handles a controller that appears later. Cold boot without a cable, physical reconnection and return from a short RTC suspend were checked on the phone.

| Validation | Observed result |
| --- | --- |
| Real clock-framework tests | 117 passed; 4 existing skips. The three new regression cases pass after the fix |
| Four cameras | 90 frames per camera before/after suspend, plus a further set after permanent installation |
| Front camera | 24 additional power/open cycles after suspend, 5 frames per cycle |
| Focus controls | 100 cycles before suspend + 40 after; optical autofocus still needs validation |
| GPU | Vulkan/Wayland rendering before/after suspend and after installation; EGL uses Freedreno FD650 / GLES 3.2 |
| USB software tests | 12 simulated cases; native service, DHCP and SSH checked separately |
| Upgrade recovery tests | 7 owned-file simulations, including partial-write and readback failures; native upgrade and boot readback verified |

Camera power-cycle fixtures temporarily released WirePlumber’s camera observers and restored the service afterwards. Normal frame capture used the desktop user with the full session active. These are bounded regression tests, not long-term reliability or battery measurements. See the [full r5 engineering notes](docs/CANDIDATE-23.md).

## What works, and what is still open

| Area | Current state |
| --- | --- |
| Desktop, display and touch | Native KDE Wayland; 1080×2400 / 144 Hz; phone-sized controls and keyboard |
| GPU | Freedreno / Turnip; native rendering tested |
| WiFi | Graphical network selection; 2.4/5 GHz scans; verified HTTPS over 5 GHz |
| Cameras | Four sensors deliver frames; repeated front-camera and focus-control tests pass within the documented conditions |
| GPS and video | Real GeoClue fixes without a SIM; H.264/HEVC/VP9 hardware decoding tested in earlier documented runs |
| Audio | PipeWire, PulseAudio compatibility and WirePlumber active; complete route and microphone validation remains |
| Fingerprint reader | Physical contact detected on kernel 21; enrollment, matching and unlock remain open |
| Cellular | Modem recognized; calls, SMS and mobile data still need an active SIM test |
| USB-C display | Direct monitor test produced no image; DisplayPort is not working |
| Daily use | Battery, thermals, long suspend and accessory coverage need more testing |

**This is an experimental development port for M2007J3SG, not a daily-driver release.** It uses Arch Linux ARM and is not an official CachyOS edition. It does not provide a universal bootloader or support arbitrary operating systems. Desktop startup alone does not establish complete phone support.

## Explore or contribute

Start with the [hardware matrix](docs/STATUS.md) and [test history](docs/TESTS.md), then the [roadmap](docs/ROADMAP.md). Useful next contributions include fingerprint protocol work, optical camera testing, audio routes, power measurements and accessory testing. Reports should state the exact kernel/revision and avoid raw logs containing identifiers.

| Source | Contents |
| --- | --- |
| `port-source/` | Kernel configuration and 25 patches, package recipes, camera/modem/location/video integration |
| `port-source/apollo-hardware-tests/` | Device diagnostics and bounded hardware tests |
| `system/` | Persistent boot, USB maintenance, desktop integration and transition-specific update tools |
| `tools/` | Source integrity checks and software regression tests |

[Build notes](docs/BUILD.md) · [Installation and recovery](docs/INSTALL.md) · [Privacy](docs/PRIVACY.md) · [Credits and licensing](docs/PROVENANCE.md)

This source snapshot is not yet a complete image builder validated from a clean environment. No flashable images, root filesystems, proprietary firmware, calibration data, NV/EFS or phone backups are distributed. Any installation requires device-specific preparation and verified recovery material. The original Android data erase was explicitly authorized; subsequent r5 updates did not reformat userdata.

Built on the work of the Apollo port and the wider Linux community. Original credits and licenses are retained in [PROVENANCE](docs/PROVENANCE.md).
