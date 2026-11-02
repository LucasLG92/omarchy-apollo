#!/usr/bin/python3
# SPDX-License-Identifier: MIT
"""Show the trusted SIM continuation as soon as the authenticated display exists.

Status checks belong inside the one window, not in a second launcher wait.
No credentials, subscriber properties, user themes or user environment are read.
"""
from pathlib import Path
import os
import resource
import stat
import subprocess
import time


def owner_display(folder=Path('/run/user/1000')):
    if not folder.is_dir():
        return None
    info = folder.stat()
    if info.st_uid != 1000 or info.st_mode & 0o077:
        return None
    sockets = [p for p in folder.glob('wayland-*')
               if p.is_socket() and p.stat().st_uid == 1000]
    return sockets[0] if len(sockets) == 1 else None


def wait_for_owner_display(run_users=Path('/run/user')):
    """Filesystem events avoid periodic wakeups while waiting at the greeter."""
    from gi.repository import Gio, GLib
    loop = GLib.MainLoop()
    monitors = []
    state = {'display': None, 'owner_inode': None, 'owner_monitor': None}

    def refresh(*_):
        folder = run_users / '1000'
        try:
            info = folder.stat()
            inode = info.st_dev, info.st_ino
            if info.st_uid == 1000 and not info.st_mode & 0o077 and inode != state['owner_inode']:
                if state['owner_monitor'] is not None:
                    state['owner_monitor'].cancel()
                monitor = Gio.File.new_for_path(str(folder)).monitor_directory(Gio.FileMonitorFlags.NONE, None)
                monitor.connect('changed', refresh)
                state.update(owner_inode=inode, owner_monitor=monitor)
                monitors.append(monitor)
            state['display'] = owner_display(folder)
        except (FileNotFoundError, GLib.Error):
            state['display'] = None
        if state['display'] is not None:
            loop.quit()

    parent = Gio.File.new_for_path(str(run_users)).monitor_directory(Gio.FileMonitorFlags.NONE, None)
    parent.connect('changed', refresh)
    monitors.append(parent)
    refresh()
    try:
        if state['display'] is None:
            loop.run()
        assert state['display'] is not None
        return state['display']
    finally:
        for monitor in monitors:
            monitor.cancel()


def main():
    assert os.geteuid() == 0
    assert Path('/etc/apollo/native-root-v1').is_file()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    os.umask(0o077)
    while not Path('/var/lib/apollo/owner-ready').is_file():
        time.sleep(1)
    while subprocess.run(['/usr/bin/systemctl', 'is-active', '--quiet',
                          'apollo-owner-setup.service'],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
        time.sleep(1)
    display = wait_for_owner_display()
    runtime = Path('/run/apollo-sim-ui')
    runtime.mkdir(mode=0o700, exist_ok=True)
    info = runtime.lstat()
    assert stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o077
    environment = {
        'PATH': '/usr/bin:/bin', 'HOME': str(runtime), 'LANG': 'es_ES.UTF-8',
        'XDG_RUNTIME_DIR': str(runtime), 'WAYLAND_DISPLAY': str(display),
        'GDK_BACKEND': 'wayland', 'GTK_USE_PORTAL': '0',
        'DBUS_SESSION_BUS_ADDRESS': 'unix:path=' + str(runtime / 'no-session-bus'),
    }
    os.execve('/usr/bin/apollo-sim-unlock', ['apollo-sim-unlock'], environment)


if __name__ == '__main__':
    main()
