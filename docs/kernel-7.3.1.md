# Current kernel: Linux 7.3.1 R15

**Installed on the development Mi 10T Pro · 4 November 2026.** R15 retains the
Apollo Linux 7.3.1 base and adds the native fingerprint prerequisites used for
the real enrollment/match/rejection milestone. No new kernel was flashed for
the prepared PAM integration. [Current results](milestone-2026-11-04.md).

The installed `r15-ddr-pm1` experiment differs from the earlier R15 image only
in **16 CPU-DDR device-tree tag bytes**. Kernel code, modules and ramdisk are
unchanged for that comparison. It is an installed experiment, **not a proven
battery optimization**; high idle drain remains under investigation.
No overclock, undervolt or thermal-protection removal is claimed.

The secure fingerprint path uses the native sensor/TEE services. Capture,
enrollment, encrypted persistence/reload, same-finger match and a different-finger
rejection passed. Standard PAM unlock is still awaiting handset deployment/tests.
Fingerprint-only wake from full suspend and its energy cost remain open.
Private images/calibration and the complete reproducible public builder are
not distributed. [Sources and boundaries](../experiments/native-fingerprint/README.md).

## Retained R14 migration and dated validation

The following describes the earlier R14 hardware port and its measured checks.
It is provenance for the retained base, not a new R15 battery benchmark.

# Apollo kernel: Linux 7.3.1 R14

**Installed and normally booted on one Mi 10T Pro · 3 November 2026.**
R14 carries the Apollo device support onto Linux 7.3.1. Earlier R9/R10/R12
documents describe their own checkpoints; they are not the current kernel.
[Current software and UI result](milestone-2026-11-03.md) · [Hardware status](status.md).

## Source provenance

The official [Linux 7.3.1 source archive](https://cdn.kernel.org/pub/linux/kernel/v7.x/linux-7.3.1.tar.xz)
and [detached release signature](https://cdn.kernel.org/pub/linux/kernel/v7.x/linux-7.3.1.tar.sign)
were verified using the upstream signing process. The archive SHA-256 is
`fa595aad93734f829c963c2a90ef7c3673224fd7fdae7b49406e397cde2de231`.
See [kernel.org signature guidance](https://www.kernel.org/signature.html).

The Apollo integration was compared across the production 7.1-based tree,
pristine 7.1 and pristine 7.3.1: 178 delta paths were reviewed, 19 merge conflicts
resolved and 160 modified source files retained over pristine 7.3.1.
This was a hardware/API migration, not a version-string replacement or a claim
that every patch from every Android custom kernel was merged.

The earlier hardware base is credited to
[royka1's Apollo packages](https://github.com/royka1/Xiaomi-Apollo-pmOS-packages)
and its upstream contributors. The installed kernel package carries the modified
source overlay. A complete public R14 build/export recipe is still pending;
the repository's older recipes do not reproduce the private development image.
No proprietary firmware or calibration is republished here.

## Implemented changes and retained mechanisms

| Area | R14 state | Scope |
| --- | --- | --- |
| Build | ThinLTO enabled while retaining normal ARM64 ET_DYN link flags | No artificial linker override; successful kernel/module build |
| Display panels | Carried panel drivers adapted to the refcounted/devm DRM panel interface | Native panel and accelerated desktop booted |
| Camera and firmware interfaces | Apollo adaptations carried across FastRPC, MHI, CCI/CAMSS, LPASS and firmware-authentication API changes | Four camera drivers bound and CAMSS graph present; R14 photo/video quality not certified |
| USB-C/PD charging | Charge current follows the announced TCPM budget, clamps/rounds values and preserves AICL/thermal protection | Actual budget/charging detected; unplugged autonomy and cold-plug animation are separate |
| CPU scheduling | EAS/schedutil retained with eight CPUs and stock limits | No overclock or undervolt; no workload-wide speedup claim |
| CPU idle | `menu` remains selected; TEO is available | TEO availability is not a demonstrated energy improvement |
| GPU | MSM hardware EGL, `simple_ondemand` and automatic runtime power control | Hardware renderer verified without llvmpipe; runtime suspend observed between activity |
| Memory | MGLRU active; zram LZO-RLE/LZ4/Zstd available, LZO-RLE still default | All three compressors passed exact-write/read checks; live swap was not reset for testing |
| Background work | Existing lazy-RCU and power-efficient workqueue configuration retained | Retained mechanisms, not newly measured battery savings |
| Security / device tree | Landlock ABI 11, reserved-memory layout retained, upstream PDC window-size correction applied | No thermal-limit removal or arbitrary PMIC writes |

## Validation actually performed

- Kernel and **502 modules** built, with architecture, release and installed
  module/artifact checks.
- Real ARM64 kernel booted in a diskless/networkless emulator. LZO-RLE, LZ4
  and Zstd zram roundtrips passed. These are correctness tests, not phone-speed benchmarks.
- **3,341 charging-policy C cases** passed and **646 device-tree checks** passed;
  reserved-memory ranges remained intact.
- Normal signed-package installation and native `depmod`; R12 fallback files
  retained. The tested R14 boot became the normal boot without changing recovery
  or DTBO for that migration.
- Native root/storage/calibration guards, eight CPUs, MGLRU and Landlock ABI 11
  checked after real boot.
- Hardware MSM EGL, Wi-Fi HTTPS, four bound camera drivers, media graph, touch,
  button and AW8697 input presence checked.
- The owner confirmed desktop, icons and widgets. Later UI rotation and Recents
  checks are recorded [separately](milestone-2026-11-03.md).
- No panic/oops, hung-task, GPU-fault or firmware-load-failure category was found
  in the bounded post-boot observation. This is not an unlimited stability guarantee.

## Still to measure or finish

There is no accepted before/after battery-runtime result, calibrated unplugged
power figure or overall performance percentage. Refresh rate, screen brightness,
radio conditions and workloads must be controlled for meaningful comparisons.
No arbitrary cross-kernel benchmark or advertised “battery kernel” result has
been substituted for measurements on this native Linux port.

Physical suspend/resume and wake sources, shutdown/cold-plug behavior, powered-off
charging, speakerphone/AEC, GPS/fingerprint, broader radios and R14 camera quality
remain open. Calls/SMS/mobile data and Android-app hardware paths were not
revalidated with R14 during the recorded test. Existing software integration
or an available driver alone does not close those items.

Private boot/initrd images, storage bindings, credentials, device identifiers,
firmware and unit calibration stay outside this public repository. The current
development image is not offered as a generic flashable release.
