# Native cameras in Omarchy

> **Historical track — 2026-10-30.** This page describes the earlier integration, not current acceptance for the 4.5 RC2 RAM rebase. See [current status](status.md) and [the rebase record](rebase-4.5.md).


All four Apollo sensors deliver camera buffers through the native PipeWire/libcamera stack in the current Omarchy session. The mobile profile includes [GNOME Camera / Snapshot](https://apps.gnome.org/Snapshot/), its GTK4 video sink and the PipeWire GStreamer plugin. The application is designed for computers, tablets and phones; its physical acceptance on Apollo is still pending.

## Choosing a camera

The previous policy exposed the three rear sensors under the same display name. The mobile profile now supplies distinct names without changing their node identities:

| Application name | Sensor |
| --- | --- |
| Apollo Main Rear Camera | Samsung S5KHMX |
| Apollo Front Camera | Samsung S5K3T2 |
| Apollo Ultrawide Camera | OmniVision OV13B10 |
| Apollo Macro Camera | Samsung S5K5E9 |

The WirePlumber fragment matches the exact Apollo node names and gives the main rear sensor a higher default priority. Applications can retain their own camera selection. The rules use the documented [libcamera monitor configuration](https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration/video.html).

Open **Camera / Cámara** from the application launcher. Complete the normal camera permission request on the phone. The isolated application test reached that permission dialog and stopped there; it was not counted as a successful graphical preview, photo or video test. Backend stream tests below do not replace that interaction.

## Fixing repeated camera opens

The software ISP created an EGL context whenever streaming started. Stopping cleared the image cache but retained the context, and the next start overwrote its handle. A long-lived camera manager could therefore accumulate graphics resources between opens.

Patch `0007-software-isp-release-egl-context.patch` releases the context on the ISP worker before the worker exits, resets the owned program handle and cleans up failed initialization. The shared EGL display stays available to other cameras. This preserves the GPU processing path.

The same stream-test source was used for the instrumented control and candidate:

| Device run | Completed opens | EGL contexts created / destroyed before service stop | Result |
| --- | --- | --- | --- |
| Installed libcamera 0.7.2-2 control | 7 of 12 planned | 7 / 0 | Next open failed; DMA-heap allocation errors observed |
| Corrected 0.7.2-3 candidate | 40 of 40 | 40 / 40 | All four cameras completed 10 opens each, 30 frames per open |
| Installed 0.7.2-3, ordinary environment | 12 of 12 | Test interposer removed | Three opens per camera, 30 frames per open |

The candidate's 1,200 frames and the installed package's additional 360 frames were 640×480 RGBA buffers with advancing timestamps. Freedreno FD650 was observed in the instrumented runs. One WirePlumber process stayed alive throughout each run; each camera client released its stream between opens. The test interposer only counts successful real EGL calls and does not replace their results.

The package build also passed the existing Samsung gain-helper checks. The candidate removed no exported symbols from the camera or camera-base libraries. Before installation, 58 installed files and links were compared with the retained rollback package. The reviewed upgrade changed only `libcamera-apollo`; its installed files match the tested archive. The temporary package-maintenance scope and library/audit overrides were removed, and the ordinary device-stack guard remains unchanged. The kernel stays at `linux-apollo 7.1.0-23`.

The current mobile profile is `omarchy-apollo-mobile 0.1.0-6` and requires `libcamera-apollo >= 0.7.2-3`. Its installed payload matches tested revision 5; revision 6 adds that minimum dependency. The [sanitized device record](evidence/camera-egl-lifecycle-2026-10-30.json) contains package checksums, individual stream cases and validation limits.

## Reproduce the stream checks

Use the provisioned development phone, close camera applications and run from its desktop account, without sudo:

```sh
python -I tests/check_camera_streams.py
```

The default is three opens of each camera, 30 frames per open. For the longer candidate workload:

```sh
python -I tests/check_camera_streams.py --cycles 10 --frames 30
```

The test discovers the current PipeWire nodes, checks their names, consumes complete camera buffers and checks advancing timestamps, release and continued discovery. Buffers are discarded; no camera image or video file is created. Last-sample caching is disabled, pad probes are removed and finished PyGObject objects are collected between opens so the test itself releases its resources. Contiguous-memory readings are recorded as diagnostics, not as a battery or performance benchmark.

`tests/support/egl-context-audit.c` is the test-only counter used in the dedicated instrumented WirePlumber process. It is not installed or enabled as a runtime dependency. The ordinary stream test does not need it or change service configuration.

## Still to validate

- Permission handling, preview layout, camera switching and photo/video controls on the physical phone.
- Correct orientation, exposure, color, optical autofocus and saved-photo quality.
- Video recording, audio synchronization and sustained capture.
- Cold boot, new-session suspend/resume and long-duration reliability with the updated library.
- Camera access from Android applications; native Linux support does not establish Waydroid camera support.

Owner PIN setup was kept running during the work. Its completion and real screen unlocking remain a separate acceptance gate. No camera scene or phone-setup screenshot is included in this repository.
