"""A disposable text field for the isolated on-screen keyboard checks."""
import os
import gi
gi.require_version('Gtk','4.0')
from gi.repository import Gtk,GLib
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

BUS='org.omarchy.Apollo.KeyboardFixture'
INTERFACE=BUS+'1'
assert os.getuid()>=1000
DBusGMainLoop(set_as_default=True)
application=Gtk.Application(application_id=BUS+'.Window')


class Fixture(dbus.service.Object):
    def __init__(self,entry,button):
        self.entry=entry;self.button=button
        self.last_modifiers=0
        self.name=dbus.service.BusName(BUS,dbus.SessionBus(),do_not_queue=True)
        super().__init__(self.name,'/org/omarchy/Apollo/KeyboardFixture')

    @dbus.service.method(INTERFACE,in_signature='s',out_signature='b')
    def Focus(self,kind):
        assert kind in ('text','button')
        focused=(self.entry if kind=='text' else self.button).grab_focus()
        if kind=='text':
            # GTK selects existing text on focus; this fixture appends test keys.
            self.entry.select_region(-1,-1)
            self.entry.set_position(-1)
        return focused

    @dbus.service.method(INTERFACE,in_signature='',out_signature='s')
    def Text(self):
        return self.entry.get_text()

    @dbus.service.method(INTERFACE,in_signature='s',out_signature='')
    def SetText(self,value):
        assert len(value)<=64
        self.entry.set_text(value)

    @dbus.service.method(INTERFACE,in_signature='',out_signature='u')
    def LastModifiers(self):
        return self.last_modifiers

    @dbus.service.method(INTERFACE,in_signature='',out_signature='u')
    def CurrentModifiers(self):
        keyboard=self.entry.get_display().get_default_seat().get_keyboard()
        return int(keyboard.get_modifier_state())

    def key_pressed(self,controller,keyval,keycode,state):
        self.last_modifiers=int(state)
        return False


def activate(app):
    window=Gtk.ApplicationWindow(application=app,title='Prueba de teclado · Apollo')
    box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=20,
        margin_start=24,margin_end=24,margin_top=24,margin_bottom=24)
    box.append(Gtk.Label(label='Solo texto de prueba',xalign=0))
    entry=Gtk.Entry(height_request=52)
    button=Gtk.Button(label='Fuera del campo',height_request=52)
    box.append(entry);box.append(button)
    window.set_child(box);window.set_default_size(400,500)
    window.fixture=Fixture(entry,button)
    keys=Gtk.EventControllerKey()
    keys.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    keys.connect('key-pressed',window.fixture.key_pressed)
    entry.add_controller(keys)
    window.present()
    GLib.idle_add(lambda:(button.grab_focus(),False)[1])


application.connect('activate',activate)
raise SystemExit(application.run([]))
