# Minimal native system and first-user setup

Reviewable development sources for the [3 November checkpoint](../../docs/checkpoint-2026-11-03.md). **The clean-image first-login sequence remains physically unaccepted.** These sources preserve an existing configured account; do not reset a real handset to manufacture a clean-install test.

`firstboot/` contains the local account state machine, operations/authorization boundary, provisioning broker and units, Qt/QML bridge, mobile setup/login theme, profile integration and synthetic tests. It collects administrator username, display name, password/PIN, hostname, locale, timezone, keyboard and optional apps. Passwords belong in the local UI, never a command line, report or repository.

`minimal/` contains the Web/Epiphany launcher, Bazaar entry, first-login profile step, native compatibility policy and PIN-layout patch. Their source is not a promise of an already validated generic installation image. Optional Flatpak apps and runtimes have their own updates; updating them does not replace the protected native device stack.

Python fixture tests, from the repository root on Linux with Python 3:

```sh
python3 -m unittest discover -s experiments/minimal-firstboot/firstboot/tests -p 'test_*.py'
```

The command exercises mocked account/authorization/profile operations. It does not create a real account, call PAM on the host or reproduce the separately recorded ARM64 account/PAM and Qt/QML tests. `firstboot/build-arm64.sh` builds the native Qt bridge and UI test with an ARM64 Qt 6 development environment; it is a component build, not a full image builder.

Original Apollo integration is MIT licensed. The Omarchy theme/branding assets retain David Heinemeier Hansson's MIT notice in `theme/LICENSE-Omarchy` and `profile-overlay/usr/lib/apollo/owner-ui/assets/LICENSE-Omarchy`. Existing upstream attribution is retained. Exact source hashes are listed in the related [source snapshot](../transactional-updates/source-snapshot.json) and repository-wide manifest. Generated binaries, user profiles and credentials are excluded.

[Pending clean-install and PIN acceptance](../../docs/pruebas-pendientes.md) · [Privacy](../../SECURITY.md).
