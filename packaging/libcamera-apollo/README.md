# Current Apollo camera package

This directory preserves the libcamera 0.7.2 recipe, sensor tuning, gain tests and six patches from the retained Apollo baseline, with their original attribution and licenses. Revision 3 adds `0007-software-isp-release-egl-context.patch` for the software ISP's EGL stream lifecycle. The historical revision remains unchanged in `hardware/apollo-base/port-source/libcamera-apollo/`.

Build this directory with `makepkg` on aarch64 with the declared dependencies. The upstream archive and every local source have SHA-512 checksums. IPA signatures cover the installed bytes; the recipe keeps stripping disabled.

This package belongs to the reviewed Apollo camera stack. The normal package guard deliberately blocks generic camera-stack replacement. A device update needs a verified prior package, candidate validation and a scoped maintenance transaction. This repository does not yet offer an automated general-purpose device-stack updater.

See [camera integration and device evidence](../../docs/cameras.md). These are locally built integration sources, not a vendor-signed package or a complete phone installer.
