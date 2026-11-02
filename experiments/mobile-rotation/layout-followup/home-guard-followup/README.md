# Android/Home rotation guard

Installed rotation 0.3.1-3 and shell 20 use the exact
[rotation client](../rotation.py) and [launcher](../omamobile-launch), with
[current source pins and scope](../SOURCEPINS.json). Bar/Launcher 19 are retained.

From empty Home, a five-second generation-bound rule retains the most recent
eligible background Android class on its original workspace with silent placement,
float and maximize. Normal activation and timeout cancel it; old callbacks cannot
affect a newer activation. It does not force focus, close tasks or set global
noFocus. Cleanup follows explicit matching/restore conditions.

**Real focused cycle passed:** guard armed and Home stayed empty in portrait and
landscape, with one background F-Droid window retained. Normal reopening disabled
the live guard before the app opened. The restart adopted the last acknowledged
output/requested-touch pair; that is not hardware touch-matrix readback.

This establishes the tested case, not all APKs, tasks, processes or surfaces.
The physical bar cycle also passed without opening an app; the earlier failure
was before 19. This does not validate wider gestures, APKs or layouts. The 94host ARM-Lua/simulated-interface checks remain separate from
this real-compositor result. Original [Apollo MIT](../LICENSE-Rotation) and
[Omarchy Mobile MIT](../LICENSE-OmarchyMobile) notices remain. No binary,
signature, live identifier, log or memory address is distributed.

The real Home/reopen cycle was tested on 3.1-2. Installed 3.1-3 adds only cleanup
of a matching original surface when was_float=false; 104focused assertions and
the updated live compositor function/inactive rule passed, without extra rotations.
The observed reopened window was floating, but its earlier state was not recorded:
actual float-off/tiling restoration is not claimed. Wider APK/task/process/surface
coverage and complete physical interface/hardware acceptance remain unverified.
