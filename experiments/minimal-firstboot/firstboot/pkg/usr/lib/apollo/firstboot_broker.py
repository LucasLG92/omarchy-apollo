# SPDX-License-Identifier: MIT
import threading
import json

from firstboot_authorize import Denied
from firstboot_engine import FirstbootError

BUS_NAME = 'org.apollo.OwnerProvisioning1'
OBJECT = '/org/apollo/OwnerProvisioning1'
INTERFACE = BUS_NAME
XML = '''<node><interface name="org.apollo.OwnerProvisioning1">
<method name="GetState"><arg direction="out" type="s" name="state"/></method>
<method name="Configure"><arg direction="in" type="s" name="username"/>
<arg direction="in" type="s" name="credential"/><arg direction="out" type="s" name="result"/></method>
<method name="ConfigureProfile"><arg direction="in" type="s" name="username"/>
<arg direction="in" type="s" name="credential"/><arg direction="in" type="s" name="profile"/>
<arg direction="out" type="s" name="result"/></method>
</interface></node>'''


def export(connection, engine, guard):
    """Register the same fixed API in production and on an isolated test bus."""
    from gi.repository import Gio, GLib
    def reply(invocation, value):
        invocation.return_value(GLib.Variant('(s)', (value,)))
    broker = Broker(engine, guard, reply, GLib.idle_add, GLib.timeout_add)
    info = Gio.DBusNodeInfo.new_for_xml(XML).interfaces[0]
    def call(_connection, sender, _path, _interface, method, parameters, invocation):
        if method == 'GetState':
            broker.get_state(sender, invocation)
        elif method == 'Configure':
            name, credential = parameters.unpack()
            broker.configure(sender, name, credential, invocation)
            credential = parameters = None
        elif method == 'ConfigureProfile':
            name, credential, profile = parameters.unpack()
            broker.configure_profile(sender, name, credential, profile, invocation)
            credential = parameters = None
        else:
            invocation.return_dbus_error(INTERFACE + '.Denied', 'DENIED')
    registration = connection.register_object(OBJECT, info, call, None, None)
    return registration, broker, info, call


class Broker:
    def __init__(self, engine, guard, reply, idle, timer, start_worker=None):
        self.engine, self.guard, self.reply, self.idle, self.timer = engine, guard, reply, idle, timer
        self.start_worker = start_worker or (lambda fn: threading.Thread(target=fn, daemon=True).start())
        self.pending = False

    def get_state(self, sender, invocation):
        try:
            # Read-only enum for the real SDDM executable. No private account
            # identity, paths or secrets; write requests require full logind.
            self.guard.check(sender, write=False)
            code = self.engine.state()
        except Denied:
            code = 'denied'
        except Exception:
            code = 'needs-admin'
        self.reply(invocation, code)

    def configure_profile(self, sender, username, credential, text, invocation):
        try:
            self.guard.check(sender, write=True)
        except Exception:
            self.reply(invocation, 'DENIED')
            return
        try:
            if not isinstance(text, str) or len(text.encode('utf-8')) > 8192: raise ValueError()
            preferences = None if text == '' and username == '' and credential == '' else json.loads(text)
            if preferences is not None:
                from firstboot_profile import validate_profile
                preferences = validate_profile(preferences)
        except Exception:
            self.reply(invocation, 'INVALID_PROFILE')
            return
        self.configure(sender, username, credential, invocation, preferences)

    def configure(self, sender, username, credential, invocation, preferences=None):
        try:
            self.guard.check(sender, write=True)
        except Exception:
            self.reply(invocation, 'DENIED')
            return
        if self.pending:
            self.reply(invocation, 'BUSY')
            return
        if not isinstance(username, str) or len(username) > 32:
            self.reply(invocation, 'INVALID_NAME')
            return
        if not isinstance(credential, str) or len(credential) > 128:
            self.reply(invocation, 'INVALID_PASSWORD')
            return
        self.pending = True

        def worker():
            nonlocal credential
            try:
                if preferences is None:
                    code = self.engine.configure(username, credential, lambda: self.guard.check(sender, write=True))
                else:
                    code = self.engine.configure(username, credential, lambda: self.guard.check(sender, write=True), preferences=preferences)
            except Denied:
                code = 'DENIED'
            except FirstbootError as error:
                code = error.code
            except Exception:
                code = 'NEEDS_ADMIN'
            finally:
                credential = None
            self.idle(self._complete, invocation, code)
        self.start_worker(worker)

    def _complete(self, invocation, code):
        self.pending = False
        # Reply and frontend clear happen before any display-manager action.
        self.reply(invocation, code)
        if code == 'configured':
            self.timer(700, self._refresh)
        return False

    def _refresh(self):
        try:
            self.engine.ops.restart_greeter_if_no_owner()
        except Exception:
            pass
        return False

