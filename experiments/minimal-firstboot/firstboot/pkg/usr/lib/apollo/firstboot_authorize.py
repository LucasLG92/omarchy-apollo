# SPDX-License-Identifier: MIT
from pathlib import Path
import os
import pwd

from owner_account import protected


class Denied(Exception):
    pass


def greeter_properties_match(properties, uid):
    return (properties.get('User', (None,))[0] == uid and properties.get('Active') is True
            and properties.get('Remote') is False and properties.get('Class') == 'greeter'
            and properties.get('Type') in ('wayland', 'x11')
            and properties.get('Seat', ('',))[0] == 'seat0')


def unpack(value):
    return value.unpack() if hasattr(value, 'unpack') else value


class SenderGuard:
    def __init__(self, connection):
        from gi.repository import Gio, GLib
        self.bus, self.Gio, self.GLib = connection, Gio, GLib
        self.sddm_uid = pwd.getpwnam('sddm').pw_uid
        if self.sddm_uid == 0 or self.sddm_uid >= 1000:
            raise Denied()

    def _credentials(self, sender):
        if not isinstance(sender, str) or not sender.startswith(':'):
            raise Denied()
        data = self.bus.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus',
                                  'GetConnectionCredentials', self.GLib.Variant('(s)', (sender,)),
                                  self.GLib.VariantType.new('(a{sv})'), self.Gio.DBusCallFlags.NONE, 2000, None).unpack()[0]
        uid, pid = unpack(data.get('UnixUserID')), unpack(data.get('ProcessID'))
        if type(uid) is not int or type(pid) is not int or uid != self.sddm_uid or pid <= 0:
            raise Denied()
        return uid, pid

    def check(self, sender, write=False):
        uid, pid = self._credentials(sender)
        executable = Path(os.readlink('/proc/' + str(pid) + '/exe'))
        if str(executable) not in ('/usr/bin/sddm-greeter-qt6', '/usr/bin/sddm-greeter'):
            raise Denied()
        protected(executable)
        if write:
            session = self.bus.call_sync('org.freedesktop.login1', '/org/freedesktop/login1',
                                         'org.freedesktop.login1.Manager', 'GetSessionByPID',
                                         self.GLib.Variant('(u)', (pid,)), self.GLib.VariantType.new('(o)'),
                                         self.Gio.DBusCallFlags.NONE, 2000, None).unpack()[0]
            raw = self.bus.call_sync('org.freedesktop.login1', session, 'org.freedesktop.DBus.Properties',
                                    'GetAll', self.GLib.Variant('(s)', ('org.freedesktop.login1.Session',)),
                                    self.GLib.VariantType.new('(a{sv})'), self.Gio.DBusCallFlags.NONE, 2000, None).unpack()[0]
            properties = {key: unpack(value) for key, value in raw.items()}
            if not greeter_properties_match(properties, uid):
                raise Denied()
        # Requery the live unique bus connection after PID/session checks.
        if self._credentials(sender) != (uid, pid):
            raise Denied()

