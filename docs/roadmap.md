# Roadmap

The goal is a complete, responsive native Omarchy phone. The latest [4.5 RC2 status](status.md) has a completed native installation with repeated normal boot and local login on the Pro development unit. **A recurrent black desktop center after cold-boot login is open**, despite restart recovery. Complete phone acceptance, a public installer and maintenance/recovery coverage remain unfinished. The earlier installation remains a [historical reference](history/README-2026-10-30.md).

## 1. Reproducible, recoverable native installation

- Publish a complete builder with source pins, licenses and verified package provenance.
- R20 completed the unit’s native boot/storage installation and Android cleanup, with repeated normal boot and human login. Extend power-cycle/recovery coverage and make the procedure reproducible without distributing per-device artifacts.
- Validate repeated unplugged boot, recovery and an update/rollback path that retains the device stack.
- Resolve recovery variability: R17 required buttons/full bootloader; R18/R19 returned automatically with original readbacks verified. Repeat and diagnose before claiming general automatic-return reliability.
- Keep generic PC reset/installer/updater paths guarded until their Apollo equivalents are proven.
- R20 actual local login passed after normal boot, with original theme/autologin checks. Confirm the latest logo/animation visually: visual6 failed and the user missed boot7’s logo. The [owner form r5](../experiments/owner-setup/README.md) still needs separate human auto-close acceptance; Polkit authentication remains pending.

## 2. Finish the hardware acceptance

- **Variant coverage:** validate the regular Mi 10T 5G separately, including its main camera, memory/storage profile and per-unit calibration. Pro evidence does not establish non-Pro compatibility; follow the [model matrix](compatibility.md).
- **Cameras:** front high-resolution/stride failure, macro focus, rotation, video, optical focus and color. The current main driver has no 108 MP mode.
- **Phone/audio:** R19 verified one manual outgoing voicemail call and audible downlink. Validate microphone/uplink, incoming calls, SMS, AEC, VoLTE path and broader routing. R20 automatic profile r2 created a fresh profile after normal boot and passed cellular IPv4 HTTPS with Wi-Fi off on one network; latest local PIN entry in SIM UI 0.2.1 passed, connected/home and a cellular-bound IPv4 HTTPS204 result passed with Wi-Fi connected/preferred. Validate other SIMs/networks, IPv6, reconnection, sustained transfer and broader UI/error/retry coverage separately. The public 0.1.3 source remains historical, and no new source is included. Resolve physical/logical slot mapping without treating slot-entry count as card count; validate Polkit use of the local R20 credential without changing SIM protection or general modem authorization policy.
- **Connectivity:** R13 connected Wi-Fi and completed a Wi-Fi-bound HTTPS request. Test both bands, sustained transfer, reconnect/suspend and Bluetooth pairing/audio.
- **Sensors/NFC:** R13 fixed one missing scratch-file creation failure and retained accelerometer/light availability. Test longer operation, sensor integration, proximity and NFC tags. GPS needs a reliable fix; fingerprint needs enrollment/verification/unlock.
- **Haptics:** R12 confirmed a very soft AW8697 rumble; R13 booted runtime v6 with local access and feedbackd discovery without manual restart. Test strength, application feedback and repeated boots.
- **IR:** R12 detected the LIRC interface and queried capabilities without transmitting. Optical emission, real carrier/duty behavior and remote-control use still need physical tests.

## 3. Make it comfortable all day

- **Resolve the recurrent black desktop center after cold-boot login.** Shell .8/official Quickshell restart recovered Home, but root cause and a definitive startup fix remain unverified.
- Installed gesture/keyboard r2 passed basic human HOME/recents/keyboard-closing acceptance. Refine thresholds, broader behavior/accessibility, and return Home after the final recent app closes. Offline checks and restart recovery do not close the startup issue.
- Translation coverage and readable device/lens names.
- Safe screen-off/wake, suspend, alarms, charging, thermal and battery measurements on real storage.
- Implement and test a separate touch-based encrypted-storage unlock path if LUKS is used; the SDDM keyboard does not provide it.
- Performance profiles measured against latency and power, not guessed from service startup.
- Keep LTE/NR5G registration and the R19 call result separate from throughput claims; later R20 cellular IPv4 HTTPS is one connectivity result, with no speed measurement.

## 4. Revalidate optional Android compatibility

The earlier Waydroid/VANILLA, APK and GPU checks remain useful history. Repeat them on the new profile before announcing support for Android apps, Google services or Android access to camera/microphone.

## What moves an item to complete

A source change, a reproducible test, the precise tested configuration and a successful physical result. Record regressions and recovery. Keep live-device findings separate from fixtures and earlier releases. Publish only reviewed summaries, never raw calibration, firmware dumps or personal diagnostics.
