#!/bin/bash
set -euo pipefail
BUILD=${APOLLO_BUILD:-$PWD/build}
HOST=${APOLLO_REPO:?Set APOLLO_REPO to the checkout path}
REFERENCE=${APOLLO_REFERENCE:?Supply private reference assets; see docs/BUILD.md}
TAG=apollo-7.1.0-r12
EXPECTED=bb417efef17457e7b512334052ea3e5a2646ce6019123d6089c7cb30ccf652913913fbe5d7c6ae24c96f06ed3aab924bbd0ee6376ac510856e9381a7aa25f021
mkdir -p "$BUILD/downloads" "$BUILD/kernel-out" "$BUILD/artifacts"
cd "$BUILD/downloads"
ARCHIVE="linux-$TAG.tar.gz"
if [ ! -s "$ARCHIVE" ]; then
    curl --fail --location --retry 3 --output "$ARCHIVE" "https://gitlab.postmarketos.org/royka1/linux/-/archive/$TAG/linux-$TAG.tar.gz"
fi
printf '%s  %s\n' "$EXPECTED" "$ARCHIVE" | sha512sum -c -
if [ ! -d "$BUILD/linux-$TAG" ]; then
    tar -xzf "$ARCHIVE" -C "$BUILD"
fi
cd "$BUILD/linux-$TAG"
if ! grep -q 'EXPORT_SYMBOL_GPL(pcie_set_target_speed)' drivers/pci/pcie/bwctrl.c; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0001-pci-export-target-speed-for-mhi-module.patch"
fi
if ! grep -q 'transient identify error' drivers/media/i2c/s5k3t2.c; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0002-s5k3t2-retry-transient-probe-transport-errors.patch"
fi
if grep -q 'S5K3T2_AGAIN_MAX.*1024' drivers/media/i2c/s5k3t2.c; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0003-samsung-limit-front-and-macro-analogue-gain.patch"
fi
if ! grep -q 'venus_iova: venus-iova' arch/arm64/boot/dts/qcom/sm8250.dtsi; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0004-sm8250-reserve-low-venus-iova.patch"
fi
if ! grep -q 'vreg_l2c_1p08' arch/arm64/boot/dts/qcom/sm8250-xiaomi-apollo.dts; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0005-apollo-front-camera-digital-supply-1080mv.patch"
fi
if ! grep -q 'SM8250 downstream venus_ns' drivers/media/platform/qcom/venus/core.c; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0006-venus-sm8250-configure-content-protection-iova.patch"
fi
if ! grep -A8 'venus: video-codec@aa00000' arch/arm64/boot/dts/qcom/sm8250.dtsi | grep -q RPMHPD_MMCX; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0007-sm8250-iris-mmcx-power-domain.patch"
fi
if ! grep -A45 'venus: video-codec@aa00000' arch/arm64/boot/dts/qcom/sm8250.dtsi | grep -q opp-240000000; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0008-sm8250-iris-correct-opp-frequencies.patch"
fi
if ! grep 'sm8250_opp_pd_table\[\]' drivers/media/platform/qcom/iris/iris_platform_gen1.c | grep -q mmcx; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0009-iris-sm8250-scale-mmcx.patch"
fi
if ! grep -q legacy_synthetic_eos drivers/media/platform/qcom/iris/iris_core.h; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0010-iris-apollo-legacy-decoder-eos.patch"
fi
if ! grep -q 'Reset completion must also arrive' drivers/i2c/busses/i2c-qcom-cci.c; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0011-cci-reset-runtime-resume.patch"
fi
if ! grep -q 'static int s5k3t2_select_page' drivers/media/i2c/s5k3t2.c; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0012-s5k3t2-recover-initial-bank-selection.patch"
fi
if [ ! -f drivers/tee/qseecom/core.c ]; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0013-qseecom-experimental-tee-transport.patch"
fi
if ! grep -q 'recovered chip identification after CCI reset' drivers/media/i2c/ov13b10.c; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0014-ov13b10-recover-read-only-chip-id.patch"
fi
if ! grep -q 'static ssize_t mdt64_image_size' drivers/soc/qcom/mdt_loader.c; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0015-qseecom-elf64-image-assembly.patch"
fi
if [ ! -f drivers/misc/apollo-fpc-gpio.c ]; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0016-apollo-fpc-power-irq-test-interface.patch"
fi
if ! grep -q 'nvt_release_panel_follower' drivers/input/touchscreen/nt36523/nt36xxx.c; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0017-nt36523-detach-panel-follower-before-workqueue-teardown.patch"
fi
if ! grep -q 'static int wled_read_brightness' drivers/video/backlight/qcom-wled.c; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0018-wled-preserve-hardware-brightness-and-balanced-ovp-irq.patch"
fi
if ! grep -q 'postcore_initcall(apr_bus_init)' drivers/soc/qcom/apr.c; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0019-apr-register-built-in-bus-before-iommu-notifiers.patch"
fi
if ! grep -q 'goto disable_supplies' drivers/media/i2c/ak7375.c; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0020-ak7377-match-apollo-and-unwind-failed-resume.patch"
fi
if ! grep -q '#define CCI_I2C_MISC_CTL_SCL_STRETCH_EN' drivers/i2c/busses/i2c-qcom-cci.c; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0021-cci-always-enable-i2c-clock-stretching.patch"
fi
if ! grep -q 'mode_active_delay_us' drivers/media/i2c/ak7375.c; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0022-ak7377-wait-after-active-mode-before-position-restore.patch"
fi
if ! grep -q 'SET_SYSTEM_SLEEP_PM_OPS(pm_runtime_force_suspend, pm_runtime_force_resume)' drivers/media/i2c/ak7375.c; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0023-ak7375-preserve-runtime-idle-state-across-system-sleep.patch"
fi
if ! grep -q 'mode-bootloader = <0x2>' arch/arm64/boot/dts/qcom/sm8250-xiaomi-apollo.dts; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0024-apollo-define-bootloader-reboot-mode.patch"
fi
if ! grep -q 'An idle' drivers/clk/clk.c; then
    patch -Np1 --fuzz=0 < "$HOST/port-source/linux-apollo/0025-clk-avoid-powering-unprepared-orphan-parents.patch"
fi
if [ ! -f "$BUILD/kernel-out/.config" ]; then
    tr -d '\r' < "$HOST/port-source/linux-apollo/config" > "$BUILD/kernel-out/.config"
fi
FW="$REFERENCE/firmware-xiaomi-apollo/firmware-xiaomi-apollo-1.1.tar.gz"
printf '%s  %s\n' c484de15c12a776735a152efadbf9182bbd6ba3940a6672d38d441627bc07d2ead4b816ef63d5b0aad4ee3de09f1c5dc176a38a7d85aaf6f379884a527680722 "$FW" | sha512sum -c -
mkdir -p "$BUILD/firmware"
tar -xzf "$FW" -C "$BUILD/firmware"
python3 - "$BUILD/kernel-out/.config" "$BUILD/firmware" "$PWD/firmware" <<'PY'
from pathlib import Path
import re, shutil, sys
config, source, target = map(Path, sys.argv[1:])
value = re.search(r'^CONFIG_EXTRA_FIRMWARE="([^"]*)"', config.read_text(), re.M)
for name in value[1].split() if value else []:
    dest = target / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source / name, dest)
PY
scripts/config --file "$BUILD/kernel-out/.config" --enable SQUASHFS_ZSTD --enable ZRAM_BACKEND_ZSTD --enable SECURITY_LANDLOCK
scripts/config --file "$BUILD/kernel-out/.config" \
    --enable BT_LE --module BT_RFCOMM --enable BT_RFCOMM_TTY \
    --module BT_BNEP --enable BT_BNEP_MC_FILTER --enable BT_BNEP_PROTO_FILTER \
    --enable WATCHDOG_SYSFS --enable U_SERIAL_CONSOLE --enable DEVFREQ_THERMAL \
    --module SM_CAMCC_8250 --module I2C_QCOM_CCI \
    --module MHI_BUS_PCI_GENERIC \
    --disable VIDEO_QCOM_VENUS --module VIDEO_QCOM_IRIS \
    --enable QCOM_QSEECOM --module TEE_QSEECOM --module APOLLO_FPC_GPIO \
    --disable RTC_HCTOSYS --disable RTC_SYSTOHC
make O="$BUILD/kernel-out" ARCH=arm64 LLVM=1 olddefconfig
make O="$BUILD/kernel-out" ARCH=arm64 LLVM=1 -j12 Image.gz qcom/sm8250-xiaomi-apollo.dtb modules > "$BUILD/kernel-build.log" 2>&1
make O="$BUILD/kernel-out" ARCH=arm64 LLVM=1 INSTALL_MOD_PATH="$BUILD/artifacts" INSTALL_MOD_STRIP=1 modules_install >> "$BUILD/kernel-build.log" 2>&1
cp "$BUILD/kernel-out/arch/arm64/boot/Image.gz" "$BUILD/artifacts/"
cp "$BUILD/kernel-out/arch/arm64/boot/dts/qcom/sm8250-xiaomi-apollo.dtb" "$BUILD/artifacts/"
cp "$BUILD/kernel-out/include/config/kernel.release" "$BUILD/artifacts/"
echo "KERNEL BUILD COMPLETE"
cat "$BUILD/artifacts/kernel.release"
