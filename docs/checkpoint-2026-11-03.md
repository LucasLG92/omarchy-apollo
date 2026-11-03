# Native-system checkpoint · 3 November 2026

Source publication for the work after the [R14 graphics milestone](milestone-2026-11-03.md). This remains an experimental port on one Mi 10T Pro. [Physical acceptance checklist — español](pruebas-pendientes.md) · [Sanitized evidence](evidence/2026-11-03-native-updates.json).

## Minimal native base and first-user setup

The development installation now uses **GNOME Web/Epiphany via Flatpak** and **Bazaar** for optional native Linux applications. Chromium, Firefox and optional utility/messaging packages were removed; essential phone, messaging, contacts, camera, files and administration components were retained. Existing personal application profiles were not deleted. There is no comparative energy or memory benchmark establishing that every website is cheaper in Web.

The earlier Android/Waydroid environment has been removed from the current development installation. Its source and dated results remain historical research. APKs are not native Linux binaries; this checkpoint does not promise an official native WhatsApp client, Google Play or Android compatibility. Web services depend on their own browser support.

The prepared first-user flow collects an administrator account, display name, password or PIN, hostname, language, timezone, keyboard and optional apps. It keeps account creation behind the local greeter/provisioning boundary, includes interrupted-setup handling and uses the account credential for authenticated administration. The existing owner's account is preserved. **A new account through a genuinely clean image, SDDM/logind and first normal login has not passed physical end-to-end acceptance.** The PIN layout revision also needs physical review after a renewed session.

Backend tests, an ARM64 disposable account/PAM check and Qt/QML ARM64 checks preceded this publication. [Reviewable firstboot/minimal sources](../experiments/minimal-firstboot/README.md) include tests and upstream theme notices; this is not a complete generic image builder.

## Transactional native userspace updates

The new experiment prepares a signed package cohort in an isolated candidate, then pairs **`/usr`, `/opt`, the local ALPM database and Apollo adapter metadata** at early boot. It retains the same kernel. A bounded-attempt C selector, mount helper, live-desktop health check, mobile update bridge and pending-transaction guard are included as [source](../experiments/transactional-updates/README.md).

The package plan checks signatures, hashes, dependencies and exact starting versions. Preparation uses a private on-device copy of configuration; `/home` and application data are excluded. Unmigrated shared-configuration changes are rejected. The private pacman download identity adjustment retains signature verification and never changes the active configuration. Before queueing, the ALPM database fingerprint is rechecked under its lock. Subsequent native package mutations are blocked while a trial is pending or unconfirmed.

This is **not a whole-filesystem snapshot**, a complete migration framework or a claim that every package is compatible. Existing configuration and app data are shared outside the versioned payload. General configuration/data migrations, a maintained public release channel and native kernel replacement are unfinished.

| Check | Result and boundary |
| --- | --- |
| Small updater tests | **66 passed:** 38 selector/manifest, 9 mobile integration, 6 additive installer, 8 pending guard, 5 private configuration. Signature checks in these unit fixtures include test doubles; genuine signature/ALPM work was separate |
| Real ARM64 package transaction on PC | Genuine project signatures; altered signatures/configuration rejected; active and fallback payloads unchanged; pending guard exercised. Synthetic identity/configuration only |
| ARM64 QEMU boots | **6 passed** with R14, ext4 and the shipping C selector/mount helper, including bounded fallback, acceptance, persistence and rollback. Synthetic desktop health/app/identity; no physical hardware certification |
| Real native ARM64 preparation on the handset | Passed for a harmless marker-package cohort in an isolated candidate. Active `/usr`, active ALPM, owner session and boot state preserved |
| Current activation | Runtime packages installed; store initialized; candidate **not queued**; new boot image **not installed or physically booted**; boot integration inactive; no reboot or partition write during preparation |
| Kernel updates | **Disabled. kexec not implemented or validated.** Existing R14 remains the normal boot |

Installed update-related packages at this checkpoint: `apollo-transactional-updates 0.1.0-5`, `apollo-minimal-system 0.1.0-8`, `omamobile-omarchy 0.1.23.apollo45-9`, with `omarchy 4.5.0rc2-1.14` and `apollo-firstboot-userland 0.2.0-2`. These versions describe the development handset, not a public package repository.

## Next physical gate

First RAM-boot the private initramfs while retaining the known boot partition. Check real login, desktop health, paired mounts, apps and gestures. Queue the harmless marker through the usual Omarchy update interface, then **RAM-boot that same image again** to test candidate selection. An ordinary reboot before permanent activation would use the old physical boot image and would not exercise the selector. Only after these checks should permanent boot integration and normal-reboot/rollback tests proceed.

The [checkbox plan](pruebas-pendientes.md) covers these steps, clean installation, hardware, power and remaining update work. No new fingerprint, speakerphone, battery-life or complete native-update acceptance is claimed. [Hardware status](status.md) · [Roadmap](roadmap.md).

## Publication boundary

This checkpoint contains generic sources, license/provenance records, reproducible small fixtures and selected boolean/count/version evidence. Private boot images, root filesystems, firmware, calibration, device/storage bindings, account files, credentials, biometric data and raw logs are excluded. Existing gallery captures predate the minimal-app cleanup; they are dated evidence, not a screenshot of the new app inventory.
