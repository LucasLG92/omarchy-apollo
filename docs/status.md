# Hardware status

**Current track:** Omarchy 4.5 RC2 rebase, last recorded trial **R11 · 2026-11-01**. Results are from one Apollo development device. They are not independent certification or a claim that every Mi 10T variant behaves identically.

The target is a complete, fast native Linux phone. That target is **not achieved**. The new track remains RAM-only; Android and original boot partitions were restored after the tests. No permanent 4.5 installation, complete public installer or working native updater is claimed.

| Area | Evidence / latest result | Acceptance gap |
| --- | --- | --- |
| Native OS | Omarchy `4.5.0rc2-1`; systemd PID 1; Hyprland/Quickshell on ARM64 | Permanent installation and repeated standalone boot |
| Display / touch | Internal portrait display and FD650 GPU; touch, app opening and keyboard exercised | App coverage, gesture polish, accessibility and sustained performance |
| Main camera — S5KHMX | R9: illuminated 240-frame sequence with AF state “focused”; R10: 24 RGB frames, 3000×2256, FD650 | Optical focus quality, color, video, rotation; sensor driver exposes 3008×2256 RAW, **not 108 MP** |
| Ultrawide — OV13B10 | R10: 24 RGB frames, 4200×3120, FD650 | Image quality and video; crop/delay driver warnings remain |
| Front — S5K3T2 | R9: 640×480 captured | A high-resolution R10 attempt timed out; investigate stride/configuration |
| Macro — S5K5E9 | R9: 640×480 captured | Optical focus, quality and useful working distance |
| Camera app | Native Wayland preview observed in omacam | Capture/video UX across all lenses and orientations |
| Torch | R9: normal-user one-second brightness 0 → 255 → 0 | Physical light not separately confirmed |
| Modem / EFS | Modem discovered; EFS normal stop/restart succeeds after fix | Actual EFS transfer and cellular stability |
| Phone permissions | R11: active UID voice/messaging checks pass; read-only call list succeeds; no startup authentication job | Real calls/SMS/data/audio **untested, no SIM** |
| Privileged administration | R11: service control and firmware still require `auth_admin` | First definitive PIN and complete permanent security profile |
| Wi-Fi | Device present; disconnected in recorded R11 samples | Connect, transfer, reconnect and suspend/resume |
| Bluetooth | Service active | Pairing, audio and reconnection |
| Accelerometer / light | Sensor proxy reports both available | Broader motion/light acceptance and app integration |
| Proximity | Sensor proxy reports unavailable | Driver / sensor-path investigation |
| NFC | `nfc0` registered; powered off at observation | Tag read/write and app behavior; no payment support claimed |
| Haptics / IR | No native haptic input or LIRC device in R11 | Driver/DT integration and physical validation |
| GPS / fingerprint | Unverified | Fix/reliability; enrollment, verification and unlock |
| Audio | Earlier-track results remain historical | Speaker, microphone, routing and call AEC in 4.5 |
| Power / alarms | USB-connected observation only | Real battery measurements, charge behavior, RTC alarms and suspend |
| Return / recovery | R10/R11 returned after graphical shutdown without a request for hardware buttons; original boot/DTBO readbacks matched | General reboot reliability and standalone recovery |
| Updates / Android apps | Earlier integration is archived; native 4.5 updater remains guarded/incomplete | Coherent upgrade/rollback and new-track Waydroid validation |

## How to read a result

**Captured** means a file/buffer was received. **Detected** means the interface appeared. **Permission passed** means the specified authorization check passed. These do not establish quality, connectivity, physical light, a GPS fix or successful voice calls.

R9 had a DMA allocation failure. R10 resolved that failure for the main camera by adding `cma=256M`, with the same kernel, DTB and initramfs. A separate high-resolution attempt selected the front camera because enumeration order changed; subsequent diagnostic captures use stable hardware IDs. Failures stay in the [lab record](validation-2026-11-01.md).

Current evidence: [R9 cameras/torch/EFS](evidence/2026-11-01-r9.json), [R10 DMA comparison](evidence/2026-11-01-r10.json), [R11 permissions/recovery](evidence/2026-11-01-r11.json). Raw diagnostics, camera images and per-device data remain private.

The [hardware investigation notes](hardware-investigation.md) keep newly identified Android paths and upstream driver candidates separate from native acceptance.

## Earlier track

The [2026-10-30 documentation](history/README-2026-10-30.md) records a different installation with permanent boot, PIN and Waydroid tests. It is retained for provenance and reusable engineering work. Those results have **not** been repeated wholesale in the new 4.5 environment and must not be added to this table as current acceptance.
