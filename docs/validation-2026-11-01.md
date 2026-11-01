# Device lab notes — 2026-11-01

This is a sanitized account of supervised native ARM64 RAM trials on a Xiaomi Mi 10T Pro. It reports observations from the development device, not a published flashable image or independent reproduction. See the [current status](status.md) for acceptance gaps.

## R9 — cameras, torch and EFS

The four sensor-specific helpers and tuning were added to **libcamera 0.7.2 plus the existing Omarchy Mobile patches**, retaining its GPU/AF work. All four sensors delivered 640×480 frames. An illuminated main-camera sequence completed 240 frames, reported AF state focused and used FD650. This is not an optical sharpness or color-quality measurement.

The first native-size main RGB capture failed to allocate DMA buffers. The device had only 32 MiB of CMA. The current main-sensor driver offers 3008×2256 RAW; requesting 108 MP was adjusted to that supported mode.

The quick-settings backend was corrected to discover Apollo's `white:flash` LED as well as `white:torch`. Normal-user brightness control completed a one-second 0→255→0 cycle. Visible light was not separately confirmed. EFS stopped with success and restarted active while the modem remained present; a real EFS transfer was not observed.

The trial returned after hardware-button recovery. Its original boot/DTBO readbacks matched. The exact cause of the return problem was not established. [R9 result](evidence/2026-11-01-r9.json).

## R10 — change one memory reservation

The boot image retained the same kernel, DTB and initramfs and added the documented kernel argument **`cma=256M`**. The physical pool was 256 MiB; all 122 observed UFS disk/partition nodes remained read-only.

With stable camera IDs, the main sensor completed 24 RGB frames at **3000×2256** and the ultrawide completed 24 at **4200×3120**, using FD650. The main allocation failure was resolved. Captured dimensions differ from RAW dimensions because the output format is aligned.

One initial attempt used camera index 4, which now referred to the front sensor, and returned no frames at the requested larger size. Numerical camera order is not stable across boots. The high-resolution front path remains unresolved; it is not counted as a main-camera failure or a passing front test.

Stopping the graphical session separately completed in about 1.8 seconds. The subsequent supervised return restored DTBO and requested Android reboot about 20.5 seconds after the finish request, without asking for the buttons. This does not isolate the cause of earlier return failures or prove standalone reboot reliability. Android completed and both original readbacks matched. [R10 result](evidence/2026-11-01-r10.json).

## R11 — phone permissions without the startup prompt

GNOME Calls starts in the background. The stock desktop ModemManager policy challenged ordinary phone actions, leaving a PIN prompt in this temporary locked-account profile. The phone-session policy was generated with ModemManager's **upstream `polkit=permissive` option**. Polkit stays enabled. Eight ordinary actions are allowed for the active local session; daemon administration and firmware retain `auth_admin`, and inactive/nonlocal defaults remain denied. The tested ModemManager executables were retained unchanged in a newly signed policy-only package.

On the device, the ordinary active user passed Voice and Messaging checks. Control and Firmware checks returned an authentication requirement. The read-only call list returned successfully with no calls; **no call was placed and no message was sent**. GNOME Calls was running, there were no pending authorization jobs or failed system units, and the actual home screen had no startup PIN dialog.

The test harness initially expanded `$$` before it reached the inner shell and supplied an invalid process argument. Disabling that extra expansion fixed the diagnostic; the recorded permission results are from the corrected repeat. This was a test-harness error, not a failed phone-policy result.

The NFC adapter was registered but off; sensor proxy reported accelerometer/light and no proximity. Wi-Fi remained disconnected in captured samples, and Bluetooth service startup did not establish pairing. The supervised session ended, graphics stopped, Android returned and original boot/DTBO readbacks matched. [R11 result](evidence/2026-11-01-r11.json).

## R12 — physical rumble and infrared detection

Kernel **`7.1.0-apollo-native-r6`** added the AW8697 v3 review driver and a separate Apollo input DTS, plus the SPI IR inactive-tail change. The original 760-line haptics driver and its authorship are retained in the [public source patch](../patches/rebase-4.5/README.md). This is a backport of a review submission, not a claim of upstream merger or a complete installation recipe.

The AW8697 input interface accepted **FF_RUMBLE start, stop and removal** for a **120 ms** effect at **8192/65535 magnitude** (approximately 12.5%). The user confirmed a **very low-strength physical vibration**. Active local access was verified through `uaccess`, without making the device world-writable. The service initially missed the device after the rule change; after restarting feedbackd, it opened the input device and the button-event check no longer reported missing feedback. This does not establish the strength range or broad application integration.

R12 booted runtime **`20261101-4`** and added that access rule during the RAM session. At that point a prepared **`20261101-5`** runtime included the rule but had not completed a boot test. R13 below later tests a complete RAM boot of v6, including that rule; the intermediate v5 package is not retroactively counted as tested.

The `ir-spi` LIRC device appeared and **`GET_FEATURES` returned `0x302`**, advertising pulse, carrier and duty-cycle capabilities. **No IR transmission was requested.** Optical emission and remote-control behavior remain unverified. The source-provenance record also describes an offline ARM64/QEMU tail-sample fixture; that was not a hardware transmission test.

The portrait display was 1080×2400, CMA was 256 MiB, all 122 observed UFS nodes were read-only, and the system and user checks found no failed units. Graphics stopped and the supervised return reached Android without a request for buttons; original boot/DTBO readbacks matched. No userdata formatting or permanent installation occurred. [R12 result](evidence/2026-11-01-r12.json).

## R13 — WiFi, runtime v6 and sensor scratch files

R13 completed a new RAM boot with kernel `7.1.0-apollo-native-r6` and runtime **`20261101-6`**. The user connected Wi-Fi from the phone screen. Connection state was checked, then an HTTPS request explicitly bound to the Wi-Fi interface returned **200** from `https://omarchy.org/`. SSID, addresses and password are excluded. This establishes that connection and request, not both-band coverage, sustained transfer or suspend/reconnect reliability.

The earlier HexagonRPC path allowed a sensor scratch file to be written, but a missing file failed the virtual read-only open before the first write could create it. The [R13 patch](../patches/rebase-4.5/README.md) creates it in the already restricted writable mapping with mode **0600**, without following a symlink or prematurely truncating existing data. It applies after the pinned Apollo sensor patch. The original file's Sensor Shell Contributors notice and **GPL-3.0-or-later** terms are retained; the recipe's different package-level license label is not used to relicense it.

An actual ARM64 RPC/VFS harness with synthetic data reproduced the baseline failure. The candidate passed **26 checks**, including creation/write, append, truncation and reading, plus rejection of outside mappings, read-only missing files and symlinks. This fixture is distinct from the phone observation. On the phone, the service generated the private scratch file in RAM. No matching missing-scratch errors appeared in the collected boot log or a **20.97-second observation**. The daemon remained the same process with no restarts during the check. Accelerometer/light remained available; proximity did not. **20.97 seconds is an observation interval, not boot time or a general speed improvement.** No before/after performance comparison is available.

Runtime v6 included the earlier haptic access rule from the start. The active local user had read/write access, feedbackd opened the device **without manual restart**, and the button-event check had no missing-feedback warning. The only confirmed physical strength remains R12's very soft pulse; it was not increased or remeasured here. This records a v6 RAM boot, not a retroactive test of the intermediate v5 package or standalone permanent boot.

CMA remained 256 MiB, all 122 observed UFS nodes were read-only, and there were no failed system units at the check. Graphics stopped, Android returned without a request for buttons, and original boot/DTBO readbacks matched. No userdata formatting, call or SMS occurred. [R13 result](evidence/2026-11-01-r13.json).

## R16 — original Plymouth in minimal RAM rescue

This was a **splash-only native RAM rescue trial**, with kernel `7.1.0-apollo-native-r6`, not another full-desktop trial. At that point the latest desktop record was R13; R17 below later records another desktop trial. R16 did not stage private calibration, configure a password/PIN, change PAM/autologin or select a permanent phone theme.

The V2 theme keeps the official Omarchy 4.5 RC2 PNG assets and `#1a1b26` background from commit `5978d93ae7da0a325b7493501911e3f1266cadd3`. Plymouth's native daemon, DRM device and active VT were verified. A **real 1080×2400 KMS framebuffer capture** was taken and reviewed: only the wordmark and background, a standard sRGB color tag, no text/EXIF metadata or device identifiers. The image is not the HTML preview. A separate human confirmation of the final R16 screen was not obtained.

Complete XKB data was present, there were **zero XKB errors in the collected rescue log**, and diagnostic tracing was disabled. One daemon RSS sample was **18,304 KiB**. No performance or boot-time comparison is available, and the inherited animation is not a measured boot percentage.

Separately, V2 had 17 Windows Qt checks, 6 offline-browser checks and a Plymouth 26.134.222 parser check. The initial 432×960 Qt render matched the upstream reference pixel for pixel. Real ARM64 Qt 6.12.0-3 / SDDM 0.21.0-7 loaded the theme in **test mode without authentication**. Package `apollo-mobile-boot 0.2.0-1` was prepared and verified through the normal GPG/ALPM path in the PC builder, with 35 integrity entries; active theme selection stayed unchanged. These checks do not establish phone PAM login, physical touch-greeter behavior or a complete Plymouth→desktop handoff.

The keyboard source submits through normal SDDM/PAM and has no fixed PIN or hardcoded credential. It does not require QtVirtualKeyboard and does not implement Plymouth touch-based LUKS unlocking. First local credential setup and actual phone authentication remain pending.

All 122 observed UFS nodes remained read-only. The rescue session returned automatically to Android without a request for buttons, and original boot/DTBO readbacks matched. No userdata formatting or permanent installation occurred. [R16 evidence](evidence/2026-11-01-r16.json) · [V2 source, previews and review scopes](../experiments/original-boot-v2/README.md).

## R17 — full desktop, PIN-locked SIM and manual recovery

Omarchy **`4.5.0rc2`** with kernel **`7.1.0-apollo-native-r6`** reached the full native RAM desktop again, with systemd as PID 1. ModemManager detected a SIM object and reported **SIM-PIN required**. A signed local PIN dialog was installed and launched in RAM, but user completion was **not confirmed**. SIM unlock, ordinary network registration and physical-to-logical slot mapping remain unverified. No calls, SMS or cellular data were tested; the agent sent no calls/messages and received no PIN.

This SIM-PIN path is separate from the Linux account/SDDM/PAM path. The experimental local account still has no configured password, administrative Polkit readiness remains pending, and phone PAM login is untested. The trial did not disable or change SIM-PIN protection. Only a sanitized result summary is published here; no SIM-development code or raw diagnostics are included.

**Recovery required the phone buttons.** A limited fastboot mode rejected a download before a partition write. After returning to the full bootloader, the original DTBO was restored. Android completed boot and the original boot/DTBO readbacks matched. No userdata formatting or permanent installation occurred. **Automatic Android return is not reliable.** Earlier successful returns in R13 or the smaller R16 rescue trial do not establish reliability for this desktop path.

Per-device calibration was used privately in RAM; calibration partitions were not written and no calibration contents, subscriber identifiers, operator/network data, PIN or raw logs are published. R13's Wi-Fi/sensor results and R16's actual splash capture retain their original scope. [R17 result](evidence/2026-11-01-r17.json).

## R18 — local access PIN accepted and network registered

The full native RAM desktop used Omarchy `4.5.0rc2`, kernel `7.1.0-apollo-native-r6` and **SIM UI 0.1.2-1**. The user entered the PIN only on the handset through the masked local numeric window; no entry screenshot was taken. The modem's ordinary access-PIN unlock was verified, followed by **home network registration**, reported LTE/NR5G access technologies and packet-service attachment. **Cellular IP Internet and actual 5G throughput were not tested.** No PIN2/PUK was entered or SIM protection changed.

The remaining lock enum represented PIN2, a different SIM restriction from the access PIN. UI 0.1.2 showed a confusing message for that state. The [0.1.3-1 candidate source](../experiments/sim-unlock/README.md) now distinguishes PIN2/PUK2. It was signed/installed through normal GPG/ALPM in the PC builder (12 integrity entries, zero altered) and passed real ARM64 GTK/GIO tests with a **synthetic modem and zero radio PIN attempts**. **0.1.3 was not phone-tested in R18.** The published source/hash and synthetic result are separate from the physical 0.1.2 result.

Voice and Messaging interfaces were present. An incoming-call check was requested, but there was no second phone available, so **no external call attempt was confirmed**. Two bounded 65-second observation windows saw zero call objects. This does not establish a failed call. Calls, call audio and SMS remain unverified; the agent placed no call or message. Physical/logical SIM slot mapping also remains unverified.

The Linux account remained locked, so the PIN UI ran as root only in supervised RAM. General modem authorization policy, local credentials and PAM were not changed. GUI/modem core dumps and debug traces were disabled for entry; late journal collection was skipped after sensitive input. No PIN, subscriber identifiers, numbers, operator, APN or credential capture is distributed.

This trial returned automatically without asking for buttons. Android completed boot and original boot/DTBO readbacks matched. R17's manual recovery remains a separate recorded result; general automatic-return reliability is **not proven**. No userdata formatting or permanent installation occurred. Phone PAM login and complete phone functionality remain pending. [R18 evidence](evidence/2026-11-01-r18.json).

## What is public

The JSON files are manually reviewed summaries: versions, dimensions, counts, Boolean outcomes and limitations. They exclude device/radio identifiers, network names, credentials, calibration, partition images, raw logs and camera photographs. [The R11 home screenshot](../media/apollo-home-r11.png) contains only the generic desktop. No personal PIN was published.

## Repeatability boundary

The source pins and [component patches](../patches/rebase-4.5/README.md) support code review. A complete clean-room rebuild and stock-device installation procedure for the new image is **not public or validated yet**. The earlier tests and recipes are not a substitute. Future reports should name the sensor by stable hardware identity, distinguish detection from use, keep failures, verify recovery, and record what was deliberately not tested.
