# Roadmap

1. Bring up a native Omarchy session with a recoverable fallback and clean compositor/shell diagnostics.
2. Make the portrait touch interface usable: readable scaling, reachable controls, application switching and a reliable on-screen keyboard.
3. Implement trusted touch PIN setup, rate-limited verification and session locking. Test incorrect PIN, crash, suspend and resume behavior before enabling automatic locking.
4. Extend the 31 passing Waydroid APK/lifecycle checks with physical file-manager activation, notifications, input, application navigation, sound/camera access and cold-boot persistence. Confirmed installation, stop/start, F-Droid persistence and GPU rendering have device evidence.
5. Extend the native four-camera stream and EGL lifecycle checks with physical GNOME Camera permission, preview, photo/video, orientation and optical focus acceptance. Repeat audio, Wi-Fi, Bluetooth, GPS and power checks from Omarchy. Track Android hardware support separately.
6. Continue unresolved fingerprint, cellular, external display and long-duration battery/thermal testing with the required accessories and SIM.
7. Implement and validate coherent Apollo system updates, rollback and matching replacement boot images; preserve the device-stack guard until that procedure is demonstrated.
8. Publish a tested installation/recovery procedure and release artifacts only after repeatable cold-boot validation.

“100% functional” is the target, not a claim about the current build. Hardware limits and failed tests stay visible.
