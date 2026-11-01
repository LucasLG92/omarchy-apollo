# V2 review records

These are small result summaries, not raw logs or authentication records.

| Record | What it tested |
| --- | --- |
| [qml-review.json](qml-review.json) | 17 Windows Qt 6.10.2 offscreen checks, original-reference equality, keyboard interaction and a **rejecting mock**; no PAM or phone greeter |
| [browser-review.json](browser-review.json) | 6 offline HTML preview checks; no credential input |
| [plymouth-review.json](plymouth-review.json) | Official parser 26.134.222 and callback review; this report predates R16, so its physical-test flags remain false |
| [arm64-sddm.json](arm64-sddm.json) | Actual target ARM64 Qt 6.12.0-3 / SDDM 0.21.0-7 test-mode load and PC-builder package integrity; no PAM login |
| [R16 native evidence](../../../docs/evidence/2026-11-01-r16.json) | Later minimal-RAM Plymouth/DRM/VT and KMS capture test, followed by verified Android recovery; no full desktop or phone PAM login |

Source hashes bind the renders and ARM load to the published QML/script. They are source hashes, not private boot-image hashes. The repository's offline checks validate provenance and publication boundaries; they do not rerun the Qt/ARM or physical tests.
