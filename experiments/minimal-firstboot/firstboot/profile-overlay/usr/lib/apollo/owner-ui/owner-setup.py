#!/usr/bin/python3
# SPDX-License-Identifier: MIT
"""Local account setup/change. No secret arguments, files, debug or logging."""
from pathlib import Path
from contextlib import contextmanager
import fcntl
import grp
import os
import pwd
import re
import resource
import stat
import subprocess
import sys
import threading

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gdk, Gio, GLib, Gtk, Pango

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from owner_account import resolve_owner
from owner_mode import set_mode
SAFE_ENV = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'}
MIN_LENGTH, MAX_LENGTH = 8, 128


def valid_credential(value, editor):
    if not isinstance(value, str) or editor not in ('pin', 'password'):
        return False
    if not MIN_LENGTH <= len(value) <= MAX_LENGTH or any(c in value for c in '\0\r\n'):
        return False
    try:
        value.encode('utf-8', 'strict')
    except UnicodeError:
        return False
    return editor == 'password' or re.fullmatch('[0-9]+', value) is not None


def valid_admin_rule_text(text):
    lines = [' '.join(line.split('#', 1)[0].split()) for line in text.splitlines()]
    return [line for line in lines if line] == ['%wheel ALL=(ALL:ALL) ALL']


def root_file(path):
    info = path.lstat()
    return stat.S_ISREG(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022


def root_directory(path):
    info = path.lstat()
    return stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022


class SystemOperations:
    """Fixed production sink. Tests replace this whole interface in memory."""
    def euid(self):
        return os.geteuid()

    @contextmanager
    def transaction(self):
        directory = Path('/run/apollo-owner-ui')
        directory.mkdir(mode=0o700, exist_ok=True)
        info = directory.lstat()
        if not root_directory(directory) or info.st_mode & 0o077:
            raise PermissionError('Private runtime is unavailable')
        fd = os.open(directory / 'credential.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o077:
                raise PermissionError('Private lock is unavailable')
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
        finally:
            os.close(fd)

    def native_ready(self):
        return root_file(Path('/etc/apollo/native-root-v1'))

    def owner_ready(self):
        path = Path('/var/lib/apollo/owner-ready')
        if not path.exists() and not path.is_symlink():
            return False
        if not root_file(path):
            raise PermissionError('Owner readiness is invalid')
        return True

    def admin_ready(self):
        record = resolve_owner()
        account = pwd.getpwnam(record['name'])
        wheel = grp.getgrnam('wheel').gr_gid
        if wheel not in os.getgrouplist(record['name'], account.pw_gid):
            return False
        rule = Path('/etc/sudoers.d/20-apollo-owner')
        if not root_directory(rule.parent) or not root_file(rule):
            return False
        if not valid_admin_rule_text(rule.read_text(encoding='utf-8')):
            return False
        package = subprocess.run(['/usr/bin/pacman', '-Qqo', str(rule)], env=SAFE_ENV,
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5)
        return package.returncode == 0 and package.stdout.strip() == b'apollo-native-profile'

    def change_account_credential(self, value):
        # chpasswd splits the fixed account from the rest of the line at the
        # first colon; NUL/CR/LF have already been rejected. No crypt bypass.
        payload = (resolve_owner()['name'] + ':' + value + '\n').encode('utf-8', 'strict')
        try:
            result = subprocess.run(['/usr/bin/chpasswd'], input=payload, env=SAFE_ENV,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=25)
            return result.returncode == 0
        finally:
            payload = None


    def sync_credential_mode(self, editor):
        return set_mode(resolve_owner(), editor)


class CredentialBackend:
    def __init__(self, mode, operations=None):
        if mode != 'change':
            raise ValueError('Unknown provisioning mode')
        self.mode, self.operations = mode, operations if operations is not None else SystemOperations()
        self.editor_sync_pending = False

    def apply(self, value, editor):
        if not valid_credential(value, editor) or self.operations.euid() != 0:
            return False
        with self.operations.transaction():
            if not self.operations.native_ready() or not self.operations.admin_ready():
                return False
            ready = self.operations.owner_ready()
            if not ready:
                return False
            if not self.operations.change_account_credential(value):
                return False
            try:
                self.editor_sync_pending = not self.operations.sync_credential_mode(editor)
            except Exception:
                self.editor_sync_pending = True
            # PAM already succeeded. Never imply that the old credential still
            # works if this non-secret UI preference cannot be synchronized.
            return True


class PinField(Gtk.Button):
    """No Gtk.Editable/IME surface in numeric mode."""
    def __init__(self, placeholder):
        super().__init__()
        self.placeholder = placeholder
        self.buffer = Gtk.PasswordEntryBuffer()
        # Keep one overflow character so an oversized paste is rejected,
        # rather than silently saved as a valid truncated 128-char secret.
        self.buffer.set_max_length(MAX_LENGTH + 1)
        self.set_size_request(-1, 52)
        self.display = Gtk.Label(label=placeholder, ellipsize=Pango.EllipsizeMode.END)
        self.display.set_max_width_chars(28)
        self.set_child(self.display)
        self.add_css_class('omarchy-pin-field')

    def get_buffer(self):
        return self.buffer

    def get_text(self):
        return self.buffer.get_text()

    def set_text(self, value):
        self.buffer.set_text(value, -1)
        length = self.buffer.get_length()
        self.display.set_text(('●' * min(length, 24) + ('…' if length > 24 else '')) if length else self.placeholder)


def password_field(placeholder):
    entry = Gtk.PasswordEntry(placeholder_text=placeholder, show_peek_icon=False)
    entry.set_size_request(-1, 52)
    entry.set_enable_undo(False)
    delegate = Gtk.Editable.get_delegate(entry)
    if not isinstance(delegate, Gtk.Text) or not isinstance(delegate.get_buffer(), Gtk.PasswordEntryBuffer):
        raise RuntimeError('Protected password field is unavailable')
    delegate.get_buffer().set_max_length(MAX_LENGTH + 1)
    delegate.set_input_purpose(Gtk.InputPurpose.PASSWORD)
    delegate.set_input_hints(Gtk.InputHints.PRIVATE | Gtk.InputHints.NO_SPELLCHECK)
    return entry


class OwnerSetup(Adw.Application):
    def __init__(self, mode='change', backend=None):
        super().__init__(application_id='org.apollo.OwnerSetup', flags=Gio.ApplicationFlags.NON_UNIQUE)
        self.mode = mode
        self.backend = backend if backend is not None else CredentialBackend(mode)
        self.busy = self.completed = False
        self.editor = 'pin' if mode == 'initial' else 'password'
        self.connect('activate', self.activate_window)

    def activate_window(self, *_):
        if self.get_active_window():
            self.get_active_window().present()
            return
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        css = Gtk.CssProvider()
        css.load_from_path(str(HERE / 'omarchy.css'))
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        Gtk.Settings.get_default().set_property('gtk-entry-password-hint-timeout', 0)
        self.win = Adw.ApplicationWindow(application=self, title='Tu cuenta Omarchy' if self.mode == 'initial' else 'Cambiar contraseña', default_width=360, default_height=760)
        self.win.add_css_class('apollo-omarchy')
        self.win.connect('close-request', self.close_requested)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=20, margin_bottom=20, margin_start=20, margin_end=20)
        box.set_valign(Gtk.Align.CENTER)
        logo = Gtk.Picture.new_for_filename(str(HERE / 'assets/logo.png'))
        logo.set_can_shrink(True)
        logo.set_size_request(-1, 48)
        box.append(logo)
        heading = Gtk.Label(label='Tu cuenta Omarchy' if self.mode == 'initial' else 'Cambiar contraseña')
        heading.add_css_class('omarchy-title')
        box.append(heading)
        box.append(Gtk.Label(label='Tu cuenta puede administrar el teléfono. Usa la misma credencial para iniciar sesión y con sudo. Es distinta del PIN de la SIM.', wrap=True))
        choices = Gtk.Box(spacing=8, homogeneous=True)
        self.choices = {}
        for editor, label in (('pin', 'PIN numérico'), ('password', 'Contraseña')):
            button = Gtk.ToggleButton(label=label)
            if self.choices:
                button.set_group(self.choices['pin'])
            button.connect('toggled', self.editor_toggled, editor)
            choices.append(button)
            self.choices[editor] = button
        box.append(choices)
        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.NONE)
        pin_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.pin_entries = [PinField(label) for label in ('PIN nuevo · 8 a 128 cifras', 'Repite el PIN')]
        for entry in self.pin_entries:
            entry.connect('clicked', self.select_field)
            pin_box.append(entry)
        self.active = self.pin_entries[0]
        self.active.add_css_class('omarchy-pin-selected')
        self.stack.add_named(pin_box, 'pin')
        password_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.password_entries = [password_field(label) for label in ('Contraseña nueva · 8 a 128 caracteres', 'Repite la contraseña')]
        for entry in self.password_entries:
            password_box.append(entry)
        self.stack.add_named(password_box, 'password')
        box.append(self.stack)
        keypad = Gtk.Grid(column_homogeneous=True, column_spacing=8, row_spacing=8)
        for i, label in enumerate(('1', '2', '3', '4', '5', '6', '7', '8', '9', 'Borrar', '0', 'Vaciar')):
            button = Gtk.Button(label=label)
            button.set_focus_on_click(False)
            button.set_size_request(-1, 48)
            button.add_css_class('omarchy-key')
            button.connect('clicked', self.digit, label)
            keypad.attach(button, i % 3, i // 3, 1, 1)
        self.keypad = keypad
        box.append(keypad)
        self.status = Gtk.Label(label='Se guardará solo en este teléfono. Se conservan todos los caracteres, incluidos los espacios.', wrap=True)
        box.append(self.status)
        self.save = Gtk.Button(label='Guardar credencial')
        self.save.add_css_class('omarchy-primary')
        self.save.set_size_request(-1, 52)
        self.save.connect('clicked', self.submit)
        box.append(self.save)
        self.close = Gtk.Button(label='Cancelar')
        self.close.connect('clicked', lambda *_: self.win.close())
        box.append(self.close)
        clamp = Adw.Clamp(maximum_size=400, tightening_threshold=360)
        clamp.set_child(box)
        clamp.set_vexpand(True)
        scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        scroll.set_child(clamp)
        self.win.set_content(scroll)
        self.set_editor(self.editor)
        self.choices[self.editor].set_active(True)
        self.win.fullscreen()
        self.win.present()
        self.win.set_focus(self.choices[self.editor])

    def all_entries(self):
        return self.pin_entries + self.password_entries

    def clear_fields(self):
        for entry in self.all_entries():
            entry.set_text('')

    def editor_toggled(self, button, editor):
        if button.get_active() and hasattr(self, 'stack') and not self.busy and not self.completed:
            self.set_editor(editor)

    def set_editor(self, editor):
        if editor not in ('pin', 'password') or self.busy or self.completed:
            return
        self.win.set_focus(None)
        self.clear_fields()
        self.editor = editor
        for entry in self.pin_entries:
            entry.set_sensitive(editor == 'pin')
            entry.set_can_focus(editor == 'pin')
        for entry in self.password_entries:
            entry.set_sensitive(editor == 'password')
            entry.set_can_focus(editor == 'password')
        self.stack.set_visible_child_name(editor)
        self.keypad.set_visible(editor == 'pin')
        self.keypad.set_sensitive(editor == 'pin')

    def select_field(self, entry, *_):
        if self.busy or self.completed or self.editor != 'pin':
            return
        self.active.remove_css_class('omarchy-pin-selected')
        self.active = entry
        self.active.add_css_class('omarchy-pin-selected')

    def digit(self, _button, label):
        if self.busy or self.completed or self.editor != 'pin':
            return
        value = self.active.get_text()
        if label == 'Borrar':
            self.active.set_text(value[:-1])
        elif label == 'Vaciar':
            self.active.set_text('')
        elif label in '0123456789' and len(label) == 1 and len(value) < MAX_LENGTH + 1:
            self.active.set_text(value + label)

    def close_requested(self, *_):
        if self.busy:
            self.status.set_text('Espera mientras se guarda la credencial.')
            return True
        self.clear_fields()
        return False

    def submit(self, *_):
        if self.busy or self.completed:
            return
        entries = self.pin_entries if self.editor == 'pin' else self.password_entries
        first, second = (entry.get_text() for entry in entries)
        if not valid_credential(first, self.editor):
            self.status.set_text('Usa entre 8 y 128 cifras.' if self.editor == 'pin' else 'Usa entre 8 y 128 caracteres, sin saltos de línea ni caracteres nulos.')
            return
        if first != second:
            self.status.set_text('Las credenciales no coinciden.')
            return
        self.busy = True
        editor = self.editor
        self.win.set_focus(None)
        self.clear_fields()
        self.save.set_sensitive(False)
        self.keypad.set_sensitive(False)
        for control in self.all_entries() + list(self.choices.values()):
            control.set_sensitive(False)
        self.status.set_text('Guardando la credencial en el teléfono…')
        threading.Thread(target=self.worker, args=(first, editor), daemon=True).start()
        first = second = None

    def worker(self, value, editor):
        try:
            success = self.backend.apply(value, editor)
        except Exception:
            success = False
        finally:
            value = None
        GLib.idle_add(self.finished, success)

    def finished(self, success):
        self.busy = False
        if success:
            self.completed = True
            self.clear_fields()
            self.status.set_text('Credencial guardada. El teclado de bloqueo necesita revisión.' if self.backend.editor_sync_pending else 'Credencial guardada. Úsala al iniciar sesión y para autorizar cambios.')
            self.save.set_visible(False)
            self.close.set_visible(self.backend.editor_sync_pending)
            if not self.backend.editor_sync_pending:
                GLib.timeout_add(600, self.close_after_success)
        else:
            self.status.set_text('No se ha podido completar la operación. Revisa la configuración antes de intentarlo de nuevo.')
            self.save.set_sensitive(True)
            for button in self.choices.values():
                button.set_sensitive(True)
            self.set_editor(self.editor)
        return GLib.SOURCE_REMOVE

    def close_after_success(self):
        if self.completed:
            self.win.close()
            self.quit()
        return GLib.SOURCE_REMOVE


def main():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    os.umask(0o077)
    if os.geteuid() != 0:
        return 1
    # Fixed privileged launcher supplies this non-secret flag. A normal user
    # cannot bypass root/authentication by invoking the source with a flag.
    if sys.argv[1:] != ['--change']:
        return 1
    resolve_owner()
    mode = 'change'
    return OwnerSetup(mode).run([sys.argv[0]])


if __name__ == '__main__':
    sys.exit(main())
