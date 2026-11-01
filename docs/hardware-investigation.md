# Hardware investigation

These notes distinguish driver leads from the bounded physical results in [R12 status](status.md). Android driver names and a patch tested on another phone do not prove complete Apollo functionality.

## Infrared

A read-only inspection of the development phone's Android environment confirmed an SPI infrared device bound to `ir-spi`. Its selected hardware description uses `ir-spi-led`, a compatible supported by the existing Linux [SPI IR LED driver](https://github.com/torvalds/linux/blob/v7.1/drivers/media/rc/ir-spi.c). In R12, a separate Apollo input DTS exposed the native LIRC device, and `GET_FEATURES` reported `0x302`. The [kernel patch](../patches/rebase-4.5/README.md) also appends an inactive SPI sample; its offline ARM64/QEMU fixture is separate from the phone test. No IR signal was transmitted. Optical emission, actual carrier/duty and operation as a remote remain unverified.

## Haptics

Android exposes the `aw8697_haptic` driver family. A subsequent Android chip-ID readback returned `0x97`, confirming AW8697 on the development device; no per-unit calibration is published. An [AW8697 v3 driver submission](https://lkml.iu.edu/hypermail/linux/kernel/2610.1/12414.html), dated 2026-10-13, adds force-feedback support and probe-time resonance calibration; its author reports testing on a POCO F3. R12 integrated that unmodified driver and physically exercised FF_RUMBLE for 120 ms at about 12.5% magnitude. The user confirmed a very soft vibration. Active local access and feedbackd opening were checked after adding a rule in RAM and restarting the service. Strength, app coverage and a complete boot with the prepared runtime v5 remain open. The original author and copyright notices are preserved in the [public patch and provenance](../patches/rebase-4.5/README.md).

## Motion, light and proximity

Android's sensor descriptors name an ST LSM6DSO accelerometer/gyroscope, ROHM BU27030 ambient light and a `Xiaomi Proximity` interface. In native R11, sensor proxy reported accelerometer and light available, but proximity unavailable. SAR ADUX registry entries alone do not establish which component implements ear proximity; alternative-device entries are not proof of fitted hardware. Gyroscope access for applications and proximity integration require their own native tests.

## Publication boundary

Only these aggregate findings are public. The selected Android device tree, raw inventory, per-unit registry/calibration and diagnostic logs are excluded. A later change should include the reviewed source, exact supported variant, recovery result and a bounded physical test before changing the hardware table.
