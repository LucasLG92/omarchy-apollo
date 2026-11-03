# Same-kernel transactional userspace prototype

**Experimental source checkpoint, not an install command or public update channel.** Runtime packages are installed on one development handset, but boot integration is inactive. The new initramfs has not booted physically. See [results](../../docs/checkpoint-2026-11-03.md) and [pending physical tests](../../docs/pruebas-pendientes.md).

## Source layout

- `runtime/selector.c`: typed root-owned state, finite attempts, one-use health proof, previous-generation rollback and escape to the physical root.
- `runtime/init-versioned-usr.sh`: early mount pairing for `/usr`, `/opt`, ALPM local database and adapter metadata; unwinds a failed selection and retains the native storage guard.
- `runtime/apollo_updates.py`: signed exact-version cohorts, isolated preparation, private configuration handling, database lock/fingerprint, queue/rollback CLI and boot-activation gate.
- `runtime/health.py`: validates the actual mount pair and an available Omarchy/Hyprland desktop; a greeter alone is insufficient.
- `runtime/mobile_bridge.py` and `integration/omamobile-update`: reuse the existing authorization/update sheet and reboot indication; activate only with a trusted early-boot capability.
- `runtime/pending_guard.py` and the ALPM hook: prevent further native package mutations while a deployment is pending or unconfirmed.
- `integration/apollo-install-release`: signed bootstrap installer with explicit absent-package support. This bootstrap tool is not the boot selector or a general rollback implementation.

Original integration is MIT licensed; Omarchy Mobile-derived code retains its source notices. The root [license record](../../LICENSES/README.md) applies. [Source snapshot](source-snapshot.json) hashes identify exact development files across this experiment and the related firstboot/minimal export. Test adaptations use portable, synthetic fixture directories and are separately covered by the repository source manifest.

## Reproduce the small tests

Use a **disposable Linux VM/container as root** with Python 3, GCC and static libc development files. Root ownership is part of the selector trust checks. Tests create small temporary fixture directories below `/var/lib` and `/var/cache/pacman`, compile the actual selector for the host and mock package/authorization commands. They do not operate on the live package database or a phone. Temporary fixture directories are removed at process exit.

From the repository root:

```sh
python3 -m unittest discover -s experiments/transactional-updates -p 'test_*.py'
```

Expected: **66 tests**. `test_support.py` is a fixture helper, not an additional test. These tests do not download packages, copy an entire sysroot, modify boot partitions or run kexec. The separately recorded real ARM64 ALPM and six virtual-boot checks need external toolchains/sysroots and are **not reproduced by this command**. Their selected outcomes and limits are in [public evidence](../../docs/evidence/2026-11-03-native-updates.json).

## Boundaries

Preparation and selection retain the same kernel. `/etc`, `/home` and application data are not versioned by this prototype; shared configuration changes without a migration are rejected. There is no general config/data migration framework, public signed channel, complete image builder or validated native kernel-update path. A failed-health fallback in QEMU does not prove recovery from every physical hardware hang. Do not install these files by copying them over a running phone.
