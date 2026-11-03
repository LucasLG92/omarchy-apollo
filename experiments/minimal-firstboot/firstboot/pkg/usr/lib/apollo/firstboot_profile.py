# SPDX-License-Identifier: MIT
"""Non-secret first-run preferences; never receives or stores a credential."""
import re
from pathlib import Path
LOCALES={'es_ES.UTF-8':'es-MX','es_MX.UTF-8':'es-MX','en_US.UTF-8':'en-US'}
KEYBOARDS={'es','latam','us'}
OPTIONAL_APPS={'org.gnome.Calculator','org.gnome.Maps','org.gnome.TextEditor','org.gnome.Fractal','de.schmidhuberj.Flare','dev.luminusos.ZapTide'}
FIELDS={'schema','display_name','hostname','locale','timezone','keyboard','apps'}
def validate_profile(value):
    if not isinstance(value,dict) or set(value)!=FIELDS or type(value['schema']) is not int or value['schema']!=1:raise ValueError('INVALID_PROFILE')
    name=value['display_name']
    if not isinstance(name,str) or len(name)>80 or any(ord(c)<32 or c in ':\x7f' for c in name):raise ValueError('INVALID_PROFILE')
    try: name.encode('utf-8','strict')
    except UnicodeError: raise ValueError('INVALID_PROFILE') from None
    if not isinstance(value['hostname'],str) or not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',value['hostname']):raise ValueError('INVALID_PROFILE')
    if not isinstance(value['locale'],str) or not isinstance(value['keyboard'],str) or value['locale'] not in LOCALES or value['keyboard'] not in KEYBOARDS:raise ValueError('INVALID_PROFILE')
    zone=value['timezone']
    if not isinstance(zone,str) or not re.fullmatch(r'(?:UTC|[A-Za-z_+-]+(?:/[A-Za-z0-9_+.-]+){1,3})',zone) or any(p in ('.','..') for p in zone.split('/')):raise ValueError('INVALID_PROFILE')
    apps=value['apps']
    if not isinstance(apps,list) or len(apps)>len(OPTIONAL_APPS) or any(not isinstance(a,str) or a not in OPTIONAL_APPS for a in apps) or len(set(apps))!=len(apps):raise ValueError('INVALID_PROFILE')
    return {**value,'apps':sorted(apps)}
