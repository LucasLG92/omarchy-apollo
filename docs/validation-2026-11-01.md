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

## What is public

The JSON files are manually reviewed summaries: versions, dimensions, counts, Boolean outcomes and limitations. They exclude device/radio identifiers, network names, credentials, calibration, partition images, raw logs and camera photographs. [The R11 home screenshot](../media/apollo-home-r11.png) contains only the generic desktop. No personal PIN was published.

## Repeatability boundary

The source pins and [component patches](../patches/rebase-4.5/README.md) support code review. A complete clean-room rebuild and stock-device installation procedure for the new image is **not public or validated yet**. The earlier tests and recipes are not a substitute. Future reports should name the sensor by stable hardware identity, distinguish detection from use, keep failures, verify recovery, and record what was deliberately not tested.
