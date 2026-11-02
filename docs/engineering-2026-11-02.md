# Next kernels, cold login and clean first-user setup

**Development checkpoint, not a complete-phone release.** The permanent installation remains **R6 / boot7**. Earlier internal-root boot and local login are verified. Quickshell now uses an installed, scoped `QSG_RENDER_LOOP=basic` configuration; a live restart restored rendering, but **cold-login acceptance is pending**. This changes the render loop, not the GPU backend. The recurring black-center issue remains open.

| Work | What passed | What has not passed |
| --- | --- | --- |
| Quickshell basic render loop | Installed; rendering recovered after a live restart | Human cold-login acceptance and a definitive startup fix |
| Kernel R7 / Landlock | Supervised RAM boot and Pacman test | Committed, physically verified permanent R7 boot |
| Kernel R8 | Complete offline kernel, DTB and modules build | Boot-image integration and all phone charging/reboot/hardware tests |
| Sleep daemon fix | Two offline groups: **6 + 51 tests**; package signature checked on the host | Installation and physical suspend/wake |
| Clean first-user setup | r2 component checks and host signatures | **r2 is not deployable:** entrypoints are missing and clean-session initialization is incomplete. r3 integration is in preparation, not included or installed |

[Machine-readable scope](evidence/2026-11-02-engineering-candidates.json). Host signing does not establish installation or hardware acceptance. No package, signature, key, image, private configuration or raw diagnostic is distributed here.

## Runtime observations are not a benchmark

A filtered R6 greeter snapshot reported EAS1, **three Energy Model domains**, `schedutil` on all three CPU policies, PSCI/menu idle states with recorded usage, GPU `simple_ondemand` and runtime suspend, and both CPU/LLCC bandwidth monitors bound. These are runtime observations of those mechanisms, not a latency, battery-life or sustained-performance result. No CPU/GPU cap, overclock, undervolt or measured speed improvement is claimed.

The GMU's missing standalone sysfs `driver` link is not a GMU-failure result: the [MSM/Adreno initialization path](https://github.com/torvalds/linux/blob/v7.1/drivers/gpu/drm/msm/adreno/a6xx_gmu.c) initializes the GMU directly from GPU initialization and manages its runtime PM. Its reported runtime state was also suspended. No additional device data or raw diagnostics are included.

**The earlier USB-derived 0.47 W figure is withdrawn.** The charger `CURRENT_NOW` path was exposing processed IIO voltage without the current conversion. The [candidate patch and origin](../patches/rebase-4.5/linux-r8-origin.json) multiply processed microvolts by five for PM8150B buck mode, with negative/overflow rejection. The primary [MiCode getter at the pinned Apollo commit](https://github.com/MiCode/Xiaomi_Kernel_OpenSource/blob/acee5ab681485b77ba8d06ef4b0e39c8af974204/drivers/power/supply/qcom/smb5-lib.c#L5890) documents the gain.

The candidate remains charging-state gated and does not implement OTG telemetry. It has **no calibrated phone current/power validation** and changes neither charging limits nor negotiation. It is not evidence of energy savings or fast charging. USB input telemetry also does not establish unplugged battery drain or total device consumption.

## R8 is a source candidate

The [two source patches](../patches/rebase-4.5/README.md) address current units and add Apollo PON values `bootloader=2` / `recovery=1`. The offline build retained the R7 configuration except its local version; the DT semantic delta was limited to those two properties. **R8 has not been booted or exercised on the phone**, and this update contains no R8 boot image. PON-only handling is not proven sufficient for this device's bootloader: vendor IMEM/reset paths also exist. Source compilation and DT comparison do not establish reliable automatic Fastboot/Recovery entry.

## Administration and a future clean installation

The existing owner account's authenticated wheel/sudo rule was verified. The user also completed normal Polkit authorization and a password-change worker from the active graphical session. The local PAM credential remains the login/sudo credential; this did not remove SIM protection or create a password bypass.

Clean first-user setup is a separate, unfinished flow. r2 passed isolated checks—**32 backend, 49 ARM Qt/QML, 8 D-Bus, 19 ARM GTK mocks and 33 ARM shadow/PAM tmpfs checks**—and host signature verification, but a later integration review found missing entrypoints and incomplete clean-session initialization. Those checks do not make r2 deployable, and do not imply that the currently configured system lacks its normal session files. **r3 is being prepared; neither candidate is published or installed in this checkpoint.** A complete disposable clean SDDM/logind/session test is still required. The current owner must not be reset to test that work.

The bootstrap source audit covered only four early-boot scripts. It cannot establish complete clean-user behavior. Fingerprint enrollment remains unverified. This repository is still not a complete public installer.

Basic HOME/recents/keyboard closing and later returning Home after closing the final recent app received human acceptance. They remain separate from cold-login rendering. The [R20 hardware results and open gaps](status.md) retain their exact scope: outgoing/downlink voice and cellular IPv4 are not microphone, incoming calls, SMS, IPv6, throughput, GPS, fingerprint or complete daily-driver validation.
