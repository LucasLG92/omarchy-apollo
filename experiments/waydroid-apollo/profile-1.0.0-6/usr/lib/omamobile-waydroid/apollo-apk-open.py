#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Review-only APK opener candidate. Default is a non-mutating plan.

Future desktop integration uses --apply as the logged-in user. No init/image
download, sudo, service enablement, root shell or install-success claim.
"""
from pathlib import Path
import argparse
import contextlib
import json
import os
import subprocess
import time
import urllib.parse
import zipfile


def apk_path(value):
    uri = urllib.parse.urlsplit(value)
    if uri.scheme:
        if uri.scheme != 'file' or uri.netloc not in ('', 'localhost'):
            raise ValueError('Primero descarga el APK en el navegador.')
        value = urllib.parse.unquote(uri.path)
    path = Path(value).resolve(strict=True)
    if not path.is_file() or path.suffix.lower() != '.apk':
        raise ValueError('Selecciona un archivo APK local; los paquetes divididos no están admitidos aquí.')
    try:
        with zipfile.ZipFile(path) as archive:
            archive.getinfo('AndroidManifest.xml')
            abis = {name.split('/')[1] for name in archive.namelist()
                    if name.startswith('lib/') and len(name.split('/')) > 2}
    except (zipfile.BadZipFile, KeyError):
        raise ValueError('El archivo no contiene un APK reconocido.') from None
    if abis and not abis & {'arm64-v8a', 'armeabi-v7a', 'armeabi'}:
        raise ValueError('Este APK contiene bibliotecas para otra arquitectura.')
    return path


def request_install(path, backend):
    if not backend.preflight():
        return 'host-not-ready'
    if not backend.app_api_ready():
        backend.open_android()
        deadline = backend.now() + 90
        while backend.now() < deadline:
            if backend.app_api_ready(): break
            backend.pause(1)
        else: return 'android-not-ready'
    # The official CLI can return zero while reporting an internal failure.
    # Never turn its zero status into a claim that the app was installed.
    return 'request-submitted-not-verified' if backend.install(path) == 0 else 'request-failed'


class Backend:
    now = staticmethod(time.monotonic)
    pause = staticmethod(time.sleep)

    def preflight(self):
        if not Path('/var/lib/waydroid/waydroid.cfg').is_file() or not Path('/var/lib/waydroid/rootfs').is_dir():
            return False
        try:
            result = subprocess.run(['/usr/lib/omamobile-waydroid/omamobile-waydroid-check', '--running'],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
            return result.returncode == 0
        except (OSError, subprocess.TimeoutExpired): return False

    def app_api_ready(self):
        try:
            result = subprocess.run(['/usr/bin/waydroid', 'app', 'list'], stdout=subprocess.PIPE,
                                    stderr=subprocess.DEVNULL, timeout=4)
            # Names remain transient in memory; do not log/persist them.
            return result.returncode == 0 and b'packageName:' in result.stdout
        except (OSError, subprocess.TimeoutExpired): return False

    def open_android(self):
        subprocess.Popen(['/usr/bin/waydroid', 'session', 'start'], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, close_fds=True, start_new_session=True)

    def install(self, path):
        try:
            return subprocess.run(['/usr/bin/waydroid', 'app', 'install', str(path)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180).returncode
        except (OSError, subprocess.TimeoutExpired): return -1


@contextlib.contextmanager
def install_lock():
    import fcntl
    runtime = Path(os.environ.get('XDG_RUNTIME_DIR', ''))
    if not runtime.is_absolute() or not runtime.is_dir() or runtime.stat().st_uid != os.getuid():
        raise ValueError('No se ha encontrado la sesión gráfica del usuario.')
    descriptor = os.open(runtime / 'apollo-waydroid-apk.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally: os.close(descriptor)


def notify(message):
    try:
        subprocess.run(['/usr/bin/notify-send', '--app-name=Android', 'APK en Omarchy', message],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
    except (OSError, subprocess.TimeoutExpired): pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('apk')
    args = parser.parse_args()
    try:
        path = apk_path(args.apk)
        if not args.apply:
            print(json.dumps({'local_apk_validated': True, 'plan_only': True,
                              'would_use_existing_waydroid_session_then_official_app_install': True,
                              'images_or_packages_downloaded': 0}))
            return
        if os.geteuid() == 0: raise ValueError('Abre el APK desde la sesión gráfica normal del usuario.')
        with install_lock(): result = request_install(path, Backend())
        messages = {
            'host-not-ready': 'Android necesita completar la preparación del sistema antes de instalar APK.',
            'android-not-ready': 'Android todavía no está listo. Ábrelo y vuelve a tocar el APK cuando termine de iniciar.',
            'request-failed': 'No se pudo completar la solicitud de instalación. Comprueba el resultado en Android.',
            'request-submitted-not-verified': 'Solicitud enviada a Android. Comprueba el resultado y abre la aplicación desde su lanzador.',
        }
        notify(messages[result])
    except BlockingIOError: notify('Hay otra instalación APK en curso.')
    except (OSError, ValueError) as error:
        # Avoid exposing filesystem paths or upstream diagnostic output.
        notify(str(error) if isinstance(error, ValueError) else 'No se puede abrir este APK local.')


if __name__ == '__main__': main()
