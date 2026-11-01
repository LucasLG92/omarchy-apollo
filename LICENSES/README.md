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
| R12 `drivers/input/misc/aw8697.c` and input Kconfig | [GPL-2.0-only](GPL-2.0.txt); original v3 driver by Armandas Kvietkus, with Griffin Kroah-Hartman and AWINIC copyright notices retained |
| R12 input/QCOM Makefiles and `drivers/media/rc/ir-spi.c` | [GPL-2.0](GPL-2.0.txt), exact original identifiers; IR source retains Samsung Electronics / Andi Shyti attribution |
| R12 AW86927 binding changes and new Apollo input DTS | [GPL-2.0-only](GPL-2.0.txt) **OR** [BSD-2-Clause](BSD-2-Clause.txt); existing binding header and new DTS identifier retained |
| R13 `hexagonrpcd/apps_std.c` scratch-file change | [GPL-3.0-or-later](GPL-3.0-or-later.txt); **Copyright (C) 2023 The Sensor Shell Contributors**, original notice retained |
| Original V2 Omarchy PNG assets and upstream theme composition | MIT — **David Heinemeier Hansson**; original notices retained in both [native theme directories](../experiments/original-boot-v2/native/) |
| V2 portrait/touch adaptation, local keyboard, staging and KMS capture helper | [MIT](../experiments/original-boot-v2/LICENSE) — Omarchy Apollo contributors; no redistributed Qt/SDDM/Plymouth toolchains |
| SIM access-PIN UI 0.1.3 candidate | [MIT](../experiments/sim-unlock/LICENSE) — 2026 Apollo contributors; source only, GTK/GIO dependencies not redistributed |

Patch files preserve the upstream context and are distributed under the licenses of the code they modify. See [patch provenance](../patches/rebase-4.5/README.md). The existing hardware archive, Quickshell, libcamera and graphics packaging retain their own notices; consult those directories before redistributing builds.

The R12 [file-by-file origin record](../patches/rebase-4.5/linux-apollo-input-origin.json) identifies the original review messages and driver blob. GPL-2.0-only and GPL-2.0 references use the included GNU GPL version 2 text; neither is relabeled “or later.” The BSD-2-Clause text is reproduced from [Linux v7.1's license file](https://github.com/torvalds/linux/blob/v7.1/LICENSES/preferred/BSD-2-Clause).

For R13, the [original apps_std.c notice](https://github.com/linux-msm/hexagonrpc/blob/93f3467dcfe1601bb70547611866a069ae914de5/hexagonrpcd/apps_std.c) permits GPL version 3 or later, and the pinned repository's [COPYING](https://github.com/linux-msm/hexagonrpc/blob/93f3467dcfe1601bb70547611866a069ae914de5/COPYING) contains GPLv3. The historical hardware recipe's package-level GPL-2.0-or-later label does not replace that source notice. The [R13 origin record](../patches/rebase-4.5/hexagonrpc-scratch-origin.json) preserves the attribution and discrepancy. The root MIT license does not apply to that imported source change.

V2 assets are from [Omarchy commit 5978d93a](https://github.com/omacom/omarchy/tree/5978d93ae7da0a325b7493501911e3f1266cadd3), under its original MIT license. The [asset manifest](../experiments/original-boot-v2/source-manifest.json) records original Git blobs; the native `LICENSE-Omarchy` files retain the full DHH notice. The [R16 media provenance](../media/README.md) distinguishes the native KMS capture from Qt renders. No endorsement or ownership of upstream branding is claimed.

## Upstream projects

[Omarchy](https://github.com/omacom/omarchy) · [Omarchy Mobile](https://github.com/derekross/omarchy-mobile) · [Apollo hardware packages](https://github.com/royka1/Xiaomi-Apollo-pmOS-packages) · [Linux](https://www.kernel.org/) · [Arch Linux ARM](https://archlinuxarm.org/) · [Hyprland](https://github.com/hyprwm/Hyprland) · [Quickshell](https://github.com/quickshell-mirror/quickshell) · [libcamera](https://libcamera.org/) · [Waydroid](https://github.com/waydroid/waydroid)

These projects retain their authorship, trademarks and licenses. Omarchy Apollo is independent. Proprietary firmware is not redistributed. Screen-capture attribution and limits are recorded in [media provenance](../media/README.md).
