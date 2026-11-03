#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Signed package cohorts installed into an inactive /usr generation.

The active /etc, /home and application state never enter a release artifact.
Preparation uses a private on-device /etc copy; changes to it are rejected.
This first backend deliberately accepts the currently running kernel only.
"""
from pathlib import Path
from contextlib import contextmanager
import argparse
import fcntl
import hashlib
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

KEY = '37F17024795607039EB4293D7B111A2281AB64AC'
PUB = Path('/usr/share/apollo/release-keyring.gpg')
STORE = Path('/var/lib/apollo/system-versions')
SELECTOR = Path('/usr/lib/apollo/apollo-boot-selector')
BOOT_CONTRACT = Path('/run/apollo-versioned-usr-v1')
REGISTRY = Path('/var/lib/apollo-updates/release.json')
ID = re.compile(r'[a-z0-9][a-z0-9_-]{0,63}\Z')
PACKAGE = re.compile(r'[a-z0-9][a-z0-9@+_.-]*\Z')
VERSION = re.compile(r'[A-Za-z0-9@+_.:~-]+\Z')
FIELDS = {'schema','id','sequence','device','kernel','config_abi','packages'}
RESERVE = 1024**3
TRANSACTION_LOG = None

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def run(args, timeout=60, env=None):
    r = subprocess.run(list(map(str,args)), capture_output=True, timeout=timeout,
        env=env or {'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8'})
    # Package scripts may print private config. Never forward their output.
    if TRANSACTION_LOG is not None:
        fd=os.open(TRANSACTION_LOG,os.O_WRONLY|os.O_CREAT|os.O_APPEND|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'ab') as log:log.write(r.stdout+r.stderr)
    require(r.returncode == 0, 'Falló '+Path(args[0]).name+' (código '+str(r.returncode)+'); no se ha activado la candidata.')
    return r.stdout.decode()

def trusted(path, directory=False):
    s = path.lstat()
    require((stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode))
        and s.st_uid == 0 and not s.st_mode & 0o022
        and (directory or s.st_nlink == 1), 'Ruta de actualización no confiable.')
    return s

def trusted_parents(path):
    require(path.is_absolute() and '..' not in path.parts, 'Se requiere una ruta absoluta normalizada.')
    for parent in reversed((path,*path.parents)):
        trusted(parent, True)

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024**2),b''):
            h.update(chunk)
    return h.hexdigest()

def atomic(path, body):
    fd, temp = tempfile.mkstemp(prefix='.commit-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(body); f.flush(); os.fsync(f.fileno())
        os.replace(temp,path)
        directory = os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally:
        if os.path.exists(temp): os.unlink(temp)

def json_unique(pairs):
    result={}
    for key,value in pairs:
        require(key not in result,'Clave JSON duplicada.')
        result[key]=value
    return result

def read_manifest(path, verify=run, keyring=PUB, artifacts=True):
    trusted_parents(path.parent)
    require(trusted(path).st_size <= 1024**2,'Manifiesto demasiado grande.')
    signature=Path(str(path)+'.sig')
    require(trusted(signature).st_size <= 16384,'Firma demasiado grande.')
    trusted(keyring)
    with tempfile.TemporaryDirectory() as home:
        out=verify(['/usr/bin/gpgv','--homedir',home,'--keyring',keyring,
            '--status-fd=1',signature,path])
    valid=[s.split()[2] for s in out.splitlines() if s.startswith('[GNUPG:] VALIDSIG ')]
    require(valid==[KEY],'Firma de publicación ajena al proyecto.')
    data=json.loads(path.read_bytes(),object_pairs_hook=json_unique)
    require(isinstance(data,dict) and set(data)==FIELDS and data['schema']=='apollo-system-release-1','Esquema de publicación no válido.')
    require(isinstance(data['id'],str) and ID.fullmatch(data['id']) and data['id']!='bootstrap','Identificador no válido.')
    require(type(data['sequence']) is int and 0<data['sequence']<=2**63-1,'Secuencia no válida.')
    require(data['device']=='xiaomi,apollo' and data['config_abi']=='apollo-shared-etc-1','Publicación para otra plataforma/configuración.')
    require(isinstance(data['kernel'],str) and VERSION.fullmatch(data['kernel']),'Kernel no válido.')
    require(isinstance(data['packages'],list) and 0<len(data['packages'])<=4096,'Conjunto de paquetes no válido.')
    names=set(); files=set()
    for row in data['packages']:
        require(isinstance(row,dict) and set(row)=={'name','from_version','version','file','bytes','sha256'},'Paquete no válido.')
        require(isinstance(row['name'],str) and PACKAGE.fullmatch(row['name']) and row['name'] not in names,'Nombre de paquete duplicado/no válido.')
        for field in ('version','from_version'):
            require((field=='from_version' and row[field] is None) or
                (isinstance(row[field],str) and VERSION.fullmatch(row[field])),'Versión de paquete no válida.')
        require(isinstance(row['file'],str) and re.fullmatch(r'[A-Za-z0-9@+_.:~-]+\.pkg\.tar\.zst',row['file'])
            and row['file'] not in files,'Archivo de paquete no válido.')
        require(type(row['bytes']) is int and 0<row['bytes']<=8*1024**3
            and isinstance(row['sha256'],str) and re.fullmatch('[0-9a-f]{64}',row['sha256']),'Tamaño/hash no válido.')
        if artifacts:
            package=path.parent/row['file']; require(trusted(package).st_size==row['bytes'] and digest(package)==row['sha256'],'Paquete incompleto o modificado.')
            require(trusted(Path(str(package)+'.sig')).st_size<=16384,'Firma de paquete no válida.')
        # Normal pacman verifies package signatures against its installed keyring.
        names.add(row['name']);files.add(row['file'])
    return data

def inventory(directory):
    """Private comparison only. Hashes/contents never appear in logs or receipts."""
    result={}
    for base,dirs,files in os.walk(directory,followlinks=False):
        for name in sorted(dirs+files):
            path=Path(base)/name; s=path.lstat(); key=path.relative_to(directory).as_posix()
            # GnuPG may create transient agent sockets in its configuration
            # directory. They are runtime endpoints, never persistent config.
            if stat.S_ISSOCK(s.st_mode):continue
            value=(stat.S_IFMT(s.st_mode),stat.S_IMODE(s.st_mode),s.st_uid,s.st_gid)
            if stat.S_ISLNK(s.st_mode):value+=(os.readlink(path),)
            elif stat.S_ISREG(s.st_mode):value+=(digest(path),)
            result[key]=value
    return result

def database_digest(root):
    # Package metadata only, not accounts, credentials or user application data.
    value=inventory(root/'var/lib/pacman/local')
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

@contextmanager
def private_download_config(root):
    """Use local packages as namespace root, restoring through an anchored fd.

    A package must never redirect the outer process's restore through a
    symlink into the live system. Directory and file descriptors stay anchored
    to the private copy even if its paths are replaced by a package script.
    """
    directory=root/'etc';trusted(directory,True)
    fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    original_stat=os.fstat(fd)
    def read():
        source=os.open('pacman.conf',os.O_RDONLY|os.O_NOFOLLOW,dir_fd=fd)
        try:
            meta=os.fstat(source)
            require(stat.S_ISREG(meta.st_mode) and meta.st_uid==0 and meta.st_nlink==1 and not meta.st_mode&0o022
                and meta.st_size<=1024**2,'Configuración de pacman no confiable.')
            with os.fdopen(os.dup(source),'rb') as f:body=f.read(1024**2+1)
            return body,meta
        finally:os.close(source)
    original,meta=read()
    staged=re.sub(rb'(?m)^[ \t]*DownloadUser[ \t]*=.*$',
        b'# Local files are handled inside the outer preparation sandbox.',original)
    def write(body):
        name='.apollo-config-'+secrets.token_hex(16)
        output=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=fd)
        try:
            with os.fdopen(os.dup(output),'wb') as f:f.write(body);f.flush()
            os.fchown(output,meta.st_uid,meta.st_gid);os.fchmod(output,stat.S_IMODE(meta.st_mode));os.fsync(output)
            os.replace(name,'pacman.conf',src_dir_fd=fd,dst_dir_fd=fd);os.fsync(fd)
        finally:
            os.close(output)
            try:os.unlink(name,dir_fd=fd)
            except FileNotFoundError:pass
    try:
        write(staged)
        try:
            yield
            current=directory.lstat()
            require(stat.S_ISDIR(current.st_mode) and (current.st_dev,current.st_ino)==(original_stat.st_dev,original_stat.st_ino),
                'La publicación sustituyó el directorio de configuración.')
            require(read()[0]==staged,'La publicación requiere migrar la configuración de pacman.')
        finally:write(original)
    finally:os.close(fd)

@contextmanager
def alpm_lock(root):
    path=root/'var/lib/pacman/db.lck'
    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
    token=os.fstat(fd)
    try:
        os.write(fd,(str(os.getpid())+'\n').encode());os.fsync(fd)
        yield
    finally:
        os.close(fd)
        current=path.lstat()
        require((current.st_dev,current.st_ino)==(token.st_dev,token.st_ino),'El bloqueo de ALPM cambió.')
        path.unlink()

class Engine:
    def __init__(self,root=Path('/'),store=STORE,selector=SELECTOR,command=run):
        self.root,self.store,self.selector,self.command=Path(root),Path(store),Path(selector),command

    def call_selector(self,*args):
        return self.command([self.selector,self.store,*args]).strip().splitlines()

    def setup(self):
        require(os.geteuid()==0,'Usa sudo para administrar las actualizaciones.')
        trusted_parents(self.store.parent)
        self.store.mkdir(mode=0o700,exist_ok=True);trusted_parents(self.store)
        (self.store/'deployments').mkdir(mode=0o700,exist_ok=True)
        (self.store/'staging').mkdir(mode=0o700,exist_ok=True)
        for name in ('deployments','staging'):trusted(self.store/name,True)

    @contextmanager
    def lock(self):
        self.setup()
        fd=os.open(self.store/'update.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
        require(trusted(self.store/'update.lock').st_ino==os.fstat(fd).st_ino,'Bloqueo no confiable.')
        try:
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);yield
        finally:os.close(fd)

    def state(self):
        lines=self.call_selector('status')
        require(len(lines)==8,'Estado de arranque no válido.')
        return dict(zip(('good','previous','trial','remaining','launched','token','failures','sequence'),lines))

    def copy(self,source,target):
        trusted(source,True);target.mkdir(mode=0o700)
        self.command(['/usr/bin/cp','-a','--reflink=auto','--one-file-system','--',str(source)+'/.',target],timeout=1800)

    def room(self):
        total=0
        for name in ('usr','opt','etc','var/lib/pacman','var/lib/omamobile/omarchy-patches'):
            path=self.root/name
            if path.exists():total+=int(self.command(['/usr/bin/du','-sx','--block-size=1','--',path]).split()[0])
        require(shutil.disk_usage(self.store).free>total+RESERVE,'Falta espacio para preparar una copia completa.')

    def receipt(self,work,release,data):
        atomic(work/'release.json',json.dumps(data,sort_keys=True,separators=(',',':')).encode()+b'\n')
        marker=f'APOLLO_DEPLOYMENT_2\n{release}\n{os.uname().release}\n{digest(work/"release.json")}\n'.encode()
        # Flush payload BEFORE the final readiness marker and directory rename.
        self.command(['/usr/bin/sync','-f',work],timeout=120)
        atomic(work/'ready-v1',marker)
        destination=self.store/'deployments'/release
        require(not destination.exists(),'Ya existe esa versión.')
        os.rename(work,destination)
        fd=os.open(destination.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
        return destination

    def copy_adapter(self,target):
        source=self.root/'var/lib/omamobile/omarchy-patches'
        if source.exists():self.copy(source,target)
        else:target.mkdir(mode=0o700)

    def bootstrap(self,refresh=False):
        with self.lock(),alpm_lock(self.root):
            if refresh:
                require(not BOOT_CONTRACT.exists(),'No se puede recapturar la base tras activar el nuevo arranque.')
                state=self.state();require(state['sequence']=='0' and state['trial']=='-' and state['launched']=='-','La preparación inicial ya está en uso.')
            else:require(not (self.store/'state-v1').exists(),'El almacén ya está inicializado.')
            self.room();work=Path(tempfile.mkdtemp(prefix='bootstrap-',dir=self.store/'staging'))
            for name,target in (('usr','usr'),('opt','opt'),('var/lib/pacman/local','pacman-local')):
                self.copy(self.root/name,work/target)
            self.copy_adapter(work/'adapter-state')
            release='bootstrap-'+str(__import__('time').time_ns()) if refresh else 'bootstrap'
            result=self.receipt(work,release,{'schema':'apollo-local-bootstrap-2','kernel':os.uname().release})
            if refresh:self.call_selector('reseed',release)
            else:self.call_selector('init');self.call_selector('seed',release)
            return {'prepared':release,'kernel':os.uname().release,'boot_changed':False,'path':str(result)}

    def prepare(self,manifest,keyring=PUB):
        with self.lock(),alpm_lock(self.root):
            data=read_manifest(manifest,self.command,keyring)
            require(data['kernel']==os.uname().release,'El cambio de kernel espera la validación presencial del cargador kexec.')
            state=self.state();require(state['trial']=='-' and state['launched']=='-','Hay un arranque pendiente de confirmar.')
            require(data['sequence']>int(state['sequence']),'Publicación antigua o repetida.')
            require(not (self.store/'deployments'/data['id']).exists(),'La versión ya existe.')
            self.room();work=Path(tempfile.mkdtemp(prefix=data['id']+'-',dir=self.store/'staging'))
            atomic(work/'base-database.sha256',(database_digest(self.root)+'\n').encode())
            sandbox=work/'root';sandbox.mkdir(mode=0o700)
            for path in ('usr','opt','etc','var/lib/pacman'):
                target=sandbox/path;target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
                self.copy(self.root/path,target)
            adapter=sandbox/'var/lib/omamobile/omarchy-patches';adapter.parent.mkdir(parents=True,exist_ok=True)
            self.copy_adapter(adapter)
            for base,dirs,files in os.walk(sandbox/'etc',followlinks=False):
                for name in files:
                    path=Path(base)/name
                    if stat.S_ISSOCK(path.lstat().st_mode):path.unlink()
            # Do not copy /home, app data, firmware partitions, runtime, or sockets.
            (sandbox/'var/lib/pacman/db.lck').unlink(missing_ok=True)
            before=inventory(sandbox/'etc')
            cache=sandbox/'var/cache/pacman/apollo-transaction';cache.mkdir(parents=True,mode=0o700)
            (sandbox/'var/cache/pacman/pkg').mkdir(parents=True,exist_ok=True)
            for row in data['packages']:
                for suffix in ('','.sig'):shutil.copyfile(str(manifest.parent/row['file'])+suffix,str(cache/row['file'])+suffix)
            for path in ('dev','proc','sys','run','tmp','home','root','var/log'):(sandbox/path).mkdir(parents=True,exist_ok=True)
            for link,target in (('bin','usr/bin'),('sbin','usr/bin'),('lib','usr/lib'),('lib64','usr/lib')):(sandbox/link).symlink_to(target)
            hook=sandbox/'etc/pacman.d/hooks/00-apollo-update-compatibility.hook'
            require(not hook.exists() and not hook.is_symlink(),'Hay una excepción previa de la protección de Apollo.')
            hook.parent.mkdir(parents=True,exist_ok=True);hook.symlink_to('/dev/null')
            plan=work/'transaction.json';atomic(plan,json.dumps(data).encode())
            # The transaction body and entire userspace run in isolated mounts,
            # processes, network, /run, /dev, /sys and /home. No live services.
            command=['/usr/bin/bwrap','--unshare-all','--die-with-parent','--new-session',
                '--bind',sandbox,'/','--proc','/proc','--dev','/dev','--tmpfs','/sys',
                '--tmpfs','/run','--tmpfs','/tmp','--ro-bind',plan,'/transaction.json',
                '--ro-bind',Path(__file__).resolve(),'/transaction.py','--clearenv',
                '--setenv','PATH','/usr/bin:/bin','--setenv','LANG','C.UTF-8',
                '--setenv','LC_ALL','C.UTF-8','--setenv','HOME','/root',
                '/usr/bin/python3','-I','-B','/transaction.py','_transaction']
            stable_dirs=('usr','opt','etc','etc/pacman.d','etc/pacman.d/hooks','var','var/lib','var/lib/pacman',
                'var/lib/pacman/local','var/lib/omamobile','var/lib/omamobile/omarchy-patches')
            inodes={name:(trusted(sandbox/name,True).st_dev,(sandbox/name).lstat().st_ino) for name in stable_dirs}
            with private_download_config(sandbox):
                self.command(command,timeout=1800)
            for name,pair in inodes.items():
                current=trusted(sandbox/name,True)
                require((current.st_dev,current.st_ino)==pair,'La publicación sustituyó un directorio del sistema.')
            hook.unlink()
            for name in ('transaction.json','transaction.py'):
                placeholder=sandbox/name;s=placeholder.lstat()
                require(stat.S_ISREG(s.st_mode) and s.st_size==0 and s.st_uid==0 and s.st_nlink==1,'Punto de montaje temporal modificado.')
                placeholder.unlink()
            require(inventory(sandbox/'etc')==before,'La candidata modifica configuración compartida: requiere una migración compatible validada.')
            require(set(p.name for p in sandbox.iterdir())=={'usr','opt','etc','var','dev','proc','sys','run','tmp','home','root','bin','sbin','lib','lib64'},
                'La candidata modifica rutas de arranque o rutas fuera del sistema versionado.')
            require(set(p.name for p in (sandbox/'var').iterdir())=={'lib','cache','log'},'La candidata requiere migrar estado adicional.')
            require(not any((sandbox/'home').iterdir()) and not any((sandbox/'root').iterdir()),'La candidata intenta modificar perfiles de usuario.')
            # Any application database migration must be designed explicitly.
            require(set((sandbox/'var/lib').iterdir())=={sandbox/'var/lib/pacman',sandbox/'var/lib/omamobile'} and
                set((sandbox/'var/lib/omamobile').iterdir())=={adapter},'La candidata requiere migrar datos persistentes.')
            require(not (sandbox/'var/lib/pacman/db.lck').exists(),'La transacción de ALPM quedó incompleta.')
            for source,target in (('usr','usr'),('opt','opt'),('var/lib/pacman/local','pacman-local')):
                os.rename(sandbox/source,work/target)
            os.rename(adapter,work/'adapter-state')
            # Delete the private on-device config copy, never export it.
            require(sandbox.parent==work and work.parent==self.store/'staging','Ruta temporal inesperada.')
            shutil.rmtree(sandbox);plan.unlink()
            shutil.copyfile(manifest,work/'signed-release.json');shutil.copyfile(str(manifest)+'.sig',work/'signed-release.json.sig')
            result=self.receipt(work,data['id'],data)
            return {'prepared':data['id'],'sequence':data['sequence'],'boot_changed':False,'path':str(result)}

    def queue(self,release):
        require(ID.fullmatch(release),'Identificador no válido.')
        with self.lock(),alpm_lock(self.root):
            # Written by the NEW initramfs after mounting ALL versioned paths.
            # Installing the tools alone is not enough to enable this action.
            trusted(BOOT_CONTRACT)
            require(BOOT_CONTRACT.read_text()=='apollo-versioned-usr-1\n','El nuevo arranque todavía no está activo.')
            deployment=self.store/'deployments'/release;trusted(deployment,True)
            base=deployment/'base-database.sha256';trusted(base)
            require(base.read_text().strip()==database_digest(self.root),'Los paquetes instalados cambiaron desde la preparación; hay que preparar otra copia.')
            data=read_manifest(deployment/'signed-release.json',self.command,artifacts=False)
            require(data['id']==release,'Identificador de candidata diferente.')
            self.call_selector('queue',release,str(data['sequence']))
            if REGISTRY.exists():
                trusted(REGISTRY)
                current=json.loads(REGISTRY.read_text())
                if current.get('id')==release:REGISTRY.unlink()
            return {'pending':release,'rebooted':False}

def transaction():
    global TRANSACTION_LOG
    require(os.geteuid()==0,'Root requerido.')
    TRANSACTION_LOG=Path('/var/log/apollo-transaction-private.log')
    data=json.loads(Path('/transaction.json').read_bytes(),object_pairs_hook=json_unique)
    paths=[]
    for row in data['packages']:
        p=Path('/var/cache/pacman/apollo-transaction')/row['file']
        require(digest(p)==row['sha256'],'El paquete cambió durante la preparación.')
        run(['/usr/bin/pacman-key','--verify',str(p)+'.sig',p])
        query=subprocess.run(['/usr/bin/pacman','-Q',row['name']],capture_output=True,text=True)
        if row['from_version'] is None:require(query.returncode==1,'El paquete ya estaba instalado.')
        else:require(query.returncode==0 and query.stdout.strip()==row['name']+' '+row['from_version'],'La base instalada cambió.')
        require(run(['/usr/bin/pacman','-Qp',p]).strip()==row['name']+' '+row['version'],'Metadatos diferentes.')
        paths.append(p)
    plan=run(['/usr/bin/pacman','-U','--noconfirm','--print','--print-format','%n %v',*paths])
    require(sorted(plan.splitlines())==sorted(r['name']+' '+r['version'] for r in data['packages']),'Dependencias fuera de la publicación firmada.')
    run(['/usr/bin/pacman','-U','--noconfirm',*paths],timeout=1200)
    patches=Path('/usr/bin/omamobile-omarchy-patches')
    if patches.is_file():run([patches,'verify'])
    for row in data['packages']:
        require(run(['/usr/bin/pacman','-Q',row['name']]).strip()==row['name']+' '+row['version'],'La instalación no coincide con la publicación.')

def native_platform():
    trusted(Path('/etc/apollo/native-root-v1'))
    require(b'xiaomi,apollo\0' in Path('/proc/device-tree/compatible').read_bytes(),'Dispositivo no compatible.')
    require(run(['/usr/bin/findmnt','-n','-o','FSTYPE','/']).strip()=='ext4','Raíz permanente no reconocida.')
    require(not Path('/etc/apollo/ram-trial').exists(),'No ejecutar desde una prueba en RAM.')

def register(manifest):
    data=read_manifest(manifest)
    require(data['kernel']==os.uname().release,'Esta publicación requiere validar otro kernel.')
    trusted_parents(REGISTRY.parent.parent)
    REGISTRY.parent.mkdir(mode=0o755,exist_ok=True);trusted_parents(REGISTRY.parent)
    value={'schema':1,'manifest':str(manifest),'sha256':digest(manifest),
        'id':data['id'],'sequence':data['sequence'],
        'updates':[r['name']+' '+(r['from_version'] or '(nuevo)')+' -> '+r['version'] for r in data['packages']]}
    atomic(REGISTRY,json.dumps(value,ensure_ascii=False).encode()+b'\n');REGISTRY.chmod(0o644)
    return {'registered':data['id'],'queued':False,'boot_changed':False}

def registered_manifest():
    require(trusted(REGISTRY).st_size<=1024**2,'Registro de publicación no válido.')
    data=json.loads(REGISTRY.read_text(),object_pairs_hook=json_unique)
    require(data.get('schema')==1 and isinstance(data.get('manifest'),str),'Registro de publicación no válido.')
    manifest=Path(data['manifest']);trusted_parents(manifest.parent);trusted(manifest)
    require(digest(manifest)==data['sha256'],'La publicación registrada ha cambiado.')
    return manifest

def fetch(url):
    parsed=urllib.parse.urlsplit(url)
    require(parsed.scheme=='https' and parsed.hostname and parsed.username is None and parsed.password is None
        and not parsed.fragment,'Se requiere una dirección HTTPS pública sin credenciales.')
    parent=Path('/var/cache/pacman');trusted_parents(parent)
    work=Path(tempfile.mkdtemp(prefix='apollo-system-release-',dir=parent))
    class HTTPSRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,request,fp,code,msg,headers,newurl):
            require(urllib.parse.urlsplit(newurl).scheme=='https','Redirección sin HTTPS rechazada.')
            return super().redirect_request(request,fp,code,msg,headers,newurl)
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),HTTPSRedirect())
    def download(source,target,limit):
        request=urllib.request.Request(source,headers={'User-Agent':'Omarchy-Apollo-Updater/0.1'})
        with opener.open(request,timeout=30) as response:
            require(urllib.parse.urlsplit(response.url).scheme=='https','Respuesta sin HTTPS rechazada.')
            fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            with os.fdopen(fd,'wb') as out:
                total=0
                while True:
                    body=response.read(min(1024**2,limit-total+1))
                    if not body:break
                    total+=len(body);require(total<=limit,'La descarga supera el tamaño permitido.')
                    out.write(body)
                out.flush();os.fsync(out.fileno())
    manifest=work/'release.json';download(url,manifest,1024**2);download(url+'.sig',Path(str(manifest)+'.sig'),16384)
    data=read_manifest(manifest,artifacts=False)
    require(data['kernel']==os.uname().release,'La publicación requiere otro kernel todavía no validado.')
    require(shutil.disk_usage(work).free>sum(p['bytes'] for p in data['packages'])+RESERVE,'Falta espacio para descargar la publicación.')
    for row in data['packages']:
        source=urllib.parse.urljoin(url,row['file'])
        download(source,work/row['file'],row['bytes'])
        download(source+'.sig',work/(row['file']+'.sig'),16384)
    read_manifest(manifest)
    return register(manifest)

def main(argv=None):
    parser=argparse.ArgumentParser(description='Actualizaciones de sistema Apollo por versiones recuperables')
    sub=parser.add_subparsers(dest='action',required=True)
    for name in ('status','bootstrap','refresh-bootstrap','rollback','apply-registered'):sub.add_parser(name)
    for name,arg in (('check','manifest'),('prepare','manifest'),('register','manifest'),('fetch','url'),('queue','release')):sub.add_parser(name).add_argument(arg)
    args=parser.parse_args(argv)
    require(os.geteuid()==0,'Ejecuta este comando con sudo.')
    native_platform();engine=Engine()
    if args.action=='check':result={'verified':read_manifest(Path(args.manifest))['id'],'boot_changed':False}
    elif args.action=='bootstrap':result=engine.bootstrap()
    elif args.action=='refresh-bootstrap':result=engine.bootstrap(refresh=True)
    elif args.action=='prepare':result=engine.prepare(Path(args.manifest))
    elif args.action=='register':result=register(Path(args.manifest))
    elif args.action=='fetch':result=fetch(args.url)
    elif args.action=='apply-registered':
        trusted(BOOT_CONTRACT)
        manifest=registered_manifest();data=read_manifest(manifest)
        deployment=STORE/'deployments'/data['id']
        if deployment.exists():
            trusted(deployment,True)
            require(digest(deployment/'signed-release.json')==digest(manifest),'La copia preparada no coincide con la publicación registrada.')
            release=data['id']
        else:release=engine.prepare(manifest)['prepared']
        result=engine.queue(release)
        print('Actualización preparada para el próximo reinicio; el sistema actual sigue en uso.')
    elif args.action=='queue':result=engine.queue(args.release)
    elif args.action=='rollback':
        trusted(BOOT_CONTRACT)
        with engine.lock():engine.call_selector('rollback')
        result={'rollback_pending':True,'rebooted':False}
    else:
        result={'initialized':(STORE/'state-v1').exists(),'boot_integration_active':BOOT_CONTRACT.exists(),
            'kernel':os.uname().release,'kernel_updates_enabled':False}
        if result['initialized']:
            state=engine.state();state.pop('token');result['state']=state
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    try:
        if sys.argv[1:]==['_transaction']:transaction()
        else:main()
    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as error:
        print('Apollo: '+str(error),file=sys.stderr);sys.exit(1)
