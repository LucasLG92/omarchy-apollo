#!/usr/bin/python3
"""Exercise the actual power helper using isolated runtime and IPC fixtures.

Run as root with PrivateMounts=yes. No display, lock, PIN or account is changed.
"""
from pathlib import Path
import argparse,json,os,pwd,shutil,subprocess,tempfile

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--helper',type=Path,required=True)
args=parser.parse_args();assert os.getuid()==0 and os.geteuid()==0
assert os.readlink('/proc/self/ns/mnt')!=os.readlink('/proc/1/ns/mnt')
owner=pwd.getpwnam('apollo');assert owner.pw_uid==1001
checks=[];mounts=[]
def run(command,**kw):return subprocess.run(command,capture_output=True,text=True,timeout=12,**kw)
stub=r'''#!/usr/bin/python3
from pathlib import Path
import json,sys,os,time
path=Path(os.environ['APOLLO_POWER_TEST_STATE']);state=json.loads(path.read_text())
name=Path(sys.argv[0]).name;args=sys.argv[1:];call=[name,*args]
state['calls'].append(call)
code=0;output=''
if name=='omarchy-apollo-keyboard-run':output=state.get('keyboard','auto')
elif name=='hyprctl' and args==['monitors','-j']:
 output=json.dumps([{'name':'OTHER' if state.get('no_panel') else 'DSI-1','dpmsStatus':state['on']}])
elif name=='omarchy-shell':
 action=args[-1]
 if action=='status':
  if state.get('fail_first_status') and not state.get('status_failed_once'):
   state['status_failed_once']=True;path.write_text(json.dumps(state));raise SystemExit(1)
  if state.get('stall_status'):time.sleep(3)
  if state.get('requested'):
   state['polls']=state.get('polls',0)+1
   if state['polls']>=2:state['secure']=True
  if state.get('cancel_touch') and state.get('secure'):state['transition']=False
  value={'secure':state.get('secure',False),'sessionLocked':state.get('secure',False),'requested':state.get('requested',False)}
  if state.get('api',True):value['mobilePowerTransition']=state.get('transition',False)
  output=json.dumps(value)
 elif action=='prepareScreenOff':
  if state.get('refuse_prepare'):code=1
  else:state['transition']=True;state['requested']=True;output='ok'
 elif action=='showKeypad':state['transition']=False;output='ok'
 elif action=='lock':
  if state.get('refuse_lock'):code=1
  else:state['requested']=True;output='ok'
 else:code=2
elif name=='hyprctl' and args[:1]==['dispatch']:
 if not state.get('secure'):state['unsafe_dispatch']=True;code=2
 else:state['dispatches'].append(args[1]);output='ok'
else:code=2
path.write_text(json.dumps(state));print(output);raise SystemExit(code)
'''
try:
    with tempfile.TemporaryDirectory(prefix='power-flow-',dir='/var/lib/omarchy-apollo') as directory:
        root=Path(directory);root.chmod(0o755)
        runtime=root/'runtime';runtime.mkdir(mode=0o700);os.chown(runtime,owner.pw_uid,owner.pw_gid)
        marker_root=root/'pin-status';marker_root.mkdir(mode=0o755)
        marker=marker_root/'1001';marker.write_text('configured\n');marker.chmod(0o644)
        for source,target in [(runtime,Path('/run/user/1001')),(marker_root,Path('/var/lib/omarchy-apollo/pin-status'))]:
            assert run(['mount','--bind',str(source),str(target)]).returncode==0;mounts.append(target)
        programs=root/'programs';programs.mkdir(mode=0o755)
        for name in ['hyprctl','omarchy-shell','omarchy-apollo-keyboard-run']:
            file=programs/name;file.write_text(stub);file.chmod(0o755)
        helper=root/'power-button';shutil.copyfile(args.helper,helper);helper.chmod(0o755)
        state=root/'state.json';state.touch();os.chown(state,owner.pw_uid,owner.pw_gid);state.chmod(0o600)
        base=['runuser','-u','apollo','--','env','PATH='+str(programs)+':/usr/bin','XDG_RUNTIME_DIR=/run/user/1001','APOLLO_POWER_TEST_STATE='+str(state),str(helper)]
        cases=[
            ('startup acquires a lock without blanking',{'on':True},['--startup'],None,0),
            ('startup waits for a temporarily unavailable lock service',{'on':True,'fail_first_status':True},['--startup'],None,0),
            ('startup preserves an existing secure lock',{'on':True,'secure':True},['--startup'],None,0),
            ('power locks then blanks an unlocked screen',{'on':True},[],'disable',0),
            ('power blanks an already locked screen',{'on':True,'secure':True},[],'disable',0),
            ('power reveals the keypad before waking',{'on':False,'secure':True},[],'enable',0),
            ('idle locks and blanks',{'on':True},['--idle'],'disable',0),
            ('idle never wakes an already blank locked screen',{'on':False,'secure':True},['--idle'],None,0),
            ('idle secures a blank unlocked screen without waking it',{'on':False},['--idle'],None,0),
            ('failed blackout preparation never blanks',{'on':True,'refuse_prepare':True},[],None,1),
            ('failed legacy lock never blanks',{'on':True,'api':False,'refuse_lock':True},[],None,1),
            ('touch during the transition cancels blanking',{'on':True,'cancel_touch':True},[],None,0),
            ('enrollment keeps the screen unchanged',{'on':True,'keyboard':'setup'},[],None,0),
            ('an invalid option changes nothing',{'on':True},['--unknown'],None,1),
            ('legacy interface still locks before blanking',{'on':True,'api':False},[],'disable',0),
            ('legacy interface still wakes a locked screen',{'on':False,'secure':True,'api':False},[],'enable',0),
            ('a missing internal panel is rejected',{'on':True,'no_panel':True},[],None,1),
            ('an unresponsive lock service never blanks',{'on':True,'stall_status':True},[],None,1),
        ]
        for label,settings,options,action,expected in cases:
            initial={'calls':[],'dispatches':[],**settings};state.write_text(json.dumps(initial))
            result=run([*base,*options]);final=json.loads(state.read_text())
            assert result.returncode==expected,label
            assert not final.get('unsafe_dispatch'),label
            dispatches=final['dispatches']
            assert (len(dispatches)==1 and 'action = "'+action+'"' in dispatches[0]) if action else not dispatches,label
            if action=='enable' and settings.get('api',True):
                reveal=next(i for i,call in enumerate(final['calls']) if call[-1]=='showKeypad')
                wake=next(i for i,call in enumerate(final['calls']) if call[:2]==['hyprctl','dispatch'])
                assert reveal<wake,label
            checks.append(label)
        marker.unlink();state.write_text(json.dumps({'calls':[],'dispatches':[],'on':True}))
        assert run(base).returncode==0 and not json.loads(state.read_text())['calls']
        checks.append('no enrolled PIN means no lock or display operation')
finally:
    for target in reversed(mounts):assert run(['umount',str(target)]).returncode==0
print(json.dumps({'checks_passed':len(checks),'checks':checks,'real_helper_executed':True,'ipc_commands_replaced_by_fixtures':True,'physical_screen_changed':False,'owner_credentials_used':False},indent=2))
