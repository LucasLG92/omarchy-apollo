# R20 — native installation, normal boot and local login

**Reviewed 2026-11-02. One Mi 10T Pro development unit; no independent reproduction.** **Native OS installation is completed on this unit:** flashed native boot and the internal ext4 root passed repeated normal boot, including after Android cleanup. The user entered the local credential after normal boot and reached the desktop. This does not establish complete daily-driver hardware acceptance or a public installer.

[Latest boot7 record](evidence/2026-11-02-native-boot-v7.json) · [initial R20 snapshot](evidence/2026-11-02-r20.json) · [login-v6 follow-up](evidence/2026-11-02-login-v6.json) · [earlier hardware trials](validation-2026-11-01.md). Earlier pending fields remain historical snapshots, superseded only where the later record provides evidence.

## Storage and persistent boot

- The initial 16 GiB source and complete physical readback matched **before the first writable native boot**. The ext4 filesystem was then expanded. [Why readback matters](internal-root-transfer.md).
- Native boot revision 7 was written, and normal reboot succeeded **without `fastboot boot`**. Systemd, the internal root and firmware/calibration guards were verified. Expected boot/recovery **image-prefix** readbacks matched; no full-partition hash equivalence is claimed.
- Android userdata was repurposed for the native root. Android `super`, `metadata` and `cache` were later cleared within the reviewed scope; the third reported normal boot passed after cleanup.
- The user entered the local code following normal boot and confirmed the desktop without a shell restart. This demonstrates persistent native boot/login on this unit, not unattended recovery, unplugged battery behavior or universal installation.

No unit image, calibration, filesystem identity, secret or private verification hash is published.

## Local owner setup and actual login

The user accepted the centered form, no duplicate software keyboard and correct second-field selection, then saved a local credential. Readiness/account-status checks used booleans only. Later **actual SDDM/PAM login passed**, including after normal boot: the user entered the credential locally and reached the desktop; the original theme, empty autologin User and ordinary-user Wayland socket were checked. No credential or account hash was read. This Linux credential is separate from SIM PIN. The latest cold-boot snapshot below has not yet reached a user Wayland session; it does not erase the earlier successful normal-boot login.

The published [r5 source](../experiments/owner-setup/README.md), native profile `20261101-5`, adds closing **600 ms after success only**. Actual ARM64 GTK synthetic checks and normal GPG/ALPM package verification were reported; the synthetic sink makes no PAM/shadow/radio operation. Separate human acceptance of that setup auto-close and **Polkit authentication remain pending**. Successful login does not substitute for testing administrative authorization.

## Current SIM UI and cold-boot boundary

The installed package is **`apollo-sim-unlock 0.2.1-1`**, a compact form without the large lock. It uses masked `Gtk.Button` fields backed by `Gtk.PasswordEntryBuffer` and a custom keypad, without a `Gtk.Editable`/OSK input surface. The controller reports the radio `sim_state` core is byte-identical to its previously reviewed implementation and 13 classification/preflight/send/close methods have identical ASTs. **18 classification checks and 17 ARM64 GTK synthetic checks passed.** These are reviewed-controller outcomes; no new private UI source or logs are included.

**Human access-PIN entry with 0.2.1 after cold boot is not confirmed.** The latest state is primary access PIN required, enum **2**, and no user Wayland session yet. Do not replace that with R19’s older PIN2/registered state or claim current network registration. The published [0.1.3 source and R19 load](../experiments/sim-unlock/README.md) remain historical.

The SIM launcher had timed out after 180 seconds while waiting for login without a user Wayland session. Profile **`20261101-6`** installed a launcher-only correction through normal GPG/ALPM: wait for the SIM user session as needed, then check the unlock state. The owner-setup wait remains 180 seconds. The controller reports **7 offline wait checks passed**; only the failed service was resumed, without replacing a live form. Human PIN completion remains pending, and no launcher source is added.

## Desktop, gestures and visual limits

The user confirmed HOME and hold-for-recents gestures. Thresholds and unwanted software-keyboard popups are still being refined. A black desktop after a live gesture update resolved through the official Quickshell restart; the next normal boot reached the desktop with human confirmation and no restart. This does not establish a persistent startup failure.

Visual boot revision 6 failed human acceptance: white text appeared and the expected logo was skipped. Revision 7 booted the internal root and retained a checked graphics-proof marker, but the user missed the logo. Its physical logo/animation appearance remains unconfirmed; a retained marker is not human visual acceptance or a measured boot percentage.

## Cellular IPv4 and automatic profile r2

The initial internal-root data check returned cellular IPv4 HTTPS **204 with Wi-Fi off**, explicitly bound to the cellular interface. A forced IPv6 attempt did not verify connectivity. Later **automatic profile candidate r2 created a fresh profile after normal boot**, connected an active cellular route and returned HTTPS 204 with Wi-Fi off. This covers **one network**, not any SIM/operator, sustained transfer or 5G speed.

During an earlier transition, the modem service restarted while two project-created profiles were eligible. A service restart and disabling the older temporary profile’s autoconnect restored connectivity; the following normal boot connected. Causality and general reconnection reliability are not established by this observation. After the latest post-cleanup cold boot, the SIM again required its access PIN, as expected; local human unlock and a new cellular check were still pending in this record. Wi-Fi function was reported.

No operator, APN, SIM/network identity or address is published. A prior browser capture remained private because it contained an address. Automatic-profile source is not added in this update; only the reviewed outcome is documented.

## What remains unverified

R19’s manual outgoing voicemail call and audible downlink remain the latest bounded voice result. Microphone/uplink, incoming calls, SMS, speed, AEC and the VoLTE path remain unverified. R13 Wi-Fi and R16 minimal-rescue Plymouth keep their original scopes. GPS, fingerprint, proximity, IR transmission and the other [hardware gaps](status.md) are not completed by the boot milestone. Polkit, latest-logo acceptance, gesture/keyboard polish, battery/suspend and upgrade/rollback remain open.

R17 manual recovery and R18/R19 automatic Android return preceded the native storage installation; they do not establish a current Android fallback after cleanup. No complete public builder/installer or independent reproduction is claimed. The regular Mi 10T still needs its own [variant validation](compatibility.md).

## Publication scope

The initial reviewed R20 summary was supplemented by later reviewed controller updates for local credential save, actual login, flashed native boot/cleanup, gestures and automatic cellular IPv4 candidate r2. Only boolean/aggregate outcomes and the approved original form/CSS/synthetic source are included. Private images, firmware, filesystem identity, account verifiers, signing material, raw logs and calibration stay outside the repository.
