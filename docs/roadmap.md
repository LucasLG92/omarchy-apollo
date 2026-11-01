# Roadmap

The goal is a complete, responsive native Omarchy phone. The latest [4.5 RC2 status](status.md) is RAM-only and does not meet that goal yet. The earlier installation remains a [historical reference](history/README-2026-10-30.md).

## 1. Reproducible, recoverable native installation

- Publish a complete builder with source pins, licenses and verified package provenance.
- Implement the Apollo-specific permanent storage/boot/recovery procedure and local first-PIN setup.
- Validate repeated unplugged boot, recovery and an update/rollback path that retains the device stack.
- Resolve the R17 recovery failure: it required hardware buttons/full bootloader after a limited-fastboot download rejection. Earlier automatic returns do not establish reliability.
- Keep generic PC reset/installer/updater paths guarded until their Apollo equivalents are proven.
- Integrate the [original V2 Plymouth/SDDM sources](../experiments/original-boot-v2/README.md) with a complete desktop. R16 tested the splash in minimal RAM rescue and ARM64 test mode only loaded the greeter; physical login, first local credential, PAM acceptance and recovery remain to be validated before selecting it permanently.

## 2. Finish the hardware acceptance

- **Cameras:** front high-resolution/stride failure, macro focus, rotation, video, optical focus and color. The current main driver has no 108 MP mode.
- **Phone/audio:** R17 detected a PIN-locked SIM. Verify local-dialog completion, unlock, network registration and physical/logical slot mapping before real calls/SMS/data and call AEC; complete local account/Polkit setup without changing SIM-PIN protection. Media speaker/microphone and routing remain open in the new base.
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

## 4. Revalidate optional Android compatibility

The earlier Waydroid/VANILLA, APK and GPU checks remain useful history. Repeat them on the new profile before announcing support for Android apps, Google services or Android access to camera/microphone.

## What moves an item to complete

A source change, a reproducible test, the precise tested configuration and a successful physical result. Record regressions and recovery. Keep live-device findings separate from fixtures and earlier releases. Publish only reviewed summaries, never raw calibration, firmware dumps or personal diagnostics.
