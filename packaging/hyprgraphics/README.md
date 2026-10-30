# Asynchronous resource completion fix

The phone froze during a desktop-package update. A private backtrace showed the
Hyprland main loop sleeping in `CAsyncResourceGatherer::await()` while rendering
error-overlay text. The gatherer worker was idle. This matches the lost-wakeup
path described in [upstream issue 53](https://github.com/hyprwm/hyprgraphics/issues/53).
The trace supports this diagnosis; it does not establish that every possible
desktop freeze has the same cause.

This patch keeps completion, condition-variable publication and waiting under
the resource mutex. An already-completed resource returns immediately. The
condition variable remains valid for multiple waiters. Worker wakeup and shutdown
flags also use their existing mutex. The library ABI and public class layout stay
unchanged.

The test uses the actual library. The stock `0.5.1-4` package times out when
completion occurs before waiting. The candidate passes 128 resources in each of
four modes: completion before waiting, waiting before completion, four concurrent
waiters, and immediate enqueue/wait. The upstream Image and ARG suites also pass.
These tests cover 512 resources; desktop activation and long-term stability are
separate acceptance steps.

Recreate the source archive from the pinned upstream release:

```sh
git clone https://github.com/hyprwm/hyprgraphics.git hyprgraphics-source
git -c core.autocrlf=false -c core.eol=lf -C hyprgraphics-source archive \
  --format=tar --prefix=hyprgraphics-0.5.1/ \
  --output="$PWD/hyprgraphics-0.5.1.tar" \
  482d4b7ec36ffdaf3573086aa586b178fd5404be
makepkg
```

Run the regression probe with an external timeout on the development phone:

```sh
c++ -std=c++26 -O2 -pthread ../../tests/check_async_resource_wait.cpp \
  -o wait-probe $(pkg-config --cflags --libs hyprgraphics)
for mode in late early multi immediate; do
  LD_LIBRARY_PATH="$PWD/src/build" timeout 12 ./wait-probe "$mode" || exit
done
ctest --test-dir src/build --output-on-failure --timeout 25
```

Check that `ldd ./wait-probe` with the same `LD_LIBRARY_PATH` resolves
`libhyprgraphics.so.4` to the candidate directory. Without that check, a missing
candidate path silently tests the installed stock library instead. The native
test runner caught this during preparation; the recorded successful run checks
the resolved library path explicitly.
