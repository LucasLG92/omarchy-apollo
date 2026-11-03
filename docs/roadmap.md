# Roadmap

The goal is a dependable native Omarchy phone. The current development unit runs
**Linux 7.3.1 R14** with a normally booted internal root, an accelerated desktop
and the latest mobile rendering fixes. [Current evidence](milestone-2026-11-03.md)
and [hardware status](status.md) separate working observations from unfinished work.

## Completed milestones, with their tested scope

- Native internal-root installation and ordinary owner login on one Mi 10T Pro.
- Linux 7.3.1 Apollo port, 502 modules, ThinLTO, USB-C/PD charge-policy checks,
  MGLRU/zram support and hardware CPU/GPU checks. No autonomy benchmark yet.
- Human-confirmed repaint correction made permanent, plus a GTK keyboard/workarea
  regression check after reloading the session.
- Frame-boundary rotation release: four measured transactions, bars fitted and
  wallpaper unchanged; sensor-inclusive and wider app timings remain separate.
- Recents burst-close restart reproduced, then a 15-window regression passed
  with the same shell process and no Home/wallpaper reloads.
- Earlier gesture, Phone/SIM continuation, one-network cellular IPv4,
  outgoing voicemail/downlink and optional Android-app milestones. These retain
  their dates and are not newly certified R14 call/hardware results.

## 1. Phone audio and essential reliability

- Resolve speakerphone distortion and the later reported call-time restart.
  Diagnose the actual route/cause before claiming AEC, microphone clipping or
  a particular component fault. Keep earpiece and speaker results separate.
- Revalidate calls and cellular data with a SIM on R14. Test microphone/uplink,
  incoming calls, SMS, reconnection, IPv6, other networks and the VoLTE path.
- Extend reboot/login/session coverage. Check the latest boot branding,
  shutdown-versus-reboot behavior and powered-off cable insertion physically.
- Verify the Omarchy charging-only animation on the real bootloader/cold-plug
  path; controller/theme integration is not completed physical acceptance.

## 2. Battery, thermal behavior and rotation polish

- Measure controlled unplugged idle and screen-on workloads: brightness,
  radio state, refresh rate, temperature and duration recorded without identifiers.
- Compare manual refresh rates and the auto90/144 policy, stock CPU policies,
  GPU runtime behavior, `menu` versus TEO and zram algorithms before selecting
  defaults based on numbers. No overclock or thermal-protection removal.
- Validate physical suspend/resume, power-key and radio wake sources. An active
  idle daemon alone does not prove successful suspend or reliable wake.
- Extend clean rotation tests to both directions, app switching, keyboard,
  natural dialogs, Android windows and repeated rapid changes. Measure sensor
  detection separately from the frame handoff and keep pixel/input pairing.
- Retain no-reload wallpaper behavior and avoid continuous idle repaint/polling.

## 3. Finish the hardware

- **Fingerprint:** establish the actual supported sensor/secure-world path,
  then enrollment, retry/error handling, verification and locked-session unlock.
  No current enrollment or fingerprint unlock is operational; never publish templates.
- **GPS/proximity:** obtain a real fix and a reliable proximity path, then
  integrate them into normal applications and call/display behavior.
- **Cameras:** revalidate R14 capture, color, optical focus, orientation and video.
  The existing main driver does not expose 108 MP.
- **Bluetooth/NFC/IR:** pairing/audio/reconnection, tag transactions and actual
  optical IR emission; interface detection is only a prerequisite.
- **Haptics:** improve useful strength and normal app feedback, with repeated-boot checks.
- **Variant coverage:** regular Mi 10T 5G needs its own main-camera, memory/storage
  and calibration validation. Pro results do not certify the non-Pro model.

## 4. Reproducible installation, updates and optional APKs

- Export the complete reviewable R14 build/provenance and package path without
  private boot/storage bindings, firmware, calibration or credentials.
- Validate clean-first-user creation, administrator policy and the first normal
  SDDM/logind session on a disposable clean target. Existing-owner success is
  not a clean-install wizard test.
- Finish public update/recovery/rollback instructions and repeated power-cycle
  tests. Retained private R12 fallback artifacts are not a generic download.
- Revalidate Waydroid/Android 13 and F-Droid on R14, then wider APK/ABI/API,
  gesture/keyboard/lifecycle and camera/microphone/GPS paths. Independent app
  windows still require the Android compatibility container; VANILLA includes
  no Google Play/GMS or Play Integrity/banking/DRM guarantee.
- Extend responsive layouts, natural dialog containment and mobile plugin
  compatibility. Installing a community plugin does not certify its phone UI.

## What closes an item

A reviewed source change, a precise configuration, a reproducible check and a
successful physical result for that feature. Keep failed trials and recovery
honestly dated. Publish selected evidence and reviewed screenshots, never raw
logs, device images, calibration, personal data or credentials.
