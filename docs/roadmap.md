# Roadmap

The goal is a complete, responsive native Omarchy phone. The latest [4.5 RC2 status](status.md) is RAM-only and does not meet that goal yet. The earlier installation remains a [historical reference](history/README-2026-10-30.md).

## 1. Reproducible, recoverable native installation

- Publish a complete builder with source pins, licenses and verified package provenance.
- Implement the Apollo-specific permanent storage/boot/recovery procedure and local first-PIN setup.
- Validate repeated unplugged boot, recovery and an update/rollback path that retains the device stack.
- Keep generic PC reset/installer/updater paths guarded until their Apollo equivalents are proven.

## 2. Finish the hardware acceptance

- **Cameras:** front high-resolution/stride failure, macro focus, rotation, video, optical focus and color. The current main driver has no 108 MP mode.
- **Phone/audio:** real calls, SMS, data and call AEC with a test SIM; media speaker/microphone and routing in the new base.
- **Connectivity:** actual Wi-Fi connection, both bands, reconnect/suspend and Bluetooth pairing/audio.
- **Sensors/NFC:** proximity, sensor integration and NFC tag operations. GPS needs a reliable fix; fingerprint needs enrollment/verification/unlock.
- **Haptics:** R12 confirmed a very soft AW8697 rumble. Test the strength range, application feedback and a complete boot with the newly packaged access rule.
- **IR:** R12 detected the LIRC interface and queried capabilities without transmitting. Optical emission, real carrier/duty behavior and remote-control use still need physical tests.

## 3. Make it comfortable all day

- Touch targets, navigation, app switching, toolkit keyboard behavior and accessible controls.
- Translation coverage and readable device/lens names.
- Safe screen-off/wake, suspend, alarms, charging, thermal and battery measurements on real storage.
- Performance profiles measured against latency and power, not guessed from service startup.

## 4. Revalidate optional Android compatibility

The earlier Waydroid/VANILLA, APK and GPU checks remain useful history. Repeat them on the new profile before announcing support for Android apps, Google services or Android access to camera/microphone.

## What moves an item to complete

A source change, a reproducible test, the precise tested configuration and a successful physical result. Record regressions and recovery. Keep live-device findings separate from fixtures and earlier releases. Publish only reviewed summaries, never raw calibration, firmware dumps or personal diagnostics.
