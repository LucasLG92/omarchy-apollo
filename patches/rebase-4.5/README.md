# Reviewable changes from the 4.5 rebase

These are source patches from supervised development tests. They are **not an installer or flashable files**. Each targets a different source tree; applying this directory as one patch series is incorrect. Review versions and retained upstream changes first.

| Patch | Target / change | Evidence | License |
| --- | --- | --- | --- |
| [Torch LED discovery](omamobile-torch-led-discovery.patch) | Omarchy Mobile shell 0.2.62: discover `white:torch` or Apollo `white:flash`, validate LED data and use the normal-user brightness path | R9 on/off control; visible-light confirmation remains open | MIT |
| [Apollo camera helpers/tuning](libcamera-apollo-sensors.patch) | libcamera 0.7.2 **after** the pinned mobile patch series: S5KHMX/S5K3T2/S5K5E9/OV13B10 helpers and sensor tuning; retains the mobile GPU/AF work | R9 four-sensor capture; R10 larger main/ultrawide RGB captures | LGPL-2.1-or-later C++/test files; CC0-1.0 Meson/data files |
| [EFS normal stop](mhi-efs-normal-stop.patch) | Apollo `mhi_efs_sync.c`: intentional signal cancellation exits successfully; a peer hangup still fails | ARM64 PTY negative control and R9 physical stop/restart | GPL-2.0, as the original source header |
| [Kernel input support](linux-apollo-input-support.patch) | Linux 7.1 Apollo hardware recipe revision 12, **after its existing hardware patches**: AW8697 v3 review driver, binding/build glue, separate Apollo input DTS and inactive SPI IR tail sample | R12 very soft physical rumble and feedbackd access; LIRC capabilities queried **without transmission** | GPL-2.0-only driver/Kconfig; GPL-2.0 Makefiles/IR; GPL-2.0-only OR BSD-2-Clause binding/DTS |

Source pins and versions are listed in the [rebase record](../../docs/rebase-4.5.md). Camera YAMLs/matrices come from [royka1's Apollo hardware packages](https://github.com/royka1/Xiaomi-Apollo-pmOS-packages/tree/4c52c8bc8f8bd23a0e31dcd944a15f838777c3e2), with recipe checksums verified during preparation. Mobile source is [Omarchy Mobile at f53b272](https://github.com/derekross/omarchy-mobile/tree/f53b272f047a0099b9b6b73632f6be671395f07c). The camera patch does not enable a 108 MP sensor mode or prove photographic quality.

No private EFS contents, sensor registry, radio identity, firmware or signing key is included. Preserve upstream authorship and the [file-specific licenses](../../LICENSES/README.md); the repository's MIT license does not replace them.

## R12 input provenance and limits

The [origin manifest](linux-apollo-input-origin.json) records the kernel target, patch checksum and original [AW8697 v3 driver submission](https://lkml.iu.edu/hypermail/linux/kernel/2610.1/12414.html) / [binding submission](https://lkml.iu.edu/hypermail/linux/kernel/2610.1/12284.html). The complete 760-line driver is unchanged from Git blob `9f703f81df2131700145d96e866e2d75b4d212f0`, with the copyright notices of **Armandas Kvietkus, Griffin Kroah-Hartman and AWINIC Technology** preserved. It is a review-submission backport, not a claim of upstream merger. The SPI driver retains its original Samsung Electronics / Andi Shyti attribution and GPL-2.0 notice.

The new DTS includes the existing public Apollo board source; it is not an Android device-tree dump. No per-unit motor calibration is included. The kernel patch does not package the userspace `uaccess` rule or distribute a runtime, boot image or firmware. R12 booted runtime `20261101-4` and added the rule in RAM; runtime `20261101-5` includes it but has no complete boot test yet. See [R12 lab notes](../../docs/validation-2026-11-01.md#r12--physical-rumble-and-infrared-detection).

An offline ARM64/QEMU check described in the manifest examined the SPI inactive-tail behavior. The R12 phone test only queried LIRC capabilities. Neither that fixture nor device detection establishes optical IR emission or remote-control operation.
