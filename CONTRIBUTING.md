# Contributing

Help turn a promising port into a dependable phone. Small, reviewable changes with a clear result are the most useful contributions.

## Choose the right track

Read [current hardware status](docs/status.md) first. The **4.5 RC2 rebase has a completed native installation and repeated normal-boot/login result on one Pro unit (R20), with broader phone acceptance and a public installer still incomplete**. Root packaging and older documentation describe the **2026-10-30 integration**; do not assume those recipes or acceptance results apply to the new track.

Useful areas: camera quality/rotation and the front high-resolution failure; audio and power measurements; drivers/sensors; touch and translation; reproducible builds; coherent native updates and recovery. [Roadmap](docs/roadmap.md).

## A good report

1. Name the phone model, code track, component versions/source commit and whether the result is native Linux or an Android container.
2. Describe expected and actual behavior, the smallest reproduction and whether it was observed on hardware or in a fixture.
3. For a fix, show the source change and the test that changed the result. Keep a failed control when useful.
4. State the recovery result and what remains untested. A service starting is not a working camera, call or GPS fix.

Use the issue templates. Hardware tests are run by a device owner with a recovery plan; do not add unattended flashing, partition formatting, unknown firmware writes or calls/messages to a test suite. Do not upload raw bugreports, firmware, calibration or partition backups.

## Check the public material

```sh
python3 tests/check_public_docs.py
```

This offline check validates document links, SVG structure, evidence invariants and the public source manifest. It does not connect to a device and does not prove hardware functionality or replace a manual privacy review.

Review every added screenshot, JSON field and patch. Remove account/contact/message content, location, SSIDs, addresses, device/radio identifiers, credentials, PINs/verifiers and private paths. Prefer a short sanitized outcome over a raw log. Use disposable fixtures for authentication tests.

Retain original authorship and licenses. New project integration is MIT; imported files keep their upstream licenses, including GPL/LGPL/CC0. See [license scope](LICENSES/README.md). Keep boot/device changes separate from UI changes so each can be reviewed and tested properly.
