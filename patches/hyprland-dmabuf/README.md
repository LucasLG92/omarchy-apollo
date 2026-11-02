# Hyprland DMA-BUF feedback backport

Three **unchanged upstream commits** applied to Hyprland 0.57.0, baseline
`0aa6745f705f2c4b0a5004eb019ef76e5bbdb426`, in numbered order. Their original
authors, public commit headers and BSD-3-Clause license are retained.
[Commit links and checksums](SOURCEPINS.json) identify the exact source.

The changes restore opt-in KMS format filtering, use a replacement feedback
table and refresh format feedback after configuration changes. This is a
targeted backport, not a whole-tree upgrade. Twelve upstream GTests linked
against the actual product library passed before deployment. The installed
`0.57.0-2.1` build retained the Arch hardening flags and dependency set.

After installation and normal reboot, the user accepted the desktop, Phone
and uninterrupted SIM flow. This supersedes the earlier open black-desktop
checkpoint for this tested configuration; it is not an unlimited cold-boot
reliability guarantee or a measured GPU-performance improvement.

See [the grouped device result](../../docs/mobile-milestone-2026-11-02.md).
No compositor binary, private diagnostic or live configuration is included.
