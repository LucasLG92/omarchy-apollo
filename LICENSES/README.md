# License scope and attribution

The root [MIT license](../LICENSE) covers original Omarchy Apollo integration and documentation. It does **not** relicense imported software, patches or third-party media. Existing source headers and nested license notices continue to apply.

## New rebase material

| Material | SPDX / origin |
| --- | --- |
| Original `media/hero.svg`, current project documentation and publication checker | MIT |
| `QuickSettings.qml`, `TorchModel.js` changes in the torch patch | MIT — Omarchy Mobile and Apollo adaptation |
| libcamera sensor helper/properties C++, new sensor-gain C++ test | [LGPL-2.1-or-later](LGPL-2.1-or-later.txt) |
| libcamera Meson changes and four sensor YAML files | [CC0-1.0](CC0-1.0.txt); Apollo tuning/matrices from royka1's hardware packages |
| `mhi_efs_sync.c` normal-stop change | [GPL-2.0](GPL-2.0.txt), retaining the original source identifier |

Patch files preserve the upstream context and are distributed under the licenses of the code they modify. See [patch provenance](../patches/rebase-4.5/README.md). The existing hardware archive, Quickshell, libcamera and graphics packaging retain their own notices; consult those directories before redistributing builds.

## Upstream projects

[Omarchy](https://github.com/omacom/omarchy) · [Omarchy Mobile](https://github.com/derekross/omarchy-mobile) · [Apollo hardware packages](https://github.com/royka1/Xiaomi-Apollo-pmOS-packages) · [Linux](https://www.kernel.org/) · [Arch Linux ARM](https://archlinuxarm.org/) · [Hyprland](https://github.com/hyprwm/Hyprland) · [Quickshell](https://github.com/quickshell-mirror/quickshell) · [libcamera](https://libcamera.org/) · [Waydroid](https://github.com/waydroid/waydroid)

These projects retain their authorship, trademarks and licenses. Omarchy Apollo is independent. Proprietary firmware is not redistributed. Screen-capture attribution and limits are recorded in [media provenance](../media/README.md).
