# Android applications, with or without Google

> **Historical track — 2026-10-30.** This page describes the earlier integration, not current acceptance for the 4.5 RC2 RAM rebase. See [current status](status.md) and [the rebase record](rebase-4.5.md).


Omarchy remains the native Linux desktop. An optional ARM Waydroid environment supplies Android applications. A new installation can choose **Android without Google (VANILLA)** or **Android with Google Play and Google services (GAPPS)**. Without Google is the default. Android starts on demand; it is not a required boot-time desktop service.

## Choose during a fresh Android installation

The installation entry point is **Instalar aplicaciones Android** in the launcher, or `omarchy-apollo-install-android` from the local desktop. It opens a touch-friendly choice and asks for administrator authorization before initializing the selected image. Cancellation does not initialize Android. The underlying installer also accepts `--flavor vanilla` or `--flavor gapps`.

Both image types are supported by [Waydroid's initialization interface](https://docs.waydro.id/usage/waydroid-command-line-options). Google sign-in happens afterwards, inside Android. The installer does not request a Google account or password. GAPPS can require the owner's [Google Play certification step](https://docs.waydro.id/faq/google-play-certification); compatibility with apps that check device integrity must be evaluated separately.

The choice applies before Android is initialized. The helper refuses an existing configuration, including a dangling configuration symlink. It has no force or reset option and does not convert an existing VANILLA installation to GAPPS. Existing applications and data are preserved when that refusal occurs.

The current owner's selected image remains VANILLA. Revision 10 is installed in the clean image. Its real privileged initializer passed [27 isolated boundary checks](evidence/android-install-profiles-2026-10-30.json), including both selections, the default, reinitialization refusal, diagnostic-file protection and permissions required by an ordinary desktop session. Those checks replace only the Waydroid download/init command with a fixture. They establish argument selection and safeguards, **not a complete GAPPS installation or successful Google Play use**. The choice screen and complete download flow still require acceptance testing.

Fresh VANILLA Android completed its first real boot on the clean Omarchy base in approximately 45 seconds. The same installation then passed [31 APK/lifecycle checks](evidence/android-clean-lifecycle-2026-10-30.json), including F-Droid persistence and FD650 rendering after restart. This repeats the older base's result below using fresh Android data and installed revision 10. The checks use a separate headless display and do not establish physical touch or file-manager acceptance.

The current integration confirms APK installation with Android's package manager. It also releases the privileged install helper before Android stops, fixing an observed restart failure caused by retained container mounts. The published device test passes 31 checks, including application persistence and FD650 rendering after restart. Physical interaction and cold-boot acceptance are still pending.

## Use from the desktop

Open **Android** from the application launcher. From a terminal in the same graphical session, without sudo:

```sh
omarchy-apollo-android start
omarchy-apollo-android install /path/to/application.apk
omarchy-apollo-android status
omarchy-apollo-android stop
```

`prepare` starts Android without opening its full interface. `stop` stops the session and container; repeating it is harmless in the tested lifecycle. This does not imply that Waydroid's small D-Bus-activated manager has also exited.

The APK file association is already registered on the test phone. To select it explicitly for another desktop account, run:

```sh
omarchy-setup-apollo-android
```

The launcher requests a progress notification and a confirmed result. Opening an APK from the physical file manager and receiving those notifications have not yet been acceptance-tested on the phone's screen.

The APK installer currently accepts one regular APK file, up to 1 GiB. It does not implement split-APK bundles. Apps must support the selected Android image and ARM processor. Apps requiring Google services generally need the GAPPS selection; a successful F-Droid test does not establish compatibility with every APK.

## Installation and lifecycle boundary

The desktop client runs as the local user and checks that its Wayland socket belongs to that user. It serializes Android startup, waits for boot completion with a deadline and refuses to take over another user's or display's active Android session.

The system D-Bus helper exposes only APK installation and release. It checks the caller against the active Waydroid session and receives an already-readable regular file descriptor, rather than opening a caller-supplied host path as root. It copies the input to an unlinked, root-private snapshot and invokes a fixed Android package-manager command as Android shell UID/GID 2000. There is no arbitrary host-command argument. Installation succeeds only when Android exits successfully and reports success; raw Android output and APK paths are not returned in the public result.

The helper has bounded package-manager output and execution time, a private temporary directory and a read-only host filesystem apart from its cache and the LXC lock directory. It exits explicitly after installation, with an idle timeout as fallback. The client waits for its process to exit before stopping or restarting Android. Keeping that helper's private mount namespace alive caused a real restart failure during development; the completed lifecycle test exercises the fix with the service protections retained.

This is a narrowly scoped integration helper, not a claim that privileged Waydroid provides the isolation of a virtual machine. Native Linux and Android application hardware support remain separate validation targets.

## Reproduce the device checks

The test runs on a provisioned Apollo installation with Android stopped, an active local desktop account and the optional `weston` test package. It creates a separate headless Wayland display; it does not use or capture the physical phone display or enter an owner credential. It installs the documented F-Droid fixture into the existing test Android environment, so it is intended for a development phone.

First verify the downloaded F-Droid APK's detached signature using the [official verification instructions](https://f-droid.org/docs/Verifying_Downloaded_APK/). This run used F-Droid 2.0.2 and the documented primary-key fingerprint `37D2C98789D8311948394E3E41E7044E1DBA2E89`. The exact fixture SHA-256 is:

```text
19d51fad482239f6df6a99120e34513667e9a86d136dafdc4a211a68c3327b52
```

Then run from the source checkout:

```sh
sudo python -I tests/check_android_lifecycle.py --apk /path/to/verified/F-Droid-2.0.2.apk
```

The runner verifies that exact digest before using the fixture. Its 31 checks cover confirmed installation, malformed-input rejection, descriptor validation, denial of root and other-UID calls, helper exit, stop/start, app persistence, GPU rendering and cleanup. Temporary fixtures and its test compositor are removed. Android is stopped after the successful test; the installed F-Droid app remains. Only sanitized JSON is printed on success.

The [device evidence](evidence/android-apk-lifecycle-2026-10-30.json) records all check names, package checksums and limits. The suite ran against `omarchy-apollo-android 0.1.0-5`; installed revision `0.1.0-6` adds the explicit, already-satisfied `xdg-utils` dependency. All eight installer/client/service files were compared byte for byte against both packages and the installed files. Package-file and database checks pass for revision 6.

The developer-test controller now creates its phase acknowledgements exclusively and changes ownership through the opened descriptor. This prevents a preplaced symlink in the test user's directory from redirecting the root ownership operation. The [six boundary checks](evidence/test-phase-ack-2026-10-30.json) reproduce the old operation against a synthetic canary in an inaccessible fixture, verify the actual replacement helper and check permissions with the real desktop UID. Run `sudo python -I tests/check_phase_ack.py` on the development phone to reproduce them. This change is confined to the test controller; it does not change the installed APK service or imply that the 31-check lifecycle suite was rerun against the revised controller.

## Android audio transport

The Android framework can send stereo PCM audio through its normal audio service and PulseAudio HAL into Linux. The device test generated three seconds at 48 kHz using the real `AudioTrack` class, with a different tone in each channel. Both tones arrived in the correct channels of an isolated PipeWire sink. Android reported all 144,000 frames played.

This was a silent transport test. The temporary audio server had no ALSA, Bluetooth or camera devices; Android had no `/dev/snd`. Only the synthetic sink's monitor was sampled, in memory. No room microphone was captured and no physical sound was played. The real desktop audio services, default output and local PIN-setup process were preserved. The [sanitized result](evidence/android-audio-transport-2026-10-30.json) records the actual measurements and source digests. It does not establish speaker audibility, microphone operation, latency or compatibility with every APK.

Build the fixture on a computer with JDK 17 or newer:

```sh
python3 tests/build_android_audio_probe.py --output audio-probe.jar
```

The builder checks a pinned SHA-256 for D8 from Google's official Maven repository. It packages only the probe DEX, with no Android framework stubs. The runtime uses Android's real boot framework. See the upstream [D8 build instructions](https://r8.googlesource.com/r8/+/refs/heads/main/README.md) and [AudioTrack API](https://developer.android.com/reference/android/media/AudioTrack).

Copy the fixture to the development phone and run with Android stopped:

```sh
sudo python -I tests/check_android_audio.py --probe-jar /path/to/audio-probe.jar
```

The optional Weston test tool and the installed native audio stack are required. The test starts a separate headless display and policy-only audio server, briefly boots the existing Android environment, runs the probe as Android shell UID 2000, checks the synthetic monitor and stops Android. Temporary fixture files, its test compositor and audio processes are removed. It does not use the physical phone display or the owner's credentials. This is a development check for the provisioned Apollo image.

## Still to validate

- Physical file-manager activation, progress/result notifications and Android touch navigation.
- Keyboard interaction, application switching and real app close/reopen from the phone screen.
- Audible Android sound through physical outputs, microphones, cameras and other hardware APIs.
- Native Omarchy cold boot, Android storage-mount persistence and suspend/resume with Android.
- Long-duration battery, memory and thermal behavior.

The inherited native camera, Wi-Fi and other hardware results do not establish Android access to the same devices.
