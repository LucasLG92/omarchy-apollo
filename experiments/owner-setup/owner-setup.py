#!/usr/bin/python3
# SPDX-License-Identifier: MIT
"""Local owner credential setup. No credential arguments, files, dumps or logs."""
from pathlib import Path
import os,re,resource,subprocess,sys,threading
import gi
gi.require_version('Gtk','4.0');gi.require_version('Adw','1')
from gi.repository import Adw,Gdk,Gio,GLib,Gtk,Pango

HERE=Path(__file__).resolve().parent
class PinField(Gtk.Button):
    """Touch field with a protected buffer and no text-input/OSK surface."""
    def __init__(self,placeholder):
        super().__init__()
        self.placeholder=placeholder;self.buffer=Gtk.PasswordEntryBuffer()
        self.buffer.set_max_length(32);self.set_size_request(-1,52)
        self.display=Gtk.Label(label=placeholder,wrap=True,justify=Gtk.Justification.CENTER)
        self.display.set_wrap_mode(Pango.WrapMode.WORD_CHAR);self.display.set_max_width_chars(28)
        self.set_child(self.display);self.add_css_class('omarchy-pin-field')
    def get_buffer(self):return self.buffer
    def get_text(self):return self.buffer.get_text()
    def set_text(self,value):
        self.buffer.set_text(value,-1)
        self.display.set_text('●'*self.buffer.get_length() if self.buffer.get_length() else self.placeholder)

class OwnerSetup(Adw.Application):
    def __init__(self):
        super().__init__(application_id='org.apollo.OwnerSetup',flags=Gio.ApplicationFlags.NON_UNIQUE)
        self.connect('activate',self.activate_window);self.busy=False;self.completed=False
    def activate_window(self,*_):
        if self.get_active_window():self.get_active_window().present();return
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        css=Gtk.CssProvider();css.load_from_path(str(HERE/'omarchy.css'))
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(),css,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        Gtk.Settings.get_default().set_property('gtk-entry-password-hint-timeout',0)
        self.win=Adw.ApplicationWindow(application=self,title='Código de Omarchy',default_width=360,default_height=760)
        self.win.add_css_class('apollo-omarchy');self.win.connect('close-request',self.close_requested)
        box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12,margin_top=20,margin_bottom=20,margin_start=20,margin_end=20)
        box.set_valign(Gtk.Align.CENTER)
        logo=Gtk.Picture.new_for_filename(str(HERE/'assets/logo.png'));logo.set_can_shrink(True);logo.set_size_request(-1,48);box.append(logo)
        title=Gtk.Label(label='Código de Omarchy');title.add_css_class('omarchy-title');box.append(title)
        box.append(Gtk.Label(label='Elige un código para iniciar sesión y autorizar cambios. Es distinto del PIN de la SIM.',wrap=True))
        self.entries=[]
        for label in ('Código nuevo · mínimo 8 cifras','Repite el código'):
            entry=PinField(label)
            entry.connect('clicked',self.select_field);box.append(entry);self.entries.append(entry)
        self.active=self.entries[0]
        self.active.add_css_class('omarchy-pin-selected')
        keypad=Gtk.Grid(column_homogeneous=True,column_spacing=8,row_spacing=8)
        for i,label in enumerate(('1','2','3','4','5','6','7','8','9','Borrar','0','Vaciar')):
            button=Gtk.Button(label=label);button.set_focus_on_click(False);button.set_size_request(-1,48)
            button.add_css_class('omarchy-key');button.connect('clicked',self.digit,label)
            keypad.attach(button,i%3,i//3,1,1)
        self.keypad=keypad;box.append(keypad)
        self.status=Gtk.Label(label='El código se establece solo en este teléfono.',wrap=True);box.append(self.status)
        self.save=Gtk.Button(label='Guardar código');self.save.add_css_class('omarchy-primary');self.save.set_size_request(-1,52)
        self.save.connect('clicked',self.submit);box.append(self.save)
        self.close=Gtk.Button(label='Cerrar');self.close.connect('clicked',lambda *_:self.win.close());box.append(self.close)
        clamp=Adw.Clamp(maximum_size=400,tightening_threshold=360);clamp.set_child(box);clamp.set_vexpand(True)
        scroll=Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER);scroll.set_child(clamp)
        self.win.set_content(scroll);self.win.fullscreen();self.win.present()
    def select_field(self,entry,*_):
        if self.busy or self.completed:return
        self.active.remove_css_class('omarchy-pin-selected')
        self.active=entry;self.active.add_css_class('omarchy-pin-selected')
    def digit(self,button,label):
        if self.busy or self.completed:return
        value=self.active.get_text()
        if label=='Borrar':self.active.set_text(value[:-1])
        elif label=='Vaciar':self.active.set_text('')
        elif len(value)<32:self.active.set_text(value+label)
    def close_requested(self,*_):
        if self.busy:
            self.status.set_text('Espera mientras el sistema guarda el código.');return True
        for entry in self.entries:entry.set_text('')
        return False
    def submit(self,*_):
        if self.busy or self.completed:return
        first,second=(entry.get_text() for entry in self.entries)
        if not re.fullmatch('[0-9]{8,32}',first):
            self.status.set_text('Usa entre 8 y 32 cifras.');return
        if first!=second:
            self.status.set_text('Los códigos no coinciden.');return
        self.busy=True;self.save.set_sensitive(False);self.keypad.set_sensitive(False)
        for entry in self.entries:entry.set_text('');entry.set_sensitive(False)
        self.status.set_text('Guardando el código en el teléfono…')
        threading.Thread(target=self.worker,args=(first,),daemon=True).start();first=second=None
    def set_credential(self,value):
        assert os.geteuid()==0 and Path('/etc/apollo/native-root-v1').is_file()
        assert not Path('/var/lib/apollo/owner-ready').exists()
        # PAM receives the secret only through a local anonymous pipe.
        result=subprocess.run(['/usr/bin/chpasswd'],input=('omarchy:'+value+'\n').encode(),
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=25)
        if result.returncode!=0:return False
        state=subprocess.check_output(['/usr/bin/passwd','-S','omarchy'],timeout=5).decode().split()
        assert state[1]=='P'
        directory=Path('/etc/sddm.conf.d');assert directory.is_dir() and not directory.is_symlink()
        temp=directory/'90-apollo-native-access.conf.new';assert not temp.exists() and not temp.is_symlink()
        temp.write_text('[Autologin]\nUser=\nRelogin=false\n\n[Theme]\nCurrent=omarchy-apollo-original\n')
        temp.chmod(0o644);temp.replace(directory/'90-apollo-native-access.conf')
        marker=Path('/var/lib/apollo/owner-ready');marker.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        marker.write_text('Owner credential configured locally through PAM.\n');marker.chmod(0o600)
        os.sync();return True
    def worker(self,value):
        try:success=self.set_credential(value)
        except Exception:success=False
        finally:value=None
        GLib.idle_add(self.finished,success)
    def finished(self,success):
        self.busy=False
        if success:
            self.completed=True;self.status.set_text('Código guardado. Se pedirá al iniciar Omarchy y para autorizar cambios.');self.save.set_visible(False)
            self.close.set_visible(False);GLib.timeout_add(600,self.close_after_success)
        else:
            self.status.set_text('El sistema no ha aceptado el código. Prueba uno más largo.');self.save.set_sensitive(True);self.keypad.set_sensitive(True)
            for entry in self.entries:entry.set_sensitive(True)
        return GLib.SOURCE_REMOVE
    def close_after_success(self):
        if self.completed:self.win.close();self.quit()
        return GLib.SOURCE_REMOVE

if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    assert os.geteuid()==0
    sys.exit(OwnerSetup().run(sys.argv))
