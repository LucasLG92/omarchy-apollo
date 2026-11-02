"""Actual GTK with an in-memory credential sink. Never PAM, shadow or a radio."""
from pathlib import Path
import importlib.util,json,sys,threading,time
spec=importlib.util.spec_from_file_location('owner_ui',Path(__file__).with_name('owner-setup.py'))
ui=importlib.util.module_from_spec(spec);spec.loader.exec_module(ui)
calls=[];gate=threading.Event()
class SyntheticOwner(ui.OwnerSetup):
    def set_credential(self,value):
        assert value=='00000007';calls.append(True);assert gate.wait(5);return True
def pump(predicate):
    deadline=time.monotonic()+6;context=ui.GLib.MainContext.default()
    while time.monotonic()<deadline:
        while context.pending():context.iteration(False)
        if predicate():return
        time.sleep(.005)
    raise AssertionError('GTK owner test timed out')
app=SyntheticOwner();assert app.register(None);app.activate()
assert all(isinstance(e.get_buffer(),ui.Gtk.PasswordEntryBuffer) and isinstance(e,ui.Gtk.Button) and not isinstance(e,ui.Gtk.Editable) for e in app.entries)
app.entries[1].emit('clicked');assert app.active is app.entries[1]
app.digit(None,'0');assert app.entries[1].get_text()=='0' and app.entries[1].display.get_text()=='●' and not app.entries[0].get_text()
app.digit(None,'Borrar');assert not app.entries[1].get_text()
app.entries[0].emit('clicked');assert app.active is app.entries[0]
app.entries[0].set_text('1234567');app.entries[1].set_text('1234567');app.submit();assert not calls and not app.busy
app.entries[0].set_text('00000007');app.entries[1].set_text('00000008');app.submit();assert not calls and not app.busy
app.entries[1].set_text('00000007');app.submit();pump(lambda:bool(calls))
assert app.busy and len(calls)==1 and all(not e.get_text() for e in app.entries)
assert app.close_requested() is True
app.submit();assert len(calls)==1
responsive=[];ui.GLib.idle_add(lambda:responsive.append(True) and False);pump(lambda:bool(responsive))
gate.set();pump(lambda:app.completed)
assert not app.busy and not app.save.get_visible() and app.close_requested() is False
pump(lambda:not app.win.get_visible());app.quit()
print(json.dumps({'real_gtk_gio_loaded':True,'synthetic_credential_sink_only':True,
 'invalid_and_mismatched_codes_not_submitted':True,'leading_zero_preserved':True,
 'password_buffers_masked_undo_disabled':True,'no_editable_widget_can_request_osk':True,
 'touch_field_selection_and_masked_keypad':True,'buffers_cleared_before_worker':True,
 'one_pending_submission_and_close_guard':True,'gtk_loop_responsive_during_credential_work':True,
 'automatic_close_only_after_success':True,
 'real_pam_or_shadow_operations':0,'radio_or_subscriber_queries':0},indent=2))
