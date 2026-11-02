#!/usr/bin/python3
# SPDX-License-Identifier: MIT
"""Check the two preloaded official images without downloading or mounting."""
from pathlib import Path
import hashlib
import json
import os
import stat


def main():
    assert os.geteuid()==0
    contract=Path('/usr/share/omamobile-waydroid/apollo-images.json')
    rows=json.loads(contract.read_text())['images']
    base=Path('/etc/waydroid-extra/images')
    for directory in (base,*base.parents):
        info=directory.lstat();assert stat.S_ISDIR(info.st_mode) and info.st_uid==info.st_gid==0 and not info.st_mode&0o022
    for row in rows:
        assert row['name'] in ('system.img','vendor.img')
        path=base/row['name'];info=path.lstat()
        assert stat.S_ISREG(info.st_mode) and info.st_uid==info.st_gid==0 and info.st_nlink==1 and not info.st_mode&0o022
        assert info.st_size==row['bytes']
        with path.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==row['sha256']
    print('Official preloaded ARM64 images verified; no downloads or mounts.')


if __name__=='__main__':main()
