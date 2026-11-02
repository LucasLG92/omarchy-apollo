# Local owner credential form — r5 source

An original GTK4/libadwaita form for Apollo's supervised native provisioning. It follows Omarchy's palette, centers the mobile layout and provides its own masked numeric keypad. This is the **native profile `20261101-5` (r5)** form source reviewed during R20 (the later `20261101-6` changes only the separate launcher), not a complete installer or general desktop authentication service.

[R20 result and boundaries](../../docs/validation-2026-11-02.md) · [review metadata and public-source hashes](review.json) · [current status](../../docs/status.md).

## Physical result and remaining checks

The user accepted the centered layout, correct second-field selection and absence of duplicate software keyboards, then saved the local credential on the phone. Only readiness/account-status booleans were checked; the credential and account hash were not read.

The subsequent r5 change closes the form 600 ms after a successful save, with an actual ARM64 GTK synthetic pass reported by the controller and the normal GPG/ALPM-verified profile installed. **Later R20 actual SDDM/PAM login passed, including after normal native boot.** The original theme, empty autologin User and ordinary-user Wayland socket were checked. Native installation and repeated normal boot are verified on the development unit. **Polkit authentication and separate human confirmation of the setup auto-close remain pending.** [Latest evidence](../../docs/evidence/2026-11-02-native-boot-v7.json).

## Source layout and integration contract

| File | Role |
| --- | --- |
| `owner-setup.py` | GTK4/PyGObject + libadwaita form and privileged local account/configuration sink |
| `omarchy.css` | Scoped dark palette, masked field selection and mobile targets |
| `assets/logo.png` | Unchanged, already-public Omarchy logo; original DHH MIT notice alongside it |
| `test_owner_setup_synthetic.py` | Actual GTK harness that replaces the credential sink with an in-memory stub |
| `review.json` | Small review summary; hashes identify these public source files, not a phone image or credential |

A reviewed package places the app, CSS and `assets/` together so relative assets resolve. Runtime dependencies are Python, PyGObject, GTK4 and libadwaita; they are not redistributed here. The complete privileged launcher, storage provisioning, package recipe and native profile are not included. This directory supplies source for review, **not a command to run provisioning on a computer or another phone**.

The real sink requires root, the native-root provisioning marker and absence of the owner-ready marker. Do not bypass or create those markers to test this source. It sets the `omarchy` account through `chpasswd` using a local anonymous pipe, checks normal account status, writes SDDM configuration that disables autologin and selects the original theme, then writes a non-secret readiness marker. It changes account/configuration state; a successful save does not establish a successful future login. Errors after an account update are not a transaction rollback.

The UI requires matching 8–32 numeric digits, preserves leading zeros, masks the protected buffers and has no `Gtk.Editable` input surface that could request another software keyboard. It clears visible buffers before asynchronous work and prevents a second submission or closing while work is pending. On failure it permits retry; only success schedules closing. These source properties are distinct from full security or accessibility acceptance.

The form contains no real/default credential. It does not put the value in command arguments, print it or save a plaintext credential file; the normal account system manages its verifier. Python memory clearing is not claimed to provide guaranteed zeroization. Linux login is separate from SIM PIN handling and does not implement touch-based LUKS unlocking.

## Test scope

The controller ran the included harness against actual ARM64 GTK. It subclasses the form and **overrides `set_credential`**, using conspicuous disposable values and an in-memory sink. The reported checks cover masking, second-field selection, validation, one pending submission, cleared buffers, responsive main loop and success-only closing. There are zero real PAM/shadow operations or radio/subscriber queries in that harness. The publication agent did not rerun the graphical harness.

The repository's ordinary offline checker imports neither GTK nor the real provisioning app. It extracts only the completion callbacks with AST and exercises fake controls/timers to verify failure stays open and success schedules the 600 ms close. Run those publication checks from the repository root:

```sh
python3 tests/check_public_docs.py
```

## License and provenance

The form, CSS and synthetic harness are original Omarchy Apollo source under the [MIT license](LICENSE). The unchanged logo is David Heinemeier Hansson's Omarchy asset under its [original MIT license](assets/LICENSE-Omarchy), reused from the repository's [V2 source tree](../original-boot-v2/source-manifest.json), pinned to commit `5978d93ae7da0a325b7493501911e3f1266cadd3`. No GTK/libadwaita binary, private provisioning data or complete unit image is included.
