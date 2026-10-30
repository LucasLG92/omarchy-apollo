# Architecture

The installed Apollo base uses an Android boot image, a device-specific mainline kernel, a SquashFS lower layer and a persistent ext4 overlay on internal userdata. It does not use the generic Omarchy UEFI/Limine/LUKS/Btrfs image layout.

The desktop package pins upstream Omarchy commit `573b518be16ec47547d50fe6197bc7f53e982340`. Its integration identifies the exact `xiaomi,apollo` device-tree token before the broad Qualcomm laptop family. Authentication remains in the trusted lock component; ordinary shell plugins never receive authentication services.

The Apollo package deliberately selects desktop defaults rather than copying the upstream PC `/etc` tree. Existing camera, audio, USB maintenance, modem, firmware, memory and boot configuration remain owned by their respective device packages. A registered lifecycle boundary refuses generic reset, LUKS and boot takeover operations which this layout cannot implement.

Native cameras are exposed through the Apollo libcamera package and WirePlumber. The mobile profile provides exact-device naming rules and GNOME Camera. The reviewed `libcamera-apollo 0.7.2-3` update releases software-ISP EGL contexts between streams; kernel and boot configuration are unchanged. The [camera report](cameras.md) separates native stream evidence from physical application and Android-camera acceptance.

Android runs separately through Waydroid VANILLA. It is an Android compatibility environment, not a replacement kernel. Hardware access from Android applications requires its own validation and is not inferred from native Linux support. Google Play, Play Services and Google accounts are outside the requested profile.

Waydroid's data directory is bound from the native ext4 storage rather than being used directly on the host's overlay root. This allows Waydroid to create its own system/vendor overlays. Its service requires that mount; Android runs on demand rather than being a mandatory boot-time desktop dependency.

The Android desktop client controls a transient user session and waits for boot completion. APK installation uses a separate system D-Bus helper which accepts only a readable file descriptor from the active session user, snapshots the APK privately and obtains the actual Android package-manager result. The client releases that helper and waits for its process to exit before a stop/start cycle, so its private mount namespace cannot retain the old Android image mounts. See [Android integration](android.md) for the interface, test procedure and remaining limits.

A screen PIN protects the graphical session. It must not be described as disk encryption: this installed development base is not encrypted and retains authorized maintenance access.
