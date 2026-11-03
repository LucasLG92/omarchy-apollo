# SPDX-License-Identifier: MIT
import subprocess
from owner_account import validate_record


def set_mode(record, mode):
    if mode not in ('pin', 'password'):
        return False
    owner = validate_record(record)
    # This child has no supplementary groups and is UID1000 before it touches
    # any user-controlled home component. No credential values cross this API.
    result = subprocess.run(['/usr/bin/python3', '-I', '/usr/lib/apollo/owner-mode-apply', mode],
                            user=owner['uid'], group=owner['gid'], extra_groups=[],
                            env={'PATH': '/usr/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'},
                            cwd='/', stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, timeout=5)
    return result.returncode == 0
