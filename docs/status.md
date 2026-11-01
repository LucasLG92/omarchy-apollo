# Hardware status

**Current track:** Omarchy 4.5 RC2 rebase. **R18 · 2026-11-01** verified local access-PIN unlock and home network registration, with LTE/NR5G flags reported. Calls, SMS, cellular IP Internet and throughput are unverified. R18 returned automatically; R17 needed buttons, so general recovery reliability is still unproven. Each row retains its actual trial; these are one-device observations, not independent certification.

The target is a complete, fast native Linux phone. That target is **not achieved**. The new track remains RAM-only; Android and original boot partitions were restored after the tests. No permanent 4.5 installation, complete public installer or working native updater is claimed.

| Area | Evidence / latest result | Acceptance gap |
| --- | --- | --- |
| Native OS | Omarchy `4.5.0rc2-1`; systemd PID 1; Hyprland/Quickshell on ARM64 | Permanent installation and repeated standalone boot |
| Display / touch | Internal portrait display and FD650 GPU; touch, app opening and keyboard exercised | App coverage, gesture polish, accessibility and sustained performance |
| Original Plymouth splash | R16: native DRM, active VT and reviewed 1080×2400 KMS capture in minimal RAM rescue | Handoff to a full desktop, repeated boots and separate user confirmation of the final R16 screen |
| Original SDDM V2 | Real ARM64 Qt 6.12.0-3 / SDDM 0.21.0-7 test-mode load; package 0.2.0-1 prepared/verified in PC builder | Phone PAM login, physical keyboard interaction and first local credential; active theme selection unchanged |
| Main camera — S5KHMX | R9: illuminated 240-frame sequence with AF state “focused”; R10: 24 RGB frames, 3000×2256, FD650 | Optical focus quality, color, video, rotation; sensor driver exposes 3008×2256 RAW, **not 108 MP** |
| Ultrawide — OV13B10 | R10: 24 RGB frames, 4200×3120, FD650 | Image quality and video; crop/delay driver warnings remain |
| Front — S5K3T2 | R9: 640×480 captured | A high-resolution R10 attempt timed out; investigate stride/configuration |
| Macro — S5K5E9 | R9: 640×480 captured | Optical focus, quality and useful working distance |
| Camera app | Native Wayland preview observed in omacam | Capture/video UX across all lenses and orientations |
| Torch | R9: normal-user one-second brightness 0 → 255 → 0 | Physical light not separately confirmed |
| Modem / EFS | Modem discovered; EFS normal stop/restart succeeds after fix | Actual EFS transfer and cellular stability |
| SIM / registration | R18: user entered access PIN on handset; unlock and home registration verified; LTE/NR5G and packet attachment reported | Physical/logical slot mapping, cellular IP Internet and throughput unverified |
| SIM UI | R18 used 0.1.2-1 as root in supervised RAM; its PIN2 message was confusing. 0.1.3-1 candidate corrects PIN2/PUK2 and passed synthetic ARM64 GTK checks | Candidate 0.1.3 is not phone-tested; ordinary-user authorization integration pending; no general policy relaxation |
| Voice / Messaging | R18: interfaces present; no confirmed external incoming-call attempt; bounded observations had zero call objects | Calls/audio/SMS unverified. Zero objects without a confirmed attempt do not establish failure |
| Phone permissions | R11: active UID voice/messaging checks pass; read-only call list succeeds; no startup authentication job | Real calls/SMS/data/audio **untested**; no SIM was available in R11 |
| Privileged administration | R11: service control and firmware still require `auth_admin` | First definitive PIN and complete permanent security profile |
| Local credential / administration | R18: Linux account remained locked; root SIM UI was temporary and no credential/PAM or modem authorization policy changed | First local credential, phone PAM login and administrative Polkit readiness |
| Wi-Fi | R13: user connected on screen; connection verified and an HTTPS request bound to Wi-Fi returned 200 from `omarchy.org` | Both bands, sustained transfer, reconnect and suspend/resume; no network identity or credentials exported |
| Bluetooth | Service active | Pairing, audio and reconnection |
| Accelerometer / light | R13: both available after sensor scratch-file fix | Broader motion/light acceptance, long-term behavior and app integration |
| Sensor scratch file | R13: created in RAM with mode 0600; zero matching missing-file errors in collected boot log and 20.97-second observation; daemon stayed the same process | Longer observation and broader regressions; no before/after performance comparison |
| Proximity | Sensor proxy reports unavailable | Driver / sensor-path investigation |
| NFC | `nfc0` registered; powered off at observation | Tag read/write and app behavior; no payment support claimed |
| Haptics — AW8697 | R12: 120 ms FF_RUMBLE at 8192/65535, very low-strength physical response; R13: active local access from runtime v6 RAM boot | Strength range and application feedback |
| Feedback service | R13: rule present from boot, feedbackd opened the device without manual restart; button-event missing-feedback warning absent | Wider event/application coverage and repeated boots |
| Infrared | R12: `ir-spi` LIRC device detected; `GET_FEATURES` reported `0x302` | No transmission occurred; optical emission, actual carrier/duty and remote control unverified |
| GPS / fingerprint | Unverified | Fix/reliability; enrollment, verification and unlock |
| Audio | Earlier-track results remain historical | Speaker, microphone, routing and call AEC in 4.5 |
| Power / alarms | USB-connected observation only | Real battery measurements, charge behavior, RTC alarms and suspend |
| Return / recovery | R18 returned automatically without requesting buttons, with Android/original boot+DTBO readbacks verified. R17 required buttons/full bootloader | **General automatic-return reliability unproven**; repeat and diagnose before permanent or unattended boot |
| Updates / Android apps | Earlier integration is archived; native 4.5 updater remains guarded/incomplete | Coherent upgrade/rollback and new-track Waydroid validation |

## How to read a result

**Captured** means a file/buffer was received. **Detected** means the interface appeared. **Permission passed** means the specified authorization check passed. These do not establish quality, connectivity, physical light, a GPS fix or successful voice calls.

R9 had a DMA allocation failure. R10 resolved that failure for the main camera by adding `cma=256M`, with the same kernel, DTB and initramfs. A separate high-resolution attempt selected the front camera because enumeration order changed; subsequent diagnostic captures use stable hardware IDs. Failures stay in the [lab record](validation-2026-11-01.md).

R12 used kernel `7.1.0-apollo-native-r6` with runtime `20261101-4` and a haptic rule added in RAM. R13 completed a new RAM boot of runtime **`20261101-6`**, including that rule and the sensor scratch-file fix. Feedbackd opened the haptic device without manual restart. This tests v6; it does not retroactively record a boot of the intermediate v5 package or establish permanent standalone boot.

Current evidence: [R9 cameras/torch/EFS](evidence/2026-11-01-r9.json), [R10 DMA comparison](evidence/2026-11-01-r10.json), [R11 permissions/recovery](evidence/2026-11-01-r11.json), [R12 haptics/IR/recovery](evidence/2026-11-01-r12.json), [R13 Wi-Fi/runtime/sensors](evidence/2026-11-01-r13.json). Raw diagnostics, camera images and per-device data remain private.

Latest desktop evidence: [R18 PIN/registration/recovery](evidence/2026-11-01-r18.json). The phone used app 0.1.2-1; the published [0.1.3 candidate source/review](../experiments/sim-unlock/README.md) is a later PC/synthetic-tested correction, not a phone-tested replacement. No PIN, number, operator or subscriber identifier is published. The agent placed no call or message. The [R17 record](evidence/2026-11-01-r17.json) retains its manual recovery result; R18's successful return does not erase it.

Separate splash evidence: [R16 minimal RAM rescue](evidence/2026-11-01-r16.json) and [original V2 theme sources/reviews](../experiments/original-boot-v2/README.md). R16 had no complete desktop or private calibration. Its single Plymouth RSS sample was 18,304 KiB; no speed/boot-time comparison is available. There were zero XKB errors in the collected rescue log and diagnostic tracing was disabled. No local password/PIN, PAM/autologin or permanent theme selection changed. SDDM's touch keyboard does not implement Plymouth touch-based LUKS unlocking.

The [hardware investigation notes](hardware-investigation.md) keep newly identified Android paths and upstream driver candidates separate from native acceptance.

## Earlier track

The [2026-10-30 documentation](history/README-2026-10-30.md) records a different installation with permanent boot, PIN and Waydroid tests. It is retained for provenance and reusable engineering work. Those results have **not** been repeated wholesale in the new 4.5 environment and must not be added to this table as current acceptance.
