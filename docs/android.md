# Android applications without Google

Omarchy remains the native Linux desktop. Waydroid VANILLA supplies an optional ARM Android environment for APKs, without Google Play or Google services. Android starts on demand; it is not a required boot-time desktop service.

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

The installer currently accepts one regular APK file, up to 1 GiB. It does not implement split-APK bundles. Apps must support the Android image and ARM processor; apps requiring Google services need a separate compatibility decision. A successful F-Droid test does not establish compatibility with every APK.

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

## Still to validate

- Physical file-manager activation, progress/result notifications and Android touch navigation.
- Keyboard interaction, application switching and real app close/reopen from the phone screen.
- Android sound, microphones, cameras and other hardware APIs.
- Native Omarchy cold boot, Android storage-mount persistence and suspend/resume with Android.
- Long-duration battery, memory and thermal behavior.

The inherited native camera, Wi-Fi and other hardware results do not establish Android access to the same devices.
