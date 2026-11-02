#!/usr/bin/python3
# SPDX-License-Identifier: MIT
"""Omarchy touch SIM PIN entry. No PIN arguments, environment, files or logs.

Based on the MIT Apollo SendPin application exported in outputs, SHA256
0673dd072dd5722bed9c4a3bab3f5f125048fc3b5a2f2e338a2fea12a7726828.
This is an isolated review candidate; it does not change system policy.
"""
from pathlib import Path
import re
import resource
import sys
import threading
import xml.etree.ElementTree as ET
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gdk, Gio, GLib, Gtk, Pango
from sim_state import BUS, MODEM, read_snapshot, classify, inventory_text, card_count

HERE = Path(__file__).resolve().parent


class PinField(Gtk.Button):
    """A protected touch buffer without GtkEditable/IME/OSK or undo surface."""
    def __init__(self, placeholder):
        super().__init__(hexpand=True)
        self.placeholder = placeholder
        self.buffer = Gtk.PasswordEntryBuffer()
        self.buffer.set_max_length(8)
        self.display = Gtk.Label(label=placeholder, wrap=True, justify=Gtk.Justification.CENTER)
        self.display.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.display.set_max_width_chars(28)
        self.display.set_selectable(False)
        self.set_child(self.display)
        self.set_size_request(-1, 52)
        self.add_css_class('omarchy-pin-field')
    def get_buffer(self): return self.buffer
    def get_text(self): return self.buffer.get_text()
    def set_text(self, value):
        self.buffer.set_text(value, -1)
        self.display.set_text('●' * self.buffer.get_length() if self.buffer.get_length() else self.placeholder)


class SimUnlock(Adw.Application):
    def __init__(self):
        super().__init__(application_id='org.apollo.SimUnlock', flags=Gio.ApplicationFlags.NON_UNIQUE)
        self.connect('activate', self.activate_window)
        self.bus = None
        self.modem = None
        self.snapshot = None
        self.busy = self.ready = self.reading = False
        self.send_blocked = self.send_consumed = self.closed = False
        self.generation = 0

    @staticmethod
    def get(bus, path, interface, prop):
        result = bus.call_sync(BUS, path, 'org.freedesktop.DBus.Properties', 'Get',
            GLib.Variant('(ss)', (interface, prop)), GLib.VariantType.new('(v)'),
            Gio.DBusCallFlags.NONE, 3000, None).unpack()[0]
        return result.unpack() if isinstance(result, GLib.Variant) else result

    def activate_window(self, *_):
        if self.get_active_window():
            self.get_active_window().present()
            return
        self.closed = False
        self._closing = False
        self._status_source = 0
        self._close_source = 0
        self._confirm_deadline = None
        self._startup_loading = True
        self._startup_deadline = GLib.get_monotonic_time() + 90 * 1000000
        self._layout_size = None
        self.win = Adw.ApplicationWindow(application=self, title='Omarchy',
                                         default_width=432, default_height=960)
        self.win.set_decorated(False)
        self.win.add_css_class('apollo-omarchy')
        self.win.add_css_class('apollo-access-continuation')
        self.win.connect('close-request', self.close_requested)
        self.win.connect('close-request', self._stop_stage_sources)
        self.win.connect('realize', self._connect_access_layout)
        self.css = Gtk.CssProvider()
        self.css.load_from_path(str(HERE / 'omarchy.css'))
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), self.css,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.get_style_manager().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        self.canvas = Gtk.Fixed(hexpand=True, vexpand=True)
        # The stage follows the display; its previous child positions must not
        # become minimum window dimensions when switching orientation.
        self.frame = Gtk.Overlay()
        self.frame.set_child(Gtk.Box(hexpand=True, vexpand=True))
        self.frame.add_overlay(self.canvas)
        self.frame.set_measure_overlay(self.canvas, False)
        self.frame.set_clip_overlay(self.canvas, True)
        self.logo = Gtk.Picture.new_for_filename(str(HERE / 'assets' / 'logo.png'))
        self.logo.set_can_shrink(True)
        self.logo.set_content_fit(Gtk.ContentFit.CONTAIN)
        self.logo.update_property([Gtk.AccessibleProperty.LABEL], ['Omarchy'])
        self.progress = Gtk.ProgressBar(show_text=False)
        self.progress.add_css_class('access-progress')
        self.progress.set_fraction(0.25)
        self.inventory = Gtk.Label(label='Preparando la SIM', justify=Gtk.Justification.CENTER)
        self.inventory.set_ellipsize(Pango.EllipsizeMode.END)
        self.inventory.add_css_class('omarchy-inventory')
        self.attempts = Gtk.Label(label='Continuar al teléfono', justify=Gtk.Justification.CENTER)
        self.attempts.set_ellipsize(Pango.EllipsizeMode.END)
        self.attempts.add_css_class('access-caption')
        self.entry = PinField('PIN de la SIM')
        self.entry.update_property([Gtk.AccessibleProperty.LABEL], ['PIN de la SIM principal'])
        self.entry.connect('clicked', lambda *_: self.entry.grab_focus())
        self.status = Gtk.Label(label='Comprobando el estado de la SIM…', wrap=True,
                                justify=Gtk.Justification.CENTER)
        self.status.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.status.set_ellipsize(Pango.EllipsizeMode.END)
        self.status.set_lines(4)
        self.status.set_valign(Gtk.Align.START)
        self.status.add_css_class('omarchy-status')
        self.spinner = Gtk.Spinner()
        self.pinsection = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.keypad = Gtk.Grid(column_spacing=8, row_spacing=8, column_homogeneous=True,
                               row_homogeneous=True)
        for index, label in enumerate(('1', '2', '3', '4', '5', '6', '7', '8', '9', 'Borrar', '0', 'Vaciar')):
            key = Gtk.Button(label=label, hexpand=True)
            key.set_focus_on_click(False)
            key.set_size_request(-1, 44)
            key.add_css_class('omarchy-key')
            key.connect('clicked', self.key_pressed, label)
            self.keypad.attach(key, index % 3, index // 3, 1, 1)
        self.pinsection.append(self.keypad)
        self.button = Gtk.Button(label='Continuar')
        self.button.add_css_class('omarchy-primary')
        self.button.set_size_request(-1, 48)
        self.button.connect('clicked', self.submit)
        self.pinsection.append(self.button)
        self.pinsection.set_visible(False)
        self.pinsection.connect('notify::visible',
            lambda widget, *_: self.entry.grab_focus() if widget.get_visible() else None)
        self.reload = Gtk.Button(label='Comprobar de nuevo')
        self.reload.set_size_request(-1, 44)
        self.reload.connect('clicked', self.discover)
        self.reload.set_visible(False)
        self.cancel = Gtk.Button(label='Más tarde')
        self.cancel.set_size_request(-1, 44)
        self.cancel.add_css_class('access-later')
        self.cancel.connect('clicked', lambda *_: self.win.close())
        for widget in (self.logo, self.progress, self.inventory, self.attempts, self.entry,
                       self.status, self.spinner, self.pinsection, self.reload, self.cancel):
            self.canvas.put(widget, 0, 0)
        self.status.connect('notify::label', self._sync_access_stage)
        self.win.set_content(self.frame)
        self.keys = Gtk.EventControllerKey()
        self.keys.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        self.keys.connect('key-pressed', self.hardware_key)
        self.win.add_controller(self.keys)
        self.win.fullscreen()
        self.win.present()
        self.discover()

    def _connect_access_layout(self, *_):
        surface = self.win.get_surface()
        if surface is not None:
            surface.connect('layout', self._layout_access)
            self._layout_access(surface, surface.get_width(), surface.get_height())

    def _layout_access(self, surface, width, height):
        width, height = int(width), int(height)
        if width < 240 or height < 320 or self._layout_size == (width, height):
            return
        self._layout_size = (width, height)
        landscape = width > height
        compact = not landscape and height < 620
        keyboard_width = min(336, int(width * 0.48) - 32) if landscape else min(336, width - 48)
        keyboard_width = max(240, keyboard_width)
        if landscape:
            left_width = width // 2
            centre_x = left_width / 2
            key_x = left_width + (width - left_width - keyboard_width) / 2
            key_y = max(12, (height - 316) / 2)
            cancel_y = key_y + 272
            logo_width = min(346, left_width - 40)
            field_width = min(304, left_width - 40)
            field_height = 48
        else:
            centre_x = width / 2
            key_x = (width - keyboard_width) / 2
            cancel_y = height - (8 if compact else 16) - 44
            key_y = cancel_y - (8 if compact else 12) - 260
            logo_width = min(220 if compact else 346, width - 48)
            field_width = min(304, width - 48)
            field_height = 44 if compact else 48
        logo_height = round(logo_width * 169 / 784)
        composition_height = logo_height + 40 + field_height
        logo_y = max(12, ((height if landscape else key_y) - composition_height) / 2)
        field_y = logo_y + logo_height + 40
        status_y = field_y + field_height + 8
        status_room = (height - 16 - status_y) if landscape else (key_y - 8 - status_y)
        status_height = max(16, min(72, status_room - (52 if landscape else 0)))
        def place(widget, x, y, w, h):
            widget.set_size_request(max(1, int(w)), max(1, int(h)))
            self.canvas.move(widget, float(round(x)), float(round(y)))
        place(self.logo, centre_x - logo_width / 2, logo_y, logo_width, logo_height)
        place(self.progress, centre_x - logo_width / 2, logo_y + logo_height + 4, logo_width, 2)
        place(self.inventory, centre_x - field_width / 2, logo_y + logo_height + 10, field_width, 14)
        place(self.attempts, centre_x - field_width / 2, logo_y + logo_height + 24, field_width, 14)
        place(self.entry, centre_x - field_width / 2, field_y, field_width, field_height)
        place(self.spinner, centre_x + field_width / 2 - 28, field_y + (field_height - 20) / 2, 20, 20)
        place(self.status, centre_x - field_width / 2, status_y, field_width, status_height)
        place(self.reload, centre_x - field_width / 2, status_y + status_height + 8, field_width, 44)
        place(self.pinsection, key_x, key_y, keyboard_width, 260)
        place(self.cancel, key_x, cancel_y, keyboard_width, 44)
        self.status.set_lines(1 if compact else 3)

    def _stop_stage_sources(self, *_):
        if self.busy:
            return False
        for name in ('_status_source', '_close_source'):
            source = getattr(self, name, 0)
            if source:
                GLib.source_remove(source)
                setattr(self, name, 0)
        return False

    def _read_access_status_later(self):
        self._status_source = 0
        if self.closed or self._closing:
            return GLib.SOURCE_REMOVE
        if not self.busy and not self.reading:
            # Status refresh only. It never invokes submit() or SendPin.
            self.start_read(for_submit=False)
        return GLib.SOURCE_REMOVE

    def _close_confirmed_access(self):
        self._close_source = 0
        if not self.closed and not self.busy:
            self.win.close()
        return GLib.SOURCE_REMOVE

    def _sync_access_stage(self, *_):
        if self.closed or self._closing:
            return
        snapshot = self.snapshot
        now = GLib.get_monotonic_time()
        unlocked = snapshot is not None and snapshot.stable and (
            card_count(snapshot) == 0 or (snapshot.active is True and snapshot.lock in (1, 3, 5)))
        if unlocked and not self.busy and not self.reading:
            self._closing = True
            if self._status_source:
                GLib.source_remove(self._status_source)
                self._status_source = 0
            self.progress.set_fraction(1)
            self.reload.set_visible(False)
            self.status.set_text('Continuando a Omarchy…')
            self._close_source = GLib.timeout_add(250, self._close_confirmed_access)
            return
        if self.ready:
            self._startup_loading = False
        if snapshot is not None and snapshot.remaining is not None and snapshot.lock == 2:
            self.attempts.set_text('PIN de la SIM · ' + str(snapshot.remaining) + ' intentos')
        else:
            self.attempts.set_text('Acceso a la SIM')
        self.progress.set_fraction(0.75 if self.send_consumed or self.busy else 0.5 if self.ready else 0.25)
        waiting = self._startup_loading and not self.ready and now < self._startup_deadline
        if self.send_consumed and not self.send_blocked:
            if self._confirm_deadline is None:
                self._confirm_deadline = now + 15 * 1000000
            waiting = waiting or now < self._confirm_deadline
        self.reload.set_visible(not self.ready and not self.busy and not self.reading and not waiting)
        self.status.update_property([Gtk.AccessibleProperty.DESCRIPTION], [self.status.get_text()])
        if waiting and not self._status_source and not self.busy:
            self._status_source = GLib.timeout_add(1000, self._read_access_status_later)
        elif not waiting and self._status_source:
            # Once entry is ready, a queued startup read must not erase a PIN
            # the owner has just begun typing.
            GLib.source_remove(self._status_source)
            self._status_source = 0


    def hardware_key(self, controller, keyval, keycode, state):
        if state & (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.ALT_MASK | Gdk.ModifierType.SUPER_MASK):
            return False
        if keyval == Gdk.KEY_Escape:
            self.win.close()
            return True
        if self.busy or self.reading or not self.ready or self.win.get_focus() != self.entry:
            return False
        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            self.submit()
            return True
        if keyval == Gdk.KEY_BackSpace:
            self.key_pressed(None, 'Borrar')
            return True
        if keyval == Gdk.KEY_Delete:
            self.key_pressed(None, 'Vaciar')
            return True
        char = Gdk.keyval_to_unicode(keyval)
        if 48 <= char <= 57:
            self.key_pressed(None, chr(char))
            return True
        return False


    def close_requested(self, *_):
        if self.busy:
            self.status.set_text('Espera el resultado del PIN que ya se ha enviado.')
            return True
        self.closed = True
        self.generation += 1
        self.ready = False
        self.entry.set_text('')
        return False

    def set_controls(self, enabled):
        self.entry.set_sensitive(enabled)
        self.keypad.set_sensitive(enabled)
        self.button.set_sensitive(enabled)

    def discover(self, *_):
        self.start_read()

    def start_read(self, for_submit=False, prefix=''):
        if self.busy or self.reading or self.closed:
            return
        expected_sim = self.snapshot.current if for_submit and self.snapshot else None
        self.ready = False
        self.reading = True
        self.set_controls(False)
        self.reload.set_sensitive(False)
        self.spinner.set_visible(True)
        self.spinner.start()
        if not for_submit:
            self.entry.set_text('')
        self.status.set_text(prefix or 'Comprobando el estado de la SIM…')
        self.generation += 1
        generation = self.generation
        # The worker only reads allowlisted status. The PIN stays in GTK's
        # password buffer and is never copied into the worker or its arguments.
        def worker():
            try:
                bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
                tree = bus.call_sync(BUS, '/org/freedesktop/ModemManager1/Modem',
                    'org.freedesktop.DBus.Introspectable', 'Introspect', None,
                    GLib.VariantType.new('(s)'), Gio.DBusCallFlags.NONE, 3000, None).unpack()[0]
                nodes = [node.get('name', '') for node in ET.fromstring(tree).findall('node')]
                nodes = [node for node in nodes if re.fullmatch('[0-9]+', node)]
                if not nodes:
                    raise RuntimeError('modem unavailable')
                modem = '/org/freedesktop/ModemManager1/Modem/' + nodes[0]
                snapshot = read_snapshot(lambda p, i, n: self.get(bus, p, i, n), modem)
                GLib.idle_add(self.read_finished, generation, bus, modem, snapshot,
                              for_submit, expected_sim, prefix)
            except Exception:
                # No raw D-Bus errors, paths or subscriber data enter logs/UI.
                GLib.idle_add(self.read_failed, generation, prefix)
        threading.Thread(target=worker, daemon=True, name='sim-status-read').start()

    def finish_read_controls(self):
        self.reading = False
        self.reload.set_sensitive(True)
        self.spinner.stop()
        self.spinner.set_visible(False)

    def read_failed(self, generation, prefix):
        if self.closed or generation != self.generation:
            return GLib.SOURCE_REMOVE
        self.finish_read_controls()
        self.entry.set_text('')
        self.pinsection.set_visible(False)
        self.ready = False
        self.inventory.set_text('Estado de las tarjetas sin confirmar')
        self.status.set_text(prefix or 'No se puede comprobar la SIM. Pulsa «Comprobar SIM».')
        return GLib.SOURCE_REMOVE

    def read_finished(self, generation, bus, modem, snapshot, for_submit, expected_sim, prefix):
        if self.closed or generation != self.generation:
            return GLib.SOURCE_REMOVE
        self.finish_read_controls()
        self.bus, self.modem, self.snapshot = bus, modem, snapshot
        self.inventory.set_text(inventory_text(snapshot))
        kind, message = classify(snapshot, self.send_blocked)
        if kind == 'pin' and self.send_consumed:
            kind, message = 'blocked', 'PIN enviado. No se reenviará en esta ventana. Cierra y vuelve a abrir para comprobar el estado.'
        self.ready = kind == 'pin'
        self.pinsection.set_visible(self.ready)
        self.set_controls(self.ready)
        if not self.ready:
            self.entry.set_text('')
        self.status.set_text((prefix + ' ' if prefix else '') + message)
        if for_submit and self.ready:
            if snapshot.current != expected_sim:
                self.entry.set_text('')
                self.status.set_text('La SIM principal ha cambiado. Comprueba la tarjeta antes de introducir el PIN.')
            else:
                self.send_pin()
        return GLib.SOURCE_REMOVE

    def key_pressed(self, button, label):
        if self.busy or self.reading or not self.ready:
            return
        value = self.entry.get_text()
        if label == 'Borrar':
            self.entry.set_text(value[:-1])
        elif label == 'Vaciar':
            self.entry.set_text('')
        elif len(value) < 8:
            self.entry.set_text(value + label)
        value = None

    def submit(self, *_):
        if self.busy or self.reading or not self.ready:
            return
        # Recheck primary SIM, Active and lock in a fresh status snapshot.
        # There is no automatic retry and no SendPin from status-only refreshes.
        self.start_read(for_submit=True)

    def send_pin(self):
        if self.busy or self.reading or not self.ready or self.send_blocked or self.send_consumed:
            return
        value = self.entry.get_text()
        if not re.fullmatch('[0-9]{4,8}', value):
            self.status.set_text('Introduce entre 4 y 8 cifras.')
            value = None
            return
        self.busy = True
        self.ready = False
        self.set_controls(False)
        self.reload.set_sensitive(False)
        parameters = GLib.Variant('(s)', (value,))
        value = None
        self.entry.set_text('')
        self.status.set_text('Comprobando el PIN…')
        self.spinner.set_visible(True)
        self.spinner.start()
        try:
            self.bus.call(BUS, self.snapshot.current, BUS + '.Sim', 'SendPin', parameters, None,
                Gio.DBusCallFlags.NONE, 30000, None, self.finished, None)
        except Exception:
            self.busy = False
            self.send_blocked = True
            self.finish_read_controls()
            self.pinsection.set_visible(False)
            self.status.set_text('No se ha podido confirmar el envío. No se reenviará el PIN en esta ventana.')
        finally:
            parameters = None

    def finished(self, connection, result, *_):
        self.busy = False
        self.ready = False
        self.finish_read_controls()
        self.pinsection.set_visible(False)
        self.send_consumed = True
        message = 'PIN enviado.'
        try:
            connection.call_finish(result)
        except GLib.Error as error:
            self.send_blocked = True
            name = Gio.DBusError.get_remote_error(error) or ''
            message = 'No se ha podido desbloquear la SIM.'
            if 'Unauthorized' in name or 'Auth' in name:
                message = 'El sistema no ha autorizado la operación.'
            elif 'Incorrect' in name or 'Wrong' in name:
                message = 'El PIN no se ha aceptado.'
        except Exception:
            self.send_blocked = True
            message = 'No se ha podido confirmar el resultado del PIN.'
        self.start_read(prefix=message)


if __name__ == '__main__':
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    sys.exit(SimUnlock().run(sys.argv))
