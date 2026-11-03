#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Native Apollo update compatibility policy, shared by the UI and ALPM."""
from pathlib import Path
import fnmatch,json,os,stat,subprocess,sys
POLICY=Path('/usr/share/apollo/update-compatibility.json')
PROTECTED=('apollo-*','omamobile-*','omarchy','omarchy-settings','hyprland','aquamarine','hyprlang','hyprutils','hyprgraphics','quickshell','qt6-*','mesa','lib32-mesa','vulkan-*','linux','linux-*','limine*','grub','mkinitcpio','dracut','fwupd','snapper','systemd-ukify','gnome-calls','modemmanager','alsa-ucm-conf','wireplumber','pipewire*','libcamera*','squeekboard')
def protected_package(name):return any(fnmatch.fnmatchcase(name,p) for p in PROTECTED)
def trusted(path):
 try:
  s=path.lstat();return stat.S_ISREG(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022
 except OSError:return False
def load_policy():
 if not trusted(POLICY):raise ValueError('Falta la política de compatibilidad de Apollo.')
 value=json.loads(POLICY.read_text())
 if value.get('schema')!=1 or not isinstance(value.get('protected_versions'),dict):raise ValueError('Política de Apollo no válida.')
 return value
def native_blocker():
 if Path('/var/lib/apollo/release-in-progress.json').exists():return 'Hay una actualización de Apollo pendiente de recuperación. Ejecuta sudo apollo-install-release --recover.'
 if Path('/etc/apollo/ram-trial').exists():return 'Sesión temporal en RAM: actualiza la instalación permanente.'
 if not trusted(Path('/etc/apollo/native-root-v1')):return 'No se reconoce la instalación nativa de Apollo.'
 try:
  policy=load_policy()
  if os.uname().release not in policy['kernels']:return 'Este kernel necesita validar su compatibilidad con Apollo.'
  fs=subprocess.run(['/usr/bin/findmnt','-n','-o','FSTYPE','/'],capture_output=True,text=True,timeout=5)
  if fs.returncode or fs.stdout.strip()!='ext4':return 'La raíz permanente de Apollo no está montada como se esperaba.'
 except (OSError,ValueError,KeyError,subprocess.TimeoutExpired):return 'No se pudo verificar la compatibilidad de Apollo.'
 return ''
def target_blocker(targets,policy=None):
 policy=policy or load_policy();versions=policy['protected_versions']
 blocked=sorted({name for name,version in targets if protected_package(name) and versions.get(name)!=version})
 if blocked:return 'Requieren una actualización validada para Apollo: '+', '.join(blocked)+'. No se ha modificado ningún paquete.'
 return ''
def alpm_guard(names):
 # ALPM has already resolved the final transaction. Reject replacing/removing
 # device-critical packages through a generic update, including reinstalls.
 blocked=sorted({n for n in names if protected_package(n)})
 if blocked:
  print('Apollo: esta transacción sustituye componentes del dispositivo ('+', '.join(blocked)+'). Usa una versión de Apollo validada; el resto de paquetes puede actualizarse normalmente.',file=sys.stderr)
  return 1
 return 0
if __name__=='__main__':
 if sys.argv[1:]==['--alpm']:sys.exit(alpm_guard([n.strip() for n in sys.stdin if n.strip()]))
 elif sys.argv[1:]==['--check']:print(native_blocker());sys.exit(bool(native_blocker()))
 else:sys.exit(2)
