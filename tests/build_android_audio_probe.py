#!/usr/bin/env python3
"""Build the synthetic Android audio test fixture with a pinned upstream D8."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile

VERSION = '9.5.28'
COMPILER_SHA256 = '38a9ffaaebbd17d1514e3ecbff5a85b989bb13c551b9e224c7409514eea84ff5'
URL = f'https://dl.google.com/dl/android/maven2/com/android/tools/r8/{VERSION}/r8-{VERSION}.jar'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path, help='New output JAR path')
    args = parser.parse_args()
    assert shutil.which('java') and shutil.which('javac'), 'Use JDK 17 or newer'
    assert not args.output.exists(), 'Refusing to replace an existing fixture'
    source = Path(__file__).resolve().parent / 'support/AndroidAudioProbe.java'
    with tempfile.TemporaryDirectory(prefix='apollo-audio-probe-build-') as temporary:
        root = Path(temporary)
        compiler = root / 'r8.jar'
        with urllib.request.urlopen(URL, timeout=45) as response:
            contents = response.read(128 * 1024 * 1024 + 1)
        assert len(contents) <= 128 * 1024 * 1024
        assert hashlib.sha256(contents).hexdigest() == COMPILER_SHA256, 'Compiler digest mismatch'
        compiler.write_bytes(contents)
        classes = root / 'classes'; classes.mkdir()
        dex = root / 'dex'; dex.mkdir()
        subprocess.run(['javac', '--release', '8', '-d', str(classes), str(source)], check=True)
        expected = classes / 'org/omarchy/apollo/AndroidAudioProbe.class'
        assert list(classes.rglob('*.class')) == [expected]
        subprocess.run(['java', '-cp', str(compiler), 'com.android.tools.r8.D8',
                        '--release', '--min-api', '26', '--output', str(dex), str(expected)], check=True)
        # Only the real probe goes into the fixture; no Android framework stubs.
        with args.output.open('xb') as target:
            with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_STORED) as archive:
                entry = zipfile.ZipInfo('classes.dex', date_time=(2026, 10, 30, 0, 0, 0))
                archive.writestr(entry, (dex / 'classes.dex').read_bytes())
    print('Probe SHA-256:', hashlib.sha256(args.output.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
