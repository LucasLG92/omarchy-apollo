# Omarchy 4.5 RC2 rebase

The current development track starts from a fresh ARM64 userspace and adapts the touch interface to Omarchy 4.5. Its acceptance evidence is from RAM trials ending in restored Android, not a permanent new installation.

## Recorded stack

| Component | Recorded version / source |
| --- | --- |
| Omarchy | `4.5.0rc2-1` — [release](https://github.com/omacom/omarchy/releases/tag/v4.5.0-rc2) |
| Hyprland | `0.57.0` |
| Mesa | `26.2.6`, Freedreno FD650 |
| Kernel | R10/R11: `7.1.0-apollo-native-r5`; R12/R13 desktop: `7.1.0-apollo-native-r6` with AW8697/IR additions and `cma=256M`; R16 minimal splash rescue also used R6 |
| Mobile shell | `0.2.62.apollo45-5` |
| Mobile core | `0.1.23.apollo45-2` |
| Phone runtime | R11/R12: `20261101-4` with the R12 haptic rule added in RAM; R13: complete RAM boot of `20261101-6`, including that rule and the sensor scratch-file fix |
| libcamera / IPA / GStreamer bridge | `0.7.2.apollo1-1` |
| ModemManager Apollo | `1.24.2-4` in R11 |
| Omarchy Mobile source | [`f53b272f047a0099b9b6b73632f6be671395f07c`](https://github.com/derekross/omarchy-mobile/tree/f53b272f047a0099b9b6b73632f6be671395f07c) |
| Apollo hardware source | [`4c52c8bc8f8bd23a0e31dcd944a15f838777c3e2`](https://github.com/royka1/Xiaomi-Apollo-pmOS-packages/tree/4c52c8bc8f8bd23a0e31dcd944a15f838777c3e2) |
| libcamera base | `v0.7.2`, with the pinned mobile patch series retained |
| HexagonRPC base | [`93f3467dcfe1601bb70547611866a069ae914de5`](https://github.com/linux-msm/hexagonrpc/tree/93f3467dcfe1601bb70547611866a069ae914de5), then the pinned Apollo `hexagonrpcd-apollo/apollo-sensor-fixes.patch`, then the R13 scratch-file patch |
| Original boot / login V2 | Omarchy assets/design at [`5978d93ae7da0a325b7493501911e3f1266cadd3`](https://github.com/omacom/omarchy/tree/5978d93ae7da0a325b7493501911e3f1266cadd3); theme package `apollo-mobile-boot 0.2.0-1` verified in PC builder; target Qt `6.12.0-3` / SDDM `0.21.0-7` test-mode load |

Version suffixes identify these local adaptations; they are not official upstream releases. Normal package signatures and package/file integrity checks were used. No private package-signing material is distributed.

## Repository layout and build coverage

| Path | Scope |
| --- | --- |
| `docs/status.md` and `docs/validation-2026-11-01.md` | Current rebase acceptance and failures |
| `docs/evidence/2026-11-01-r*.json` | Sanitized summaries of R9–R13 |
| `patches/rebase-4.5/` | Reviewable torch, camera-sensor, EFS, kernel input and sensor RPC changes, each with its own target/license |
| Root `PKGBUILD`, `platform/`, `config/`, `lock/`, other recipes | Earlier 2026-10-30 integration; not a complete R11–R13 build recipe |
| `hardware/apollo-base/` | Earlier imported hardware source archive and provenance |
| `experiments/original-boot-v2/` | Original design, portrait/touch source and review records; not active theme configuration or a complete phone login installer |

The R11–R13 systems were built and tested privately with per-device calibration staged in RAM. This repository does not yet contain a validated end-to-end public builder for those systems. The patches do not contain calibration, are not firmware, and cannot be flashed. They target different source trees and are not one sequential patch series.

The R12 [kernel input patch and provenance](../patches/rebase-4.5/README.md) include the original AW8697 v3 review driver, kernel build/binding additions, a separate Apollo child DTS and an SPI IR inactive-tail change. The driver is not claimed to be merged upstream. R12 physically exercised only a very soft rumble; IR was queried without transmitting. The kernel patch does not contain the userspace access-rule packaging or the unpublished runtime image.

The R13 sensor RPC patch creates a missing scratch file only for an already permitted writable mapping, with mode 0600 and no symlink following. Runtime v6 completed a RAM boot and included the earlier haptic access rule: feedbackd opened the device without manual restart. This validates that v6 session, not an intermediate v5 boot or a permanent installation. [R13 evidence](evidence/2026-11-01-r13.json).

R16 is a separate minimal RAM rescue test of Plymouth, with native DRM/VT and a reviewed KMS image. It did not boot this complete userspace stack or stage private calibration. Real ARM64 SDDM test-mode loading is also recorded, but phone PAM login and local credential setup remain untested. R13 remains the latest full-desktop acceptance record. See [V2 sources and scope](../experiments/original-boot-v2/README.md).

## Next release gate

Before recommending a permanent installation: publish a reproducible builder and matching artifacts, validate the native boot/recovery/storage plan, complete local first-PIN setup, retain Apollo-specific kernel/camera/modem variants through updates, and repeat hardware/security acceptance. The current native updater is guarded and incomplete. A successful RAM trial does not authorize formatting a user's phone.

See [roadmap](roadmap.md), [contributing](../CONTRIBUTING.md), [security](../SECURITY.md) and [license details](../LICENSES/README.md).
