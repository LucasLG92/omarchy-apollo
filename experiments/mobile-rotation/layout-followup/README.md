# Rotation and mobile shell: exact installed source

**Rotation 0.3.1-3 / shell 20** are selected here. Source pins include exact
rotation.py and omamobile-launch20; Bar/Launcher 19, HomePager 13, Search 14 logic,
the original install script and unrelated packaged patches are retained.
[Current hashes and scoped results](SOURCEPINS.json).

The cumulative `0002-shell16-to19-panel-geometry.patch` reconstructs the panel
sources from shell16 with `patch --binary -p1 --fuzz=0`, matching final hashes.
It targets extracted installed-shell paths, **not the core adapter95 baseline**.
The older 0001 launcher patch records the per-app screen backport; current helper
source additionally cancels the Home guard. These are source records, not a
complete package recipe or a live-system installer.

The automatic no-app/no-focus bar cycle passed portrait 44/44 at 432px and
landscape 32/28 at 960px, Search 408×48. The latest physical bar failure was before 19;
physical bar-cycle acceptance passed. The definitive Home-guard cycle retained empty Home
in both orientations and normal app reopening disabled the live guard. Only
one background F-Droid case is established; no all-app/surface claim is made.
[Guard detail](home-guard-followup/README.md).

The client publishes the existing monitor rule once per orientation change,
with invariant/drift checks; it does not rewrite mode/scale/refresh policy.
Exact app-ID compatibility rules override Android activity metadata; empty Home
and adaptable apps follow the sensor. The config has zero default overrides,
including no F-Droid-specific rule. [Contract and schemas](CONTRACT.txt).
The focused temporary override/restore test passed; requested touch transforms
are not hardware matrix readback.

Original MIT source headers and the Apollo/Omarchy Mobile notices are retained.
No runtime app inventory, identifiers, device data, package, signature, binary,
raw log, private configuration or memory address is included. No measured
battery/performance benefit or complete physical acceptance is claimed.

The real Home/reopen cycle was tested on 3.1-2. Installed 3.1-3 adds only cleanup
of a matching original surface when was_float=false; 104focused assertions and
the updated live compositor function/inactive rule passed, without extra rotations.
The observed reopened window was floating, but its earlier state was not recorded:
actual float-off/tiling restoration is not claimed. Wider APK/task/process/surface
coverage and complete physical interface/hardware acceptance remain unverified.
