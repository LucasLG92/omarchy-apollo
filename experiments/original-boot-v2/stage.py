"""Prepare a NEW package tree; never install or activate the original-style theme."""
from pathlib import Path
import argparse,shutil
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();source=Path(__file__).resolve().parent;dest=args.output.resolve()
assert not dest.exists(),'Output must be a new package staging directory.'
assert dest!=Path(dest.anchor) and len(dest.parts)>=3,'Refusing a filesystem root.'
dest.mkdir(parents=True)
for kind,parent in (('plymouth','usr/share/plymouth/themes'),('sddm','usr/share/sddm/themes')):
 for theme in (source/'native'/kind).iterdir():
  assert theme.is_dir() and not theme.is_symlink();shutil.copytree(theme,dest/parent/theme.name)
docs=dest/'usr/share/doc/apollo-mobile-boot';docs.mkdir(parents=True)
for name in ('INTEGRACION.txt','source-manifest.json'):shutil.copy2(source/name,docs/name)
licenses=dest/'usr/share/licenses/apollo-mobile-boot';licenses.mkdir(parents=True)
shutil.copy2(source/'LICENSE',licenses/'LICENSE')
print('New original-style package tree staged; no active theme or authentication changes.')
