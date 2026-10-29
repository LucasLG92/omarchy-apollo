# Build status and recipes

These are integration packages for an already provisioned Apollo Linux base. This repository does not yet provide a validated installer from stock Android. Do not use a generic Omarchy ISO or format phone partitions with PC installation instructions.

Build as an ordinary user in a clean checkout on aarch64 with the matching, signature-verified Omarchy ARM edge and Arch Linux ARM repositories. The runtime recipe is the root `PKGBUILD`. It fetches a pinned upstream git commit and applies `patches/`. The original Apollo kernel, camera and firmware packages remain separate and must be preserved.

The recipes in `packaging/` build additional components. Put each recipe at the root of a separate clean staging copy of this repository as `PKGBUILD`, then use `makepkg` there. The keyboard recipe pins upstream wvkbd v0.20; the mobile recipe installs interface templates and its keyboard service; the Android recipe installs the ext4 bind-mount dependency and on-demand launcher.

Building a package does not install it, initialize Android, migrate existing Android data, seed a user's desktop or select a display-manager session. Those migration steps are being validated on the test device before becoming a public installer. The current development workflow retains the previous desktop configuration, original Android data directory and boot/recovery backups privately.

Record the upstream commit, resulting package checksums, dependencies changed and actual device tests for every release. Local integration builds and official signed repository packages must remain distinguishable. Do not disable signature verification to make a remote package install.
