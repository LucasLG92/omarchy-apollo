#!/usr/bin/python3
# SPDX-License-Identifier: MIT
"""Local touch PIN entry using MM SendPin; never arguments, files or logs."""
import re
import resource
import sys
import xml.etree.ElementTree as ET
import gi
gi.require_version('Gtk','4.0')
gi.require_version('Adw','1')
from gi.repository import Adw,Gio,GLib,Gtk
BUS='org.freedesktop.ModemManager1'
MODEM=BUS+'.Modem'

class SimUnlock(Adw.Application):
    def __init__(self):
        super().__init__(application_id='org.apollo.SimUnlock',flags=Gio.ApplicationFlags.NON_UNIQUE)
        self.connect('activate',self.activate_window)
        self.bus=None;self.modem=None;self.sim=None;self.busy=False;self.ready=False;self.send_blocked=False

    def get(self,path,interface,prop):
        result=self.bus.call_sync(BUS,path,'org.freedesktop.DBus.Properties','Get',
            GLib.Variant('(ss)',(interface,prop)),GLib.VariantType.new('(v)'),
            Gio.DBusCallFlags.NONE,3000,None).unpack()[0]
        return result.unpack() if isinstance(result,GLib.Variant) else result

    def activate_window(self,*_):
        if self.get_active_window():self.get_active_window().present();return
        self.win=Adw.ApplicationWindow(application=self,title='PIN de la SIM',default_width=432,default_height=720)
        self.win.connect('close-request',self.close_requested)
        box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=18,
            margin_top=24,margin_bottom=24,margin_start=24,margin_end=24)
        title=Gtk.Label(label='Desbloquear la SIM',wrap=True);title.add_css_class('title-1');box.append(title)
        box.append(Gtk.Label(label='Introduce el PIN de tu tarjeta en el móvil.',wrap=True))
        self.entry=Gtk.Entry(visibility=False,max_length=8,hexpand=True)
        self.entry.set_buffer(Gtk.PasswordEntryBuffer())
        self.entry.set_max_length(8)
        self.entry.set_enable_undo(False)
        Gtk.Settings.get_default().set_property('gtk-entry-password-hint-timeout',0)
        self.entry.set_input_purpose(Gtk.InputPurpose.PIN)
        self.entry.set_input_hints(Gtk.InputHints.PRIVATE|Gtk.InputHints.INHIBIT_OSK)
        self.entry.set_size_request(-1,52);self.entry.connect('activate',self.submit);box.append(self.entry)
        self.status=Gtk.Label(label='',wrap=True);box.append(self.status)
        self.keypad=Gtk.Grid(column_spacing=8,row_spacing=8,column_homogeneous=True)
        for index,label in enumerate(('1','2','3','4','5','6','7','8','9','Borrar','0','Vaciar')):
            key=Gtk.Button(label=label);key.set_size_request(-1,52)
            key.connect('clicked',self.key_pressed,label)
            self.keypad.attach(key,index%3,index//3,1,1)
        box.append(self.keypad)
        self.button=Gtk.Button(label='Desbloquear');self.button.add_css_class('suggested-action')
        self.button.set_size_request(-1,52);self.button.connect('clicked',self.submit);box.append(self.button)
        self.reload=Gtk.Button(label='Comprobar SIM');self.reload.connect('clicked',self.discover);box.append(self.reload)
        cancel=Gtk.Button(label='Cerrar');cancel.connect('clicked',lambda *_:self.win.close());box.append(cancel)
        scroll=Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        scroll.set_child(box);self.win.set_content(scroll)
        self.discover()
        self.win.present()

    def close_requested(self,*_):
        if self.busy:
            self.status.set_text('Espera el resultado del PIN que ya se ha enviado.')
            return True
        self.entry.set_text('')
        return False

    def discover(self,*_):
        if self.busy:return
        self.ready=False;self.button.set_sensitive(False)
        try:
            self.bus=Gio.bus_get_sync(Gio.BusType.SYSTEM,None)
            tree=self.bus.call_sync(BUS,'/org/freedesktop/ModemManager1/Modem',
                'org.freedesktop.DBus.Introspectable','Introspect',None,GLib.VariantType.new('(s)'),
                Gio.DBusCallFlags.NONE,3000,None).unpack()[0]
            nodes=[node.get('name','') for node in ET.fromstring(tree).findall('node')]
            nodes=[node for node in nodes if re.fullmatch('[0-9]+',node)]
            if not nodes:raise RuntimeError('modem unavailable')
            self.modem='/org/freedesktop/ModemManager1/Modem/'+nodes[0]
            self.sim=self.get(self.modem,MODEM,'Sim')
            if not re.fullmatch('/org/freedesktop/ModemManager1/SIM/[0-9]+',self.sim):raise RuntimeError('SIM unavailable')
            self.refresh()
        except Exception:
            self.status.set_text('La SIM todavía no está disponible.');self.button.set_sensitive(False)

    def key_pressed(self,button,label):
        if self.busy or not self.ready:return
        value=self.entry.get_text()
        if label=='Borrar':self.entry.set_text(value[:-1])
        elif label=='Vaciar':self.entry.set_text('')
        elif len(value)<8:self.entry.set_text(value+label)

    def refresh(self,prefix=''):
        self.ready=False
        lock=self.get(self.modem,MODEM,'UnlockRequired')
        retries=self.get(self.modem,MODEM,'UnlockRetries')
        left=retries.get(2) if isinstance(retries,dict) else None
        text=prefix
        # PIN2/PUK2 govern secondary SIM facilities. They must never be
        # mistaken for the access PIN or submitted to the SendPin operation.
        if lock in (1,3,5):
            self.status.set_text('La SIM no solicita su PIN de acceso.')
            self.button.set_sensitive(False);self.entry.set_sensitive(False)
            self.keypad.set_sensitive(False);return
        if lock==4 or left==0:
            self.status.set_text('La tarjeta requiere el PUK. No se enviarán más PIN.')
            self.button.set_sensitive(False);self.entry.set_sensitive(False);return
        if lock!=2:
            self.status.set_text('La tarjeta no está solicitando su PIN habitual.')
            self.button.set_sensitive(False);return
        if self.send_blocked:
            self.status.set_text(prefix+' No se reenviará el PIN en esta ventana. Comprueba tu PIN y vuelve a abrir la aplicación.')
            self.button.set_sensitive(False);self.entry.set_sensitive(False);self.keypad.set_sensitive(False);return
        if left is not None:text+=(' ' if text else '')+'Intentos restantes: '+str(left)
        self.status.set_text(text);self.ready=True
        self.button.set_sensitive(True);self.entry.set_sensitive(True);self.keypad.set_sensitive(True)

    def submit(self,*_):
        if self.busy or not self.ready:return
        try:self.refresh()
        except Exception:
            self.status.set_text('No se puede comprobar la SIM. Pulsa «Comprobar SIM».');return
        if not self.ready:return
        value=self.entry.get_text()
        if not re.fullmatch('[0-9]{4,8}',value):
            self.status.set_text('Introduce entre 4 y 8 cifras.');return
        self.busy=True;self.button.set_sensitive(False);self.entry.set_sensitive(False)
        self.keypad.set_sensitive(False);self.reload.set_sensitive(False)
        parameters=GLib.Variant('(s)',(value,));value=None;self.entry.set_text('')
        self.status.set_text('Comprobando el PIN…')
        try:
            self.bus.call(BUS,self.sim,BUS+'.Sim','SendPin',parameters,None,
                Gio.DBusCallFlags.NONE,30000,None,self.finished,None)
        except Exception:
            self.busy=False;self.ready=False;self.send_blocked=True;self.reload.set_sensitive(True)
            self.status.set_text('No se ha podido enviar el PIN. Comprueba el estado de la SIM.')
        finally:parameters=None

    def finished(self,connection,result,*_):
        self.busy=False
        self.ready=False;self.reload.set_sensitive(True)
        try:
            connection.call_finish(result)
        except GLib.Error as error:
            self.send_blocked=True
            name=Gio.DBusError.get_remote_error(error) or ''
            message='No se ha podido desbloquear la SIM.'
            if 'Unauthorized' in name or 'Auth' in name:message='El sistema no ha autorizado la operación.'
            elif 'Incorrect' in name or 'Wrong' in name:message='El PIN no se ha aceptado.'
            try:self.refresh(message)
            except Exception:self.status.set_text(message);self.button.set_sensitive(False)
            return
        except Exception:
            self.send_blocked=True
            self.status.set_text('No se ha podido consultar el estado de la SIM.');self.button.set_sensitive(False)
            return
        # A successful SendPin must never be retried automatically if the
        # subsequent read fails or the modem temporarily reprobes its object.
        self.status.set_text('PIN enviado. Pulsa «Comprobar SIM» para ver el estado.')
        try:self.refresh()
        except Exception:pass

if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    sys.exit(SimUnlock().run(sys.argv))
