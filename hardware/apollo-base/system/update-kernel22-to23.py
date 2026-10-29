#!/usr/bin/python3
# SPDX-License-Identifier: GPL-2.0-only
"""Native Apollo 22 -> 23 update, with complete boot-partition rollback.

Requires the private candidate/recovery pair and a successful native trial.
Importing this module does not access phone hardware.
"""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import signal
import stat
import struct
import subprocess
import sys
import time


def digest_fd(fd, size):
    digest = hashlib.sha256()
    offset = 0
    while offset < size:
        data = os.pread(fd, min(1024*1024, size-offset), offset)
        if not data:
            raise OSError('Short read from boot partition')
        digest.update(data)
        offset += len(data)
    return digest.hexdigest()


def digest_file(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_image(fd, path):
    offset = 0
    with path.open('rb') as stream:
        while data := stream.read(1024*1024):
            written = 0
            while written < len(data):
                amount = os.pwrite(fd, data[written:], offset+written)
                if amount <= 0:
                    raise OSError('Short write to boot partition')
                written += amount
            offset += len(data)
    os.fsync(fd)


def update_with_rollback(fd, image, backup, partition_size, install, restore_package):
    """The descriptor must already be exclusively opened and model-checked."""
    if image.stat().st_size <= 0 or image.stat().st_size >= partition_size:
        raise ValueError('Candidate does not fit the boot partition')
    expected_new = digest_file(image)
    original = digest_fd(fd, partition_size)
    if backup.exists():
        if backup.stat().st_size != partition_size or digest_file(backup) != original:
            raise ValueError('Existing recovery backup differs from current boot partition')
    else:
        with backup.open('xb') as stream:
            os.chmod(backup, 0o600)
            offset = 0
            while offset < partition_size:
                data = os.pread(fd, min(1024*1024, partition_size-offset), offset)
                if not data:
                    raise OSError('Short read while preserving boot partition')
                stream.write(data)
                offset += len(data)
            stream.flush()
            os.fsync(stream.fileno())
        if digest_file(backup) != original:
            raise OSError('Recovery backup verification failed')
    try:
        install()
        write_image(fd, image)
        if digest_fd(fd, image.stat().st_size) != expected_new:
            raise OSError('Candidate boot readback mismatch')
    except BaseException:
        # Restore the full partition, including the tail past the older image.
        if digest_fd(fd, partition_size) != original:
            write_image(fd, backup)
        if digest_fd(fd, partition_size) != original:
            raise OSError('Boot rollback verification failed')
        restore_package()
        raise
    return {'boot_write_and_readback_verified': True,
            'full_partition_backup_verified': True,
            'original_partition_sha256': original,
            'new_boot_sha256': expected_new}


def main():
    if not __debug__ or os.geteuid() != 0 or sys.argv[1:] not in (['plan'], ['apply']):
        raise SystemExit('Run on Apollo as root: update-kernel22-to23.py plan|apply')
    root = Path('/run/apollo-storage')
    directory = root/'maintenance/kernel23'
    assert Path('/run/apollo-persistent').is_file()
    assert (root/'.apollo-storage-v1').read_text() == 'apollo-persistent-v1\n'
    assert b'xiaomi,apollo' in Path('/proc/device-tree/compatible').read_bytes().split(b'\0')
    assert bytes.fromhex('7e9ea4d88a1164b012b16b1d34f1c8ec416207d7') in Path('/sys/kernel/notes').read_bytes()
    assert subprocess.check_output(['findmnt', '-n', '-o', 'FSTYPE', str(root)], text=True).strip() == 'ext4'
    assert subprocess.check_output(['pacman', '-Q', 'linux-apollo'], text=True).strip() == 'linux-apollo 7.1.0-22'
    manifest = json.loads((directory/'upgrade-manifest.json').read_text())
    expected_files = {'boot-persistent.img', 'known-good-kernel22-r4.img',
                      'linux-apollo-7.1.0-22-aarch64.pkg.tar.xz',
                      'linux-apollo-7.1.0-23-aarch64.pkg.tar.xz'}
    assert set(manifest) == expected_files
    for name, item in manifest.items():
        path = directory/name
        assert path.stat().st_size == item['size'] and digest_file(path) == item['sha256']
    usb = json.loads((directory/'usb-deployment-manifest.json').read_text())
    for item in usb['files'].values():
        assert digest_file(Path(item['destination'])) == item['sha256']
    assert subprocess.check_output(['systemctl', 'is-enabled', 'apollo-usb-gadget.service'], text=True).strip() == 'enabled'
    assert int(Path('/sys/class/power_supply/qcom-battery/capacity').read_text()) >= 30
    nodes = [p.parent.name for p in Path('/sys/class/block').glob('*/uevent')
             if 'PARTNAME=boot' in p.read_text().splitlines()]
    assert len(nodes) == 1
    sysfs = Path('/sys/class/block')/nodes[0]
    device = Path('/dev')/nodes[0]
    size = 134217728
    assert stat.S_ISBLK(device.stat().st_mode)
    assert int((sysfs/'size').read_text())*512 == size
    assert (sysfs/'ro').read_text().strip() == '0' and not list((sysfs/'holders').iterdir())
    lock_fd = os.open('/run/apollo-kernel-upgrade.lock', os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW, 0o600)
    fcntl.flock(lock_fd, fcntl.LOCK_EX|fcntl.LOCK_NB)
    fd = os.open(device, os.O_RDWR|os.O_EXCL)
    try:
        assert os.fstat(fd).st_rdev == device.stat().st_rdev
        assert struct.unpack('Q', fcntl.ioctl(fd, 0x80081272, b'\0'*8))[0] == size
        old = manifest['known-good-kernel22-r4.img']
        assert digest_fd(fd, old['size']) == old['sha256']
        time.sleep(0.2)
        assert digest_fd(fd, old['size']) == old['sha256']
        if sys.argv[1] == 'plan':
            print(json.dumps({'preflight_passed': True, 'known_boot22_verified_twice': True,
                              'running_trial23_verified': True, 'usb_integration_verified': True,
                              'partition_write_requested': False}))
            return
        gate = json.loads((directory/'accepted-native-trial.json').read_text())
        assert gate['boot_id_sha256'] == hashlib.sha256(Path('/proc/sys/kernel/random/boot_id').read_bytes()).hexdigest()
        assert gate['candidate_boot_sha256'] == manifest['boot-persistent.img']['sha256']
        for required in ('display144', 'cameras_before_and_after', 'gpu_render',
                         'focus_before_and_after', 'front_power_cycles', 'rtc_suspend_resume',
                         'wireplumber_restored', 'clock_warnings_absent'):
            assert gate[required], required

        def package(version, logfile):
            with (directory/logfile).open('wb') as log:
                subprocess.run(['pacman', '-U', '--noconfirm',
                                str(directory/f'linux-apollo-7.1.0-{version}-aarch64.pkg.tar.xz')],
                               stdout=log, stderr=subprocess.STDOUT, check=True)
                subprocess.run(['depmod', '7.1.0'], stdout=log, stderr=subprocess.STDOUT, check=True)
                subprocess.run(['pacman', '-Qkk', 'linux-apollo'], stdout=log, stderr=subprocess.STDOUT, check=True)

        def interrupted(*args):
            raise InterruptedError('Update interrupted; restoring recovery pair')
        signal.signal(signal.SIGTERM, interrupted)
        signal.signal(signal.SIGINT, interrupted)
        result = update_with_rollback(fd, directory/'boot-persistent.img',
                                      directory/'kernel22-full-boot-partition.img', size,
                                      lambda: package(23, 'package23-install.log'),
                                      lambda: package(22, 'package22-rollback.log'))
        result.update({'installed_package': 'linux-apollo 7.1.0-23',
                       'userdata_formatted': False, 'dtbo_modified': False,
                       'reboot_not_requested': True})
        (directory/'transaction-result.json').write_text(json.dumps(result, indent=2)+'\n')
        os.sync()
        print(json.dumps(result))
    finally:
        os.close(fd)
        os.close(lock_fd)


if __name__ == '__main__':
    main()
