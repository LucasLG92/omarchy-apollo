# Hardware status

**Current track: Omarchy 4.5 RC2, native installation completed on one Mi 10T Pro development unit, with an open desktop-startup regression.** Native boot/internal root and local login are verified. **The latest cold-boot login reproduced a black desktop center while the bar/search pill remained visible.** The home screen recovered through an official Quickshell restart on installed shell .8; the recurring startup cause and definitive fix remain unresolved. [Latest result](evidence/2026-11-02-cold-boot-sim-desktop.json).

SIM UI 0.2.1 accepted the access PIN entered only on the phone. The modem reached connected/home with secondary PIN2 remaining; a cellular-bound IPv4 HTTPS request returned 204 while Wi-Fi was connected/preferred. Basic shell .8/r2 HOME/recents/keyboard closing passed human acceptance. **Complete daily-driver acceptance is not verified:** Polkit, broader phone/audio/hardware, IPv6, throughput, battery/suspend and a public installer remain open.

| Area | Evidence / latest result | Acceptance gap |
| --- | --- | --- |
| Native OS / root | R20: flashed native boot, internal ext4 root/systemd/hardware target and repeated normal boot verified, including after Android cleanup | Extended boot/recovery coverage, unplugged power tests and reproducible public installation |
| Display / touch | Recurrent black desktop center after latest cold-boot login; bar/search pill visible. Official shell restart restored Home; shell .8/r2 basic HOME/recents/keyboard closing human-accepted | **Recurring startup/rendering cause and final fix open**; full refinement, final-recent-app→Home, accessibility and sustained performance |
| Original Plymouth splash | R16 reviewed native KMS capture. Later visual6 failed human acceptance; boot7 retained graphics proof and booted the internal root | User did not observe the latest logo: physical logo/animation acceptance remains open |
| Original SDDM V2 | R20: original theme selected, autologin User empty, ordinary-user Wayland socket and human credential→desktop login verified after normal boot | Broader greeter/error/session coverage; no touch LUKS unlock |
| Main camera — S5KHMX | R9: illuminated 240-frame sequence with AF state “focused”; R10: 24 RGB frames, 3000×2256, FD650 | Optical focus quality, color, video, rotation; sensor driver exposes 3008×2256 RAW, **not 108 MP** |
| Ultrawide — OV13B10 | R10: 24 RGB frames, 4200×3120, FD650 | Image quality and video; crop/delay driver warnings remain |
| Front — S5K3T2 | R9: 640×480 captured | A high-resolution R10 attempt timed out; investigate stride/configuration |
| Macro — S5K5E9 | R9: 640×480 captured | Optical focus, quality and useful working distance |
| Camera app | Native Wayland preview observed in omacam | Capture/video UX across all lenses and orientations |
| Torch | R9: normal-user one-second brightness 0 → 255 → 0 | Physical light not separately confirmed |
| Modem / EFS | Modem discovered; EFS normal stop/restart succeeds after fix | Actual EFS transfer and cellular stability |
| SIM / registration | Latest cold boot: human local access PIN accepted; modem connected (state11)/home, primary PIN no longer required, secondary PIN2 enum3 remains | Slot mapping and wider stability; prior slot entries do not prove physical card count, and PIN2 is not a second SIM |
| SIM UI | Installed 0.2.1-1: compact masked-button keypad, human cold-boot access-PIN entry passed. Profile 20261101-6 launcher fix and earlier synthetic checks retain their scope | Broader retry/error/UX coverage; public source 0.1.3 remains historical, no new UI/launcher payload included |
| Voice / Messaging | R19: manual outgoing voicemail/downlink confirmed | Microphone/uplink, incoming calls and SMS unverified; newer SIM/data success does not establish them |
| Cellular IP data | Latest R20: fresh AUTO profile active; cellular-bound IPv4 HTTPS204 with Wi-Fi connected/preferred. Prior Wi-Fi-off tests retained | IPv6, other SIMs/networks, reconnect/sustained transfer and speed. Cellular need not be default while Wi-Fi is preferred |
| Phone permissions | R11: active UID voice/messaging checks passed and read-only call list succeeded | Broader ordinary-session authorization and administration; no SIM was available in that earlier trial |
| Privileged administration | R11: service control and firmware still require `auth_admin` | End-to-end Polkit authentication with the newly saved credential and complete permanent security profile |
| Local credential / owner UI | R20: setup layout accepted, credential saved; actual SDDM/PAM login and normal-boot desktop human-confirmed | Polkit authorization; r5 600 ms setup auto-close passed ARM64 synthetic checks but lacks separate human acceptance |
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
| Audio | R19: voicemail downlink heard by the user during the active outgoing call | Microphone/uplink, route coverage, call AEC and media audio; no audio file was recorded |
| Power / alarms | USB-connected observation only | Real battery measurements, charge behavior, RTC alarms and suspend |
| Storage / recovery | R20: userdata repurposed for native root; super/metadata/cache cleared, subsequent normal native boot passed; expected boot/recovery image-prefix readback matched | Extended native recovery/rollback and repeated power-cycle testing. Earlier Android-return results are historical, not a current fallback claim |
| Updates / Android apps | Earlier integration is archived; native 4.5 updater remains guarded/incomplete | Coherent upgrade/rollback and new-track Waydroid validation |

## Latest native installation record

[Latest SIM/desktop follow-up](evidence/2026-11-02-cold-boot-sim-desktop.json) supersedes boot7’s pending SIM and limited desktop state. [Boot7 and normal-boot evidence](evidence/2026-11-02-native-boot-v7.json) supersede the pending-installation state in the [initial R20 snapshot](evidence/2026-11-02-r20.json) and [earlier login-v6 record](evidence/2026-11-02-login-v6.json). The initial 16 GiB transfer passed full physical readback before first writable native boot; later boot/recovery checks verified the expected image prefixes, not claimed hashes of entire partitions. [Lab notes](validation-2026-11-02.md) · [transfer lesson](internal-root-transfer.md).

An earlier live-update black desktop recovered, and one later normal boot reached the desktop. **A subsequent cold-boot login reproduced the black center**, so the earlier success does not close the startup issue. Quickshell was alive and its Home model loaded while the bar/search pill rendered. Installed shell .8 passed normal GPG/ALPM/Qkk checks; an official Quickshell restart, without a Hyprland restart or active PIN forms, restored wallpaper, clock and eight icons according to the controller’s private review. The capture is not public. The cause and definitive startup fix remain open.

The user then accepted basic HOME, hold-for-recents and keyboard closing on installed gesture/keyboard r2. Further refinement and returning Home after closing the final recent app remain pending. These successful interactions do not validate startup rendering.

The [owner form r5](../experiments/owner-setup/README.md) saved the normal local account credential. Actual login was then verified, including after normal native boot, without reading the secret or verifier. Polkit and separate human auto-close acceptance remain pending. Visual6 showed white text and skipped the expected logo; boot7’s logo was missed by the user, so its visual acceptance remains unconfirmed. No boot-speed benchmark is claimed.

Automatic profile r2 worked on one network. After the latest cold-boot local SIM-PIN entry, it was active and a request bound to cellular returned IPv4 HTTPS204 with Wi-Fi connected/preferred. Primary access PIN was no longer required; secondary PIN2 (enum3) remained. A non-default cellular route under Wi-Fi preference is separate from that successful bound request. Earlier transition/restart observations remain in the lab record; no universal SIM/APN or throughput claim is made.

## How to read a result

**Captured** means a file/buffer was received. **Detected** means the interface appeared. **Permission passed** means the specified authorization check passed. These do not establish quality, connectivity, physical light, a GPS fix or successful voice calls.

R9 had a DMA allocation failure. R10 resolved that failure for the main camera by adding `cma=256M`, with the same kernel, DTB and initramfs. A separate high-resolution attempt selected the front camera because enumeration order changed; subsequent diagnostic captures use stable hardware IDs. Failures stay in the [lab record](validation-2026-11-01.md).

R12 used kernel `7.1.0-apollo-native-r6` with runtime `20261101-4` and a haptic rule added in RAM. R13 completed a new RAM boot of runtime **`20261101-6`**, including that rule and the sensor scratch-file fix. Feedbackd opened the haptic device without manual restart. This tests v6; it does not retroactively record a boot of the intermediate v5 package or establish permanent standalone boot.

Current evidence: [R9 cameras/torch/EFS](evidence/2026-11-01-r9.json), [R10 DMA comparison](evidence/2026-11-01-r10.json), [R11 permissions/recovery](evidence/2026-11-01-r11.json), [R12 haptics/IR/recovery](evidence/2026-11-01-r12.json), [R13 Wi-Fi/runtime/sensors](evidence/2026-11-01-r13.json). Raw diagnostics, camera images and per-device data remain private.

Earlier full-desktop RAM evidence: [R19 outgoing call/downlink](evidence/2026-11-01-r19.json). GNOME Calls was opened without a number/dial URI; the user dialed manually. The call probe queried only state, direction and state reason plus object listing; it did not read Number/Name or export subscriber/network identity. App 0.1.3 had a [verified native load](../experiments/sim-unlock/phone-load-r19.json), not full human UI acceptance. The [R18 PIN/registration record](evidence/2026-11-01-r18.json) and [R17 manual recovery](evidence/2026-11-01-r17.json) keep their original scope. No permanent installation was completed in R19.

Separate splash evidence: [R16 minimal RAM rescue](evidence/2026-11-01-r16.json) and [original V2 theme sources/reviews](../experiments/original-boot-v2/README.md). R16 had no complete desktop or private calibration. Its single Plymouth RSS sample was 18,304 KiB; no speed/boot-time comparison is available. There were zero XKB errors in the collected rescue log and diagnostic tracing was disabled. No local password/PIN, PAM/autologin or permanent theme selection changed. SDDM's touch keyboard does not implement Plymouth touch-based LUKS unlocking.

The [hardware investigation notes](hardware-investigation.md) keep newly identified Android paths and upstream driver candidates separate from native acceptance.

## Device-variant coverage

All physical results above are from the **Mi 10T Pro development unit**. The regular Mi 10T 5G shares a useful platform base, but has **no acceptance result from this project**. Its main camera, RAM/storage profile and own private calibration need separate validation. Current private artifacts are tied to the development unit and are not redistributable/direct-flash images. See the [compatibility matrix and FAQ](compatibility.md).

## Earlier track

The [2026-10-30 documentation](history/README-2026-10-30.md) records a different installation with permanent boot, PIN and Waydroid tests. It is retained for provenance and reusable engineering work. Those results have **not** been repeated wholesale in the new 4.5 environment and must not be added to this table as current acceptance.
