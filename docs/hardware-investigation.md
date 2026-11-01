# Hardware investigation

These notes record useful leads, **not completed native features**. The current acceptance table remains [R11 status](status.md). Android driver names and a patch tested on another phone do not prove that the Apollo port works.

## Infrared

A read-only inspection of the development phone's Android environment confirmed an SPI infrared device bound to `ir-spi`. Its selected hardware description uses `ir-spi-led`, a compatible supported by the existing Linux [SPI IR LED driver](https://github.com/torvalds/linux/blob/v7.1/drivers/media/rc/ir-spi.c). The current Apollo native device tree does not expose a working LIRC device. Native device-tree/power integration and physical transmission/receiver validation remain to be done. No IR signal has been emitted by this investigation.

## Haptics

Android exposes the `aw8697_haptic` driver family. The exact fitted chip still needs confirmation before selecting a native driver. An [AW8697 v3 driver submission](https://lkml.iu.edu/hypermail/linux/kernel/2610.1/12414.html), dated 2026-10-13, adds force-feedback support and probe-time resonance calibration; its author reports testing on a POCO F3. That is a potential backport, not Apollo test evidence. The native R11 inventory had no haptics input device, and this investigation did not activate the motor.

## Motion, light and proximity

Android's sensor descriptors name an ST LSM6DSO accelerometer/gyroscope, ROHM BU27030 ambient light and a `Xiaomi Proximity` interface. In native R11, sensor proxy reported accelerometer and light available, but proximity unavailable. SAR ADUX registry entries alone do not establish which component implements ear proximity; alternative-device entries are not proof of fitted hardware. Gyroscope access for applications and proximity integration require their own native tests.

## Publication boundary

Only these aggregate findings are public. The selected Android device tree, raw inventory, per-unit registry/calibration and diagnostic logs are excluded. A later change should include the reviewed source, exact supported variant, recovery result and a bounded physical test before changing the hardware table.
