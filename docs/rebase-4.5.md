# Omarchy 4.5 RC2 rebase

The current development track starts from a fresh ARM64 userspace and adapts the touch interface to Omarchy 4.5. Its acceptance evidence is from RAM trials ending in restored Android, not a permanent new installation.

## Recorded stack

| Component | Recorded version / source |
| --- | --- |
| Omarchy | `4.5.0rc2-1` — [release](https://github.com/omacom/omarchy/releases/tag/v4.5.0-rc2) |
| Hyprland | `0.57.0` |
| Mesa | `26.2.6`, Freedreno FD650 |
| Kernel | R10/R11: `7.1.0-apollo-native-r5`; R12: `7.1.0-apollo-native-r6` with AW8697/IR additions; both use `cma=256M` |
| Mobile shell | `0.2.62.apollo45-5` |
| Mobile core | `0.1.23.apollo45-2` |
| Phone runtime | `20261101-4` in R11/R12; R12 added the haptic access rule in RAM. `20261101-5` includes the rule but has no complete boot test yet |
| libcamera / IPA / GStreamer bridge | `0.7.2.apollo1-1` |
| ModemManager Apollo | `1.24.2-4` in R11 |
| Omarchy Mobile source | [`f53b272f047a0099b9b6b73632f6be671395f07c`](https://github.com/derekross/omarchy-mobile/tree/f53b272f047a0099b9b6b73632f6be671395f07c) |
| Apollo hardware source | [`4c52c8bc8f8bd23a0e31dcd944a15f838777c3e2`](https://github.com/royka1/Xiaomi-Apollo-pmOS-packages/tree/4c52c8bc8f8bd23a0e31dcd944a15f838777c3e2) |
| libcamera base | `v0.7.2`, with the pinned mobile patch series retained |

Version suffixes identify these local adaptations; they are not official upstream releases. Normal package signatures and package/file integrity checks were used. No private package-signing material is distributed.

## Repository layout and build coverage

| Path | Scope |
| --- | --- |
| `docs/status.md` and `docs/validation-2026-11-01.md` | Current rebase acceptance and failures |
| `docs/evidence/2026-11-01-r*.json` | Sanitized summaries of R9–R12 |
| `patches/rebase-4.5/` | Reviewable torch, camera-sensor, EFS and kernel input changes, each with its own target/license |
| Root `PKGBUILD`, `platform/`, `config/`, `lock/`, other recipes | Earlier 2026-10-30 integration; not a complete R11/R12 build recipe |
| `hardware/apollo-base/` | Earlier imported hardware source archive and provenance |

The R11/R12 systems were built and tested privately with per-device calibration staged in RAM. This repository does not yet contain a validated end-to-end public builder for those systems. The patches do not contain calibration, are not firmware, and cannot be flashed. They target different source trees and are not one sequential patch series.

The R12 [kernel input patch and provenance](../patches/rebase-4.5/README.md) include the original AW8697 v3 review driver, kernel build/binding additions, a separate Apollo child DTS and an SPI IR inactive-tail change. The driver is not claimed to be merged upstream. R12 physically exercised only a very soft rumble; IR was queried without transmitting. The kernel patch does not contain the userspace access-rule packaging or the unpublished runtime image.

## Next release gate

Before recommending a permanent installation: publish a reproducible builder and matching artifacts, validate the native boot/recovery/storage plan, complete local first-PIN setup, retain Apollo-specific kernel/camera/modem variants through updates, and repeat hardware/security acceptance. The current native updater is guarded and incomplete. A successful RAM trial does not authorize formatting a user's phone.

See [roadmap](roadmap.md), [contributing](../CONTRIBUTING.md), [security](../SECURITY.md) and [license details](../LICENSES/README.md).
