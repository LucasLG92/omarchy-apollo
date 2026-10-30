# Quickshell for Apollo

This recipe follows the Omarchy Quickshell package and pins upstream commit `9b0f339b19057f4731bf3b48293307d7ef241671`. Quickshell retains its LGPL-3.0-only license. The package recipe, Qt compatibility patch and package hook originate in [Omarchy packages](https://github.com/omacom/omarchy-pkgs/tree/main/pkgbuilds/quickshell). Apollo's focused changes are listed below.

## Idle notification lifetime

Changing both the enabled state and timeout can replace a Wayland idle notification at the same memory address. Previously `bNotification` retained that address while the old object was deleted. `QProperty` could then consider the replacement unchanged, leaving `isIdle` dependent on the deleted object's property. The compositor reported idle, but the shell never received the transition and did not lock.

`0001-detach-idle-notification-before-replacement.patch` publishes a null notification before deleting the old object. Dependent bindings detach while the old object is still valid, then attach to the new notification even if its address is reused. Idle inhibitors remain respected. Authentication and the compositor protocol are unchanged.

The real-device reproduction dynamically loads the installed Omarchy idle service with an isolated home and changes its timeouts from disabled to five seconds. Its lock/wake actions are replaced with harmless completion commands in the fixture. The installed original receives the compositor event but reports `idle: false`; the corrected production binary reports `idle: true` and completes the fixture lock action. This establishes the notification fix, separately from the subsequent live lock and physical PIN checks.

## Window test timing

`0002-test-wait-for-popup-polish.patch` preserves the expected popup coordinates while waiting for Quickshell's existing deferred polish. The original immediate comparison fails on both Qt's offscreen backend and an isolated XCB display. The updated test passes on a private authenticated Xvfb display. Production popup positioning code is unchanged.

The package builds production and test executables separately: `BUILD_TESTING=OFF` for the installed binary, `ON` for nine selected CTest targets. `check()` uses Xvfb with TCP disabled, without connecting test windows to the owner's desktop. ARM builds use two jobs to bound heat and memory pressure. Run the Wayland service regression separately with `python tests/check_idle_notification_replacement.py` from an unlocked native session; do not interact with the phone during its short idle observation.

The original installed package and detached signature are retained privately for rollback. Package integrity, a running native shell, actual automatic secure locking and physical wake/PIN acceptance must be recorded individually before claiming the complete feature.
