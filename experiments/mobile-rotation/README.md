# Historical Apollo rotation source 0.2.0-2

For the selected installed source and current evidence, see the [latest integration](layout-followup/README.md). The snapshot below retains its original scope.

**Installed, enabled and active.** The controller observed a sensor-triggered
orientation change. **Human physical image-and-touch acceptance is pending**;
this is not a four-orientation certification.

The six exact [MIT payloads](SOURCEPINS.json) use the existing SSC SensorProxy and
Hyprland 0.57 interface. Monitor and touch transforms are coordinated; changes
stop on an unexpected layout instead of overwriting a foreign configuration.
The profile and baseline are public model-level DSI/NVT configuration for the
tested Apollo setup, not a probe or a unique device identifier. They retain
1080×2400, scale2.5 and the tested refresh setting; verify those assumptions on
another device before considering integration. No claim of VRR or battery savings.

`PKGBUILD.reference` preserves the actual recipe and payload-archive checksum for
provenance. The archive is deliberately not distributed, so it is **not a ready
makepkg source set**. Repackage the listed six source files under your normal
review/signing process. This repository update neither starts a service nor
applies the baseline, changes a display or installs a package.
