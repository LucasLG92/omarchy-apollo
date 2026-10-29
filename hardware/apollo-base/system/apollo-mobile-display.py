#!/usr/bin/python3
"""Apply a reversible portrait desktop profile as the local desktop user."""
from pathlib import Path
import configparser,datetime,json,os,shutil,subprocess

assert os.geteuid()!=0, 'Run this as the desktop user, without sudo'
home=Path.home(); config=home/'.config'
def run(*args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=30)
 if p.returncode: raise RuntimeError(p.stderr[:400])
 return p.stdout
outputs=json.loads(run('kscreen-doctor','-j'))['outputs']
native=[o for o in outputs if o['name']=='DSI-1' and o['connected'] and o['enabled']]
assert len(native)==1
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
backup=home/'.local/state/apollo-mobile/backups'/stamp
backup.mkdir(parents=True); backup.chmod(0o700)
for name in ('kwinrc','kwinoutputconfig.json','plasma-org.kde.plasma.desktop-appletsrc'):
 source=config/name
 if source.is_file(): shutil.copyfile(source,backup/name)
(backup/'screen-before.json').write_text(json.dumps({'scale':native[0]['scale'],'output':'DSI-1'})+'\n')
theme=home/'.local/share/aurorae/themes/WhiteSur-dark/WhiteSur-darkrc'
if theme.is_file():
 shutil.copyfile(theme,backup/'WhiteSur-darkrc')
 parser=configparser.ConfigParser(interpolation=None,strict=False); parser.optionxform=str
 parser.read(theme)
 assert parser.has_section('Layout')
 for key,value in {'ButtonWidth':32,'ButtonHeight':32,'ButtonSpacing':8,
                   'TitleHeight':32,'TitleEdgeTop':6,'TitleEdgeBottom':6,
                   'TitleEdgeTopMaximized':6,'TitleEdgeBottomMaximized':6,
                   'TitleBorderLeft':16,'TitleBorderRight':16}.items():
  parser.set('Layout',key,str(value))
 with theme.open('w') as stream: parser.write(stream,space_around_delimiters=False)
run('kwriteconfig6','--file','kwinrc','--group','Windows','--key','Placement','Maximizing')
run('kwriteconfig6','--file','kwinrc','--group','Windows','--key','BorderlessMaximizedWindows','false')
run('kscreen-doctor','output.'+str(native[0]['id'])+'.scale.2.25')
panels=Path('/usr/share/apollo/apollo-mobile-panels.js')
assert panels.is_file()
run('qdbus6','org.kde.plasmashell','/PlasmaShell','org.kde.PlasmaShell.evaluateScript',panels.read_text())
run('qdbus6','org.kde.KWin','/KWin','org.kde.KWin.reconfigure')
print('Perfil de pantalla aplicado: escala 225 %, controles mayores y ventanas nuevas maximizadas.')
print('La configuración anterior queda guardada de forma privada en '+str(backup))
