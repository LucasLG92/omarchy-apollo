# Roadmap

The goal is a complete, responsive native Omarchy phone. The latest [4.5 RC2 status](status.md) is RAM-only and does not meet that goal yet. The earlier installation remains a [historical reference](history/README-2026-10-30.md).

## 1. Reproducible, recoverable native installation

- Publish a complete builder with source pins, licenses and verified package provenance.
- Implement the Apollo-specific permanent storage/boot/recovery procedure and local first-PIN setup.
- Validate repeated unplugged boot, recovery and an update/rollback path that retains the device stack.
- Resolve recovery variability: R17 required buttons/full bootloader; R18/R19 returned automatically with original readbacks verified. Repeat and diagnose before claiming general automatic-return reliability.
- Keep generic PC reset/installer/updater paths guarded until their Apollo equivalents are proven.
- Integrate the [original V2 Plymouth/SDDM sources](../experiments/original-boot-v2/README.md) with a complete desktop. R16 tested the splash in minimal RAM rescue and ARM64 test mode only loaded the greeter; physical login, first local credential, PAM acceptance and recovery remain to be validated before selecting it permanently.

## 2. Finish the hardware acceptance

- **Variant coverage:** validate the regular Mi 10T 5G separately, including its main camera, memory/storage profile and per-unit calibration. Pro evidence does not establish non-Pro compatibility; follow the [model matrix](compatibility.md).
- **Cameras:** front high-resolution/stride failure, macro focus, rotation, video, optical focus and color. The current main driver has no 108 MP mode.
- **Phone/audio:** R19 verified one manual outgoing voicemail call and audible downlink. Validate microphone/uplink, incoming calls, SMS, IP data, AEC, VoLTE path and broader routing. The SIM UI 0.1.3 loaded physically, but notice origin/PIN2 meaning and human UI-fix acceptance remain pending. Resolve physical/logical slot mapping without treating slot-entry count as card count; complete local account/Polkit setup without changing SIM protection or general authorization policy.
- **Connectivity:** R13 connected Wi-Fi and completed a Wi-Fi-bound HTTPS request. Test both bands, sustained transfer, reconnect/suspend and Bluetooth pairing/audio.
- **Sensors/NFC:** R13 fixed one missing scratch-file creation failure and retained accelerometer/light availability. Test longer operation, sensor integration, proximity and NFC tags. GPS needs a reliable fix; fingerprint needs enrollment/verification/unlock.
- **Haptics:** R12 confirmed a very soft AW8697 rumble; R13 booted runtime v6 with local access and feedbackd discovery without manual restart. Test strength, application feedback and repeated boots.
- **IR:** R12 detected the LIRC interface and queried capabilities without transmitting. Optical emission, real carrier/duty behavior and remote-control use still need physical tests.

## 3. Make it comfortable all day

- Touch targets, navigation, app switching, toolkit keyboard behavior and accessible controls.
- Translation coverage and readable device/lens names.
- Safe screen-off/wake, suspend, alarms, charging, thermal and battery measurements on real storage.
- Implement and test a separate touch-based encrypted-storage unlock path if LUKS is used; the SDDM keyboard does not provide it.
- Performance profiles measured against latency and power, not guessed from service startup.
- Keep LTE/NR5G registration and the R19 call result separate from throughput claims; no cellular-IP or speed measurement is published.

## 4. Revalidate optional Android compatibility

The earlier Waydroid/VANILLA, APK and GPU checks remain useful history. Repeat them on the new profile before announcing support for Android apps, Google services or Android access to camera/microphone.

## What moves an item to complete

A source change, a reproducible test, the precise tested configuration and a successful physical result. Record regressions and recovery. Keep live-device findings separate from fixtures and earlier releases. Publish only reviewed summaries, never raw calibration, firmware dumps or personal diagnostics.
