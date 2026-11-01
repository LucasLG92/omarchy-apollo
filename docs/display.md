# Display controls for a phone

> **Historical track — 2026-10-30.** This page describes the earlier integration, not current acceptance for the 4.5 RC2 RAM rebase. See [current status](status.md) and [the rebase record](rebase-4.5.md).


Open **Pantalla Apollo** from the application launcher. The installed mobile profile adds manual orientation, automatic rotation, a rotation lock and refresh-rate selections. The current panel advertises 60, 90, 120 and 144 Hz. The physical display remains at its previous 144 Hz setting until the owner chooses a change after PIN enrollment.

While the trusted PIN-creation surface is active, display changes return `APOLLO_PIN_SETUP_ACTIVE`. This guard was exercised against the installed service: the panel geometry, refresh, touch configuration and PIN process were preserved. Complete enrollment on the phone before trying the controls; do not share the PIN.

## Orientation and keyboard

The controller changes the compositor's monitor transform and touch transform together. It offers portrait, inverted portrait, both landscape directions, automatic rotation and a lock which preserves the current orientation. Automatic mode claims the real system accelerometer; choosing a manual orientation releases that claim. Sensor changes are debounced, and invalid or undefined readings do not select a new transform.

The service uses sensor and compositor events rather than a polling loop. It restores saved choices after a compositor configuration reload or service restart. The default configuration holds no accelerometer claim and changes no panel setting. Display preferences contain only orientation and refresh choices, in a private per-user state file. A failed preference write restores the previous monitor and touch configuration.

The keyboard profile reserves 300 logical pixels in portrait and 180 in landscape. Both sizes were measured from the real wvkbd layer in the isolated compositor test. Mobile revision 9 adds automatic text-input integration after PIN enrollment, while preserving the bar button for manual control. It stays hidden in manual mode while the PIN-creation surface is open. See the separate [19-check keyboard record and limits](keyboard.md).

## Commands

Use these in the native desktop session, without sudo:

```sh
omarchy-apollo-display settings
omarchy-apollo-display status
omarchy-apollo-display orientation auto
omarchy-apollo-display orientation lock
omarchy-apollo-display orientation portrait
omarchy-apollo-display orientation landscape-left
omarchy-apollo-display refresh 60
```

The GUI presents the same controls as the CLI and keeps a touch-sized **Cerrar** button in its header. Its desktop entry matches the GTK application ID. Refresh changes are accepted only for a mode advertised by the target panel. No measured battery-life improvement is claimed. Physical refresh switching remains to be acceptance-tested.

## Device checks and limits

The [23-check record](evidence/display-controls-2026-10-30.json) covers the actual controller, D-Bus client, GTK window, compositor, keyboard and real accelerometer connection. The compositor ran as a separate Wayland client on KWin's virtual backend, with private runtime, configuration, state and session bus. Its DRM-device list excluded the physical GPU card nodes. The physical display was not used or captured.

The checks exercise all four monitor/touch configuration pairs, invalid inputs, an unadvertised refresh mode, an actual permission-denied preference write and rollback, sensor claim/release, a real configuration-reload event, persisted restart, both keyboard sizes and GTK window creation. The refresh rejection test does not validate the real panel's four advertised modes. A matching transform setting is not a physical finger-mapping test. The phone was not moved through all four orientations during this run.

Run on the provisioned development phone from the local desktop account:

```sh
systemd-run --user --wait --pipe --collect \
  python -I /path/to/omarchy-apollo/tests/check_display_controls.py
```

This uses the desktop user's normal service context for the sensor policy. The test itself creates a private session bus. The optional `kwin` test tool is needed in addition to the installed mobile stack. The result uses a private fixture file, so auxiliary desktop-service output cannot be mistaken for the test record. The runner also verifies that the D-Bus owner is the exact controller process it started. Temporary compositors and clients are stopped afterwards. No owner credential is used. The installed controller is byte-identical to the tested source; the package and native database were checked after installation.

Physical automatic rotation, finger accuracy after rotation, application behavior in landscape, refresh switching and battery measurements remain pending. New-session cold boot and real PIN unlocking are separate acceptance gates.
