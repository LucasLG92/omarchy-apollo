# Reviewable changes from the 4.5 rebase

These are source patches from supervised development tests. They are **not an installer or flashable files**. Each targets a different source tree; applying this directory as one patch series is incorrect. Review versions and retained upstream changes first.

| Patch | Target / change | Evidence | License |
| --- | --- | --- | --- |
| [Torch LED discovery](omamobile-torch-led-discovery.patch) | Omarchy Mobile shell 0.2.62: discover `white:torch` or Apollo `white:flash`, validate LED data and use the normal-user brightness path | R9 on/off control; visible-light confirmation remains open | MIT |
| [Apollo camera helpers/tuning](libcamera-apollo-sensors.patch) | libcamera 0.7.2 **after** the pinned mobile patch series: S5KHMX/S5K3T2/S5K5E9/OV13B10 helpers and sensor tuning; retains the mobile GPU/AF work | R9 four-sensor capture; R10 larger main/ultrawide RGB captures | LGPL-2.1-or-later C++/test files; CC0-1.0 Meson/data files |
| [EFS normal stop](mhi-efs-normal-stop.patch) | Apollo `mhi_efs_sync.c`: intentional signal cancellation exits successfully; a peer hangup still fails | ARM64 PTY negative control and R9 physical stop/restart | GPL-2.0, as the original source header |

Source pins and versions are listed in the [rebase record](../../docs/rebase-4.5.md). Camera YAMLs/matrices come from [royka1's Apollo hardware packages](https://github.com/royka1/Xiaomi-Apollo-pmOS-packages/tree/4c52c8bc8f8bd23a0e31dcd944a15f838777c3e2), with recipe checksums verified during preparation. Mobile source is [Omarchy Mobile at f53b272](https://github.com/derekross/omarchy-mobile/tree/f53b272f047a0099b9b6b73632f6be671395f07c). The camera patch does not enable a 108 MP sensor mode or prove photographic quality.

No private EFS contents, sensor registry, radio identity, firmware or signing key is included. Preserve upstream authorship and the [file-specific licenses](../../LICENSES/README.md); the repository's MIT license does not replace them.
