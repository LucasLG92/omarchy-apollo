# Local firmware inputs

This recipe accounts for firmware that the earlier development image unpacked outside its package database. A clean image installs the model's GPU, touch, speaker and remote-processor firmware as a separate tracked package.

The two checksum-pinned input archives originate from the [Apollo postmarketOS package sources](https://github.com/royka1/Xiaomi-Apollo-pmOS-packages). They must be supplied privately in the build staging directory's `private-inputs/` folder. This repository contains the recipe and input filenames, not the proprietary archives or resulting firmware package.

Four model firmware files also exist in the generic Qualcomm and Cirrus packages. The model variants are installed under `firmware/updates/`, which the kernel searches before the generic directory. This preserves the tested versions without overwriting another package's files. See the kernel's [firmware search-path documentation](https://docs.kernel.org/driver-api/firmware/fw_search_path.html). Package installation has been checked in the new root; hardware acceptance after boot remains pending.

Device-specific modem NV, IMEI and radio identity are not package inputs. The separate modem service obtains its required device data privately at runtime. Do not publish device partitions, calibration dumps, firmware packages or personalized installation images with the source repository.
