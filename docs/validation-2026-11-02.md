# R20 — native installation, normal boot and local login

**Reviewed 2026-11-02. One Mi 10T Pro development unit; no independent reproduction.** **Native OS installation is completed on this unit:** flashed native boot/internal root and local login are verified. **Later cold-boot login reproduced the black desktop center**; an official shell restart recovered Home, but the startup/rendering cause and definitive fix remain open. Human local SIM-PIN entry and cellular IPv4 passed. This does not establish complete daily-driver acceptance or a public installer.

[Latest cold-boot SIM/desktop result](evidence/2026-11-02-cold-boot-sim-desktop.json) · [earlier boot7 record](evidence/2026-11-02-native-boot-v7.json) · [initial R20 snapshot](evidence/2026-11-02-r20.json) · [login-v6 follow-up](evidence/2026-11-02-login-v6.json) · [earlier hardware trials](validation-2026-11-01.md). Earlier pending fields remain historical snapshots, superseded only where the later record provides evidence.

## Storage and persistent boot

- The initial 16 GiB source and complete physical readback matched **before the first writable native boot**. The ext4 filesystem was then expanded. [Why readback matters](internal-root-transfer.md).
- Native boot revision 7 was written, and normal reboot succeeded **without `fastboot boot`**. Systemd, the internal root and firmware/calibration guards were verified. Expected boot/recovery **image-prefix** readbacks matched; no full-partition hash equivalence is claimed.
- Android userdata was repurposed for the native root. Android `super`, `metadata` and `cache` were later cleared within the reviewed scope; the third reported normal boot passed after cleanup.
- The user entered the local code following normal boot and confirmed the desktop without a shell restart. This demonstrates persistent native boot/login on this unit, not unattended recovery, unplugged battery behavior or universal installation.

No unit image, calibration, filesystem identity, secret or private verification hash is published.

## Local owner setup and actual login

The user accepted the centered form, no duplicate software keyboard and correct second-field selection, then saved a local credential. Readiness/account-status checks used booleans only. Later **actual SDDM/PAM login passed**, including after normal boot: the user entered the credential locally and reached the desktop; the original theme, empty autologin User and ordinary-user Wayland socket were checked. No credential or account hash was read. This Linux credential is separate from SIM PIN. The subsequent cold-boot login succeeded but reproduced the desktop rendering failure described below; authentication success does not establish reliable startup presentation.

The published [r5 source](../experiments/owner-setup/README.md), native profile `20261101-5`, adds closing **600 ms after success only**. Actual ARM64 GTK synthetic checks and normal GPG/ALPM package verification were reported; the synthetic sink makes no PAM/shadow/radio operation. Separate human acceptance of that setup auto-close and **Polkit authentication remain pending**. Successful login does not substitute for testing administrative authorization.

## SIM UI and successful cold-boot local PIN entry

Installed SIM UI **0.2.1-1** is compact, with masked `Gtk.Button`/`PasswordEntryBuffer` fields and its own keypad without a Gtk.Editable/OSK surface. The earlier controller review reported byte-identical radio core/13 AST-identical flow methods, 18 classification and 17 ARM GTK synthetic checks. The profile 20261101-6 launcher-only fix followed a pre-login wait timeout, with seven offline checks; no new UI/launcher source is published.

The user subsequently **entered the primary SIM PIN only on the handset and confirmed coverage**. The app consumed it successfully: ModemManager reached connected/state11 and home registration, primary access PIN was no longer required and remaining lock was secondary **SIM_PIN2 (3)**. PIN2 is not evidence of a second card. The earlier enum2/no-user-session state is historical, not current. No PIN value, subscriber/operator/APN identity or credential screen is exported.

This establishes that local access-PIN entry and network result, not every error/retry/UX branch. Published [0.1.3 source/R19 loading](../experiments/sim-unlock/README.md) remain historical.

## Recurrent desktop center failure and restart recovery

An earlier live-gesture upgrade produced a black desktop that recovered through the official shell restart. One following normal boot worked without a restart. **The latest cold-boot login then reproduced a black desktop center**: the user reported coverage but no desktop, while the bar and search pill were visible. Quickshell had one process, no normal application windows and a loaded Home model. No per-unit geometry or raw diagnostic is published. This recurrence leaves an open startup/rendering fault; the earlier successful boot is not evidence that it is resolved.

Shell **.8** was installed with normal GPG/ALPM/Qkk verification. An official **Quickshell-only restart**, without restarting Hyprland or active PIN forms, recovered wallpaper, clock and eight icons according to the controller’s private capture review. The publication agent did not read or export that capture. This is recovery, **not a verified definitive startup fix**; cause investigation continues.

After that installation, the user accepted basic **HOME, hold-for-recents and keyboard closing** with gesture/keyboard **r2**. The controller also reports 14 integrated-touch, 14 Qt, 9 helper and 5 plugin-compile offline checks passed. Wider refinement remains open; returning Home when the final recent app is closed is a pending request. No new shell/plugin source payload is added here.

Visual boot6 failed human acceptance (white text/skipped logo). Boot7’s logo was missed by the user and remains visually unconfirmed; this is separate from the logged-in desktop recurrence.

## Cellular IPv4 and automatic profile r2

The initial internal-root data check returned cellular IPv4 HTTPS **204 with Wi-Fi off**, explicitly bound to the cellular interface. A forced IPv6 attempt did not verify connectivity. Later **automatic profile candidate r2 created a fresh profile after normal boot**, connected an active cellular route and returned HTTPS 204 with Wi-Fi off. This covers **one network**, not any SIM/operator, sustained transfer or 5G speed.

During an earlier transition, the modem service restarted while two project-created profiles were eligible. A service restart and disabling the older temporary profile’s autoconnect restored connectivity; the following normal boot connected. Causality and general reconnection reliability are not established by this observation. That cold boot initially required access PIN, but the user later entered it on the phone and confirmed coverage. With the fresh AUTO profile active, a request **bound to cellular IPv4 returned HTTPS204 while Wi-Fi was connected/preferred**. The cellular path was not the general default under Wi-Fi preference; that does not undo the successful bound test. The earlier Wi-Fi-off result remains separately scoped.

No operator, APN, SIM/network identity or address is published. A prior browser capture remained private because it contained an address. Automatic-profile source is not added in this update; only the reviewed outcome is documented.

## What remains unverified

R19’s manual outgoing voicemail call and audible downlink remain the latest bounded voice result. Microphone/uplink, incoming calls, SMS, speed, AEC and the VoLTE path remain unverified. R13 Wi-Fi and R16 minimal-rescue Plymouth keep their original scopes. GPS, fingerprint, proximity, IR transmission and the other [hardware gaps](status.md) are not completed by the boot milestone. The recurrent desktop startup/rendering fault, Polkit, latest-logo acceptance, wider gesture/keyboard polish, battery/suspend and upgrade/rollback remain open.

R17 manual recovery and R18/R19 automatic Android return preceded the native storage installation; they do not establish a current Android fallback after cleanup. No complete public builder/installer or independent reproduction is claimed. The regular Mi 10T still needs its own [variant validation](compatibility.md).

## Publication scope

The initial reviewed R20 summary was supplemented by later reviewed controller updates for local credential save/login, flashed native boot/cleanup, successful cold-boot SIM entry, cellular IPv4, recurring desktop failure/recovery and basic gesture/keyboard r2 acceptance. Only boolean/aggregate outcomes and the approved original form/CSS/synthetic source are included. Private images, firmware, filesystem identity, account verifiers, signing material, raw logs and calibration stay outside the repository.
