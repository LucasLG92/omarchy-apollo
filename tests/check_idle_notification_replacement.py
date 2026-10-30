#!/usr/bin/python3
"""Exercise a real Wayland notification replacement; never lock the desktop."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", default="quickshell")
    parser.add_argument("--omarchy", type=Path, default=Path("/usr/share/omarchy"))
    args = parser.parse_args()
    if os.getuid() == 0 or not os.environ.get("WAYLAND_DISPLAY"):
        parser.error("Run as the desktop user in an unlocked Wayland session.")
    source = args.omarchy / "shell/plugins/services/idle"
    content = (source / "Service.qml").read_text()
    for old in ('import qs.Commons\n', '  ShellIpc {', 'Quickshell.env("HOME")', '"omarchy-system-lock"', '"omarchy-system-wake"'):
        if content.count(old) != 1:
            parser.error("The installed idle service differs from the reviewed fixture.")
    with tempfile.TemporaryDirectory(prefix="apollo-idle-regression-") as directory:
        root = Path(directory)
        fixture_home = root / "fixture-home"
        fixture_home.mkdir(mode=0o700)
        content = content.replace('import qs.Commons\n', '').replace('  ShellIpc {', '  IpcHandler {')
        content = content.replace('Quickshell.env("HOME")', json.dumps(str(root / "fixture-home")))
        content = content.replace('"omarchy-system-lock"', '"true"').replace('"omarchy-system-wake"', '"true"')
        (root / "Service.qml").write_text(content)
        (root / "IdleModel.js").write_bytes((source / "IdleModel.js").read_bytes())
        (root / "shell.qml").write_text('''
import QtQuick
import Quickshell
ShellRoot {
 id: harness
 property var service: null
 QtObject {id: stub; property var shellConfig: ({idle:{screensaver:0,lock:0}})}
 Item {id: host; visible:false}
 Component.onCompleted: {
  var component=Qt.createComponent('Service.qml', Component.PreferSynchronous);
  service=component.createObject(host);
  if (!service) {console.log('APOLLO_IDLE_FIXTURE_ERROR');Qt.quit();return}
  service.shell=stub;
 }
 Timer {interval:1000;running:true;onTriggered: {stub.shellConfig={idle:{screensaver:0,lock:5}}}}
 Timer {interval:9000;running:true;onTriggered: {
  console.log('APOLLO_IDLE_RESULT '+service.statusJson());Qt.quit();
 }}
}
''')
        environment = dict(os.environ, HOME=str(fixture_home))
        environment["QT_LOGGING_RULES"] = environment.get("QT_LOGGING_RULES", "") + "\nquickshell.wayland.idle_notify.debug=true"
        process = subprocess.Popen([args.binary, "-p", str(root / "shell.qml")], env=environment,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, start_new_session=True)
        try:
            output, _ = process.communicate(timeout=16)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.communicate()
            raise SystemExit("Idle regression timed out; no desktop lock was requested.")
        records = [line.split("APOLLO_IDLE_RESULT ", 1)[1] for line in output.splitlines() if "APOLLO_IDLE_RESULT " in line]
        if process.returncode or not records:
            raise SystemExit("The isolated idle fixture did not finish successfully.")
        state = json.loads(records[-1])
        result = {
            "configured_seconds": state["lock"],
            "compositor_sent_idle": "has been marked idle" in output,
            "idle_notification_observed": state["idle"],
            "fixture_action_completed": state["lastEvent"] == "process-exit: lock exitCode=0 status=0",
            "real_lock_or_wake_requested": False,
            "owner_preferences_or_pin_read": False,
            "physical_wake_and_pin_tested": False,
        }
        print(json.dumps(result, indent=2))
        if result["configured_seconds"] != 5 or not result["compositor_sent_idle"] or not result["idle_notification_observed"] or not result["fixture_action_completed"]:
            raise SystemExit("Idle replacement regression failed; interaction during the observation can also prevent idling.")


if __name__ == "__main__":
    main()
