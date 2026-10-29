# Contributing

Small, reproducible improvements are welcome. Identify the exact phone model, upstream commit, kernel package and component you changed. Keep desktop results separate from Android-container results.

For a hardware fix, explain the failure, include the relevant source change and describe the test that changed its status. A successful service start alone does not establish a working camera, GPS fix, fingerprint unlock or cellular call. For UI work, include an actual device capture and check portrait layout, touch targets, keyboard visibility and suspend/resume behavior.

Keep boot, firmware, calibration and storage changes separate from desktop changes. This installation does not have the generic Omarchy disk layout. Never apply a PC installer or reset path to the phone without an Apollo-specific implementation and recovery procedure.

Before attaching logs or screenshots, remove credentials, keys, network names and hardware addresses, device identifiers, account information, locations and notifications. Prefer a short sanitized result over a raw diagnostic archive. Do not upload firmware dumps or partition backups.

Retain upstream attribution and the licenses of copied patches and tools. Avoid unrelated formatting changes and tests which merely restate configuration values.
