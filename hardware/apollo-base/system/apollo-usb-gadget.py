#!/usr/bin/python3
# SPDX-License-Identifier: GPL-2.0-only
"""Prepare Apollo's NCM link after switch_root without disrupting a bound link."""
from pathlib import Path
import errno
import fcntl
import json
import os
import sys


class Refused(RuntimeError):
    """An existing configuration differs from this service's ownership contract."""


class Gadget:
    DEVICE_MAC = '02:42:61:70:6f:01'
    HOST_MAC = '02:42:61:70:6f:02'
    # composite.c reports USB 2.01 on this HS controller when LPM is available.
    # It changes the stored descriptor during GET_DESCRIPTOR after binding.
    RUNTIME_NUMBERS = {'bcdUSB': {0x0201}}
    NUMBERS = {
        'idVendor': (0x1d6b, {0}),
        'idProduct': (0x0104, {0}),
        'bcdUSB': (0x0200, {0}),
        'bDeviceClass': (0xef, {0}),
        'bDeviceSubClass': (2, {0}),
        'bDeviceProtocol': (1, {0}),
    }
    STRINGS = {
        'serialnumber': 'apollo-linux',
        'manufacturer': 'Apollo development',
        'product': 'Apollo Linux USB maintenance',
    }

    def __init__(self, configfs=Path('/sys/kernel/config/usb_gadget'),
                 controllers=Path('/sys/class/udc')):
        self.root = configfs
        self.controllers = controllers
        self.path = self.root / 'apollo'

    def read(self, path):
        return path.read_text().strip()

    def read_mac(self, path):
        # The NCM address show method on this kernel includes its trailing NUL.
        return self.read(path).removesuffix('\0').lower()

    def write(self, path, value):
        path.write_text(str(value) + '\n')

    def mkdir(self, path):
        path.mkdir(exist_ok=True)

    def number(self, path):
        value = self.read(path)
        return int(value, 16 if value.lower().startswith('0x') else 10)

    def validate(self, bound):
        g = self.path
        for name, (expected, defaults) in self.NUMBERS.items():
            allowed = {expected} | self.RUNTIME_NUMBERS.get(name, set())
            if not bound:
                allowed |= defaults
            if self.number(g/name) not in allowed:
                raise Refused('Unexpected USB descriptor: ' + name)
        language = g/'strings/0x409'
        if language.exists():
            for name, expected in self.STRINGS.items():
                if self.read(language/name) not in ({expected} if bound else {'', expected}):
                    raise Refused('Unexpected USB string descriptor: ' + name)
        elif bound:
            raise Refused('Bound gadget is missing its identity')
        for parent, allowed in (('configs', {'c.1'}), ('functions', {'ncm.usb0'})):
            if any(p.name not in allowed for p in (g/parent).iterdir()):
                raise Refused('Unexpected USB configuration or function')
        config = g/'configs/c.1'
        if config.exists():
            link = config/'ncm.usb0'
            if link.exists() and not link.is_symlink():
                raise Refused('The NCM link is occupied by another entry')
            links = [p for p in config.iterdir() if p.is_symlink()]
            if any(p.name != 'ncm.usb0' or p.resolve() != (g/'functions/ncm.usb0').resolve()
                   for p in links):
                raise Refused('Unexpected USB function link')
            if bound and len(links) != 1:
                raise Refused('Bound gadget does not contain the NCM function')
            maximum = self.number(config/'MaxPower')
            if maximum not in ({250} if bound else {2, 250}):
                raise Refused('Unexpected USB power descriptor')
        elif bound:
            raise Refused('Bound gadget is missing its configuration')
        function = g/'functions/ncm.usb0'
        if bound and (not function.is_dir()
                      or self.read_mac(function/'dev_addr') != self.DEVICE_MAC
                      or self.read_mac(function/'host_addr') != self.HOST_MAC):
            raise Refused('Bound gadget has unexpected NCM addresses')

    def ensure(self):
        if not self.root.is_dir():
            raise OSError(errno.ENODEV, 'USB configfs is not ready')
        controllers = sorted(p.name for p in self.controllers.iterdir())
        if len(controllers) > 1:
            raise Refused('Multiple USB controllers require an explicit board configuration')
        if self.path.exists():
            bound = bool(self.read(self.path/'UDC'))
            self.validate(bound)
            if bound:
                # Never unbind or rewrite an active gadget during service restarts.
                return 'already-bound'
        foreign = {self.read(p/'UDC') for p in self.root.iterdir()
                   if p != self.path and (p/'UDC').is_file()}
        if controllers and controllers[0] in foreign:
            raise Refused('USB controller is owned by another gadget')
        self.mkdir(self.path)
        for name, (expected, _) in self.NUMBERS.items():
            if self.number(self.path/name) != expected:
                self.write(self.path/name, hex(expected))
        language = self.path/'strings/0x409'
        self.mkdir(language)
        for name, value in self.STRINGS.items():
            if self.read(language/name) != value:
                self.write(language/name, value)
        config = self.path/'configs/c.1'
        self.mkdir(config)
        self.mkdir(config/'strings/0x409')
        if self.read(config/'strings/0x409/configuration') != 'USB network':
            self.write(config/'strings/0x409/configuration', 'USB network')
        if self.number(config/'MaxPower') != 250:
            self.write(config/'MaxPower', 250)
        function = self.path/'functions/ncm.usb0'
        self.mkdir(function)
        for name, value in (('dev_addr', self.DEVICE_MAC), ('host_addr', self.HOST_MAC)):
            if self.read_mac(function/name) != value:
                self.write(function/name, value)
        link = config/'ncm.usb0'
        if not link.is_symlink():
            link.symlink_to(function)
        self.validate(False)
        if not controllers:
            # An add event from the UDC starts this service again. No polling on battery.
            return 'waiting-controller'
        self.write(self.path/'UDC', controllers[0])
        if self.read(self.path/'UDC') != controllers[0]:
            raise OSError(errno.EIO, 'USB controller binding did not persist')
        return 'bound'


def main():
    if sys.argv[1:] != ['ensure'] or os.geteuid() != 0:
        raise SystemExit('Run as root: apollo-usb-gadget ensure')
    compatible = Path('/proc/device-tree/compatible').read_bytes().split(b'\0')
    if b'xiaomi,apollo' not in compatible or not Path('/run/apollo-persistent').is_file():
        raise SystemExit('This service requires an installed Apollo system')
    fd = os.open('/run/apollo-usb-gadget.lock', os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            status = Gadget().ensure()
        except Refused as error:
            print(str(error), file=sys.stderr)
            return 2
        except (OSError, ValueError) as error:
            print('USB setup will retry; error ' + str(getattr(error, 'errno', 'attribute')), file=sys.stderr)
            return 75
        print(json.dumps({'usb_maintenance': status, 'network_configuration': 'systemd-networkd'}))
        return 0
    finally:
        os.close(fd)


if __name__ == '__main__':
    raise SystemExit(main())
