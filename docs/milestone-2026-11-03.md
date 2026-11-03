# Linux 7.3.1 R14 and the mobile rendering milestone

**3 November 2026 · one Xiaomi Mi 10T Pro development unit.**
Linux 7.3.1 R14 is installed as the normal native boot. The owner entered the
local session normally and confirmed Home, icons and widgets. The latest UI
updates are installed, not merely host-side candidates.

[Structured summary](evidence/2026-11-03-r14-ui.json) ·
[Fresh handset screenshots](gallery.md) · [Kernel changes](kernel-7.3.1.md).

## Tested software

| Component | Installed version |
| --- | --- |
| Native kernel | `7.3.1-apollo-native-r14` |
| Kernel package | `linux-apollo-native-r14 7.3.1.apollo.r14-1` |
| Omarchy | `4.5.0rc2-1.12` |
| Hyprland | `0.57.0-2.4` |
| Mobile shell | `0.2.62.apollo45-29` |
| Rotation integration | `0.4.9-1` |

The existing signed-package path was used. Signatures, exact package plans,
installed payloads and package integrity were checked. The 20 existing managed
Omarchy adaptations were verified separately rather than accepting arbitrary
integrity warnings. The owner's configuration and account were preserved.

## Complete repaint after application and keyboard changes

The owner reported fragments or stale pieces after switching applications and
opening/closing the keyboard. A temporary `debug.damage_tracking = 1`
compatibility check was human-confirmed to display complete, fitting interfaces,
then made permanent in the packaged phone configuration.

Monitor damage mode repaints the complete output **when damaged**, retaining the
compositor's idle-frame gating. It is not continuous undamaged rendering. See
the [Hyprland option reference](https://wiki.hypr.land/configuring/core/config-options/).
No font, zoom, DPI or output-scale change was used to disguise the issue.

After the final shell reload, an owned GTK fixture's workarea and actual inner
allocation followed 960×372 → 960×192 → 960×372 with keyboard visibility. All
three phases fitted, and the original workspace and keyboard state were restored.
This checks geometry and the persistent mode; the earlier human comparison is
the visual evidence for the reported fragments.

## Rotation: release at a composed frame

The earlier immediate release attempt produced a reported black flash and was
rejected. The new compositor API queues the finish request and retains the old
GPU frame until the newly composed scene is ready at the output boundary.
The existing bounded expiry, authentication/DPMS cancellation and input/scanout
guards remain. Rotation images are not written to disk.

The candidate first passed a bounded real-panel/GPU test with a synthetic
configuration and protected home, after a verified empty owner session exited
normally. The display manager was restored. After installation, the owner
logged in normally; no password or PIN was obtained by the agent.

| On-device transaction | Release time | Bars fit | Wallpaper reloaded |
| --- | --- | --- | --- |
| 1 | 680.1 ms | Yes | No |
| 2 | 499.8 ms | Yes | No |
| 3 | 498.4 ms | Yes | No |
| 4 | 647.6 ms | Yes | No |

These durations start at the rotation transaction, **after sensor detection**.
They are four observations, not an end-to-end sensor benchmark or a guarantee
for every app. All four GPU holds were active, safe releases completed and
native fallback/timeouts stayed at zero. The original monitor/touch pairing
was restored. Static screenshots show the final orientation, not transition
smoothness; broader physical visual acceptance remains useful.

## Recents: reproduce the black screen, then stop the shell restart

Closing five disposable GTK windows with Recents open repeatedly changed the
shell process and reset its counters. The compositor and owner session stayed
alive. No GPU/OOM fault category was found in that observation. No native stack
trace was collected, so a particular native crash function is not claimed.

The final shell uses the native toplevel model for incremental row removal,
instead of rebuilding a reversed JavaScript-array model while window objects
are being destroyed. Nearby cards use still previews; off-screen cards do not
keep exporting live frames. [ObjectModel](https://quickshell.org/docs/types/Quickshell/ObjectModel/)
and [ScreencopyView](https://quickshell.org/docs/types/Quickshell.Wayland/ScreencopyView/)
describe the underlying interfaces.

Recents requests Home preparation through the established public IPC, respecting
the scoped plugin API. It waits for an empty workspace and acknowledgement of
a fresh Home frame before hiding. The wait is bounded; it does not unmap Home,
reset its layout or create a continuous idle polling loop.

**Final regression check:** three bursts of five disposable windows, 15 total,
with the same shell process throughout, completed handoffs without watchdog
timeouts, visible Home/icons, no Home remaps and no wallpaper reloads. Only
the owned test service was signalled; global Clear all and user app closure
were not used by this automated test. The earlier human-confirmed last-app
return-to-Home result retains its separate scope.

## What this milestone does not certify

- Cellular calls, SMS and data were not revalidated on R14; the test SIM had
  been removed. Historical outgoing voicemail/downlink and IPv4 results remain historical.
- Speakerphone remains unresolved after distortion and a later reported
  call-time restart. No new call, loudspeaker playback or microphone recording
  was performed for this milestone or its screenshots.
- Fingerprint enrollment/unlock, GPS, Bluetooth audio, proximity and other
  unfinished hardware functions do not become complete through UI changes.
- Battery runtime, physical suspend/wake, shutdown/cold cable insertion and
  the powered-off charging animation still need dedicated physical validation.
- The private boot image is not a generic public installer. The regular Mi 10T
  5G has not been independently validated.

The fresh Phone/Recents screenshots used disposable application data; GNOME
Calls used a dummy provider and no call was placed. No credentials, biometrics,
subscriber/network identifiers, personal conversations, partition images,
firmware or per-device calibration are included in the public record.
