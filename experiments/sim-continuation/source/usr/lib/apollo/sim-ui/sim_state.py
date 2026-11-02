# SPDX-License-Identifier: MIT
"""Pure, identity-free ModemManager snapshot and primary-PIN classification.

Never read subscriber identifiers, switch slots, reset a modem or submit a PIN.
The current SIM path is transient routing data, not a stable card identifier.
"""
from dataclasses import dataclass
import re

BUS = 'org.freedesktop.ModemManager1'
MODEM = BUS + '.Modem'
SIM = BUS + '.Sim'
SIM_PATH = re.compile(r'/org/freedesktop/ModemManager1/SIM/[0-9]+\Z')


def valid_sim(path):
    return isinstance(path, str) and SIM_PATH.fullmatch(path) is not None


@dataclass(frozen=True)
class Snapshot:
    current: str
    lock: int
    remaining: int | None
    slots: tuple | None
    active: bool | None
    slot_active: tuple
    stable: bool


def read_snapshot(get, modem):
    """Only allowlisted MM properties; safe to run outside the GTK thread.

    SimSlots can be unavailable on older plugins. A current SIM absent from the
    slot array is not added as another card: proxies can be recreated. Active
    is read separately from every occupied slot and the current SIM. Stale
    proxies yield unknown Active rather than a second PIN request.
    """
    current = get(modem, MODEM, 'Sim')
    try:
        raw_slots = get(modem, MODEM, 'SimSlots')
        slots = tuple(raw_slots) if isinstance(raw_slots, (list, tuple)) else None
    except Exception:
        slots = None
    lock = get(modem, MODEM, 'UnlockRequired')
    retries = get(modem, MODEM, 'UnlockRetries')
    remaining = retries.get(2) if isinstance(retries, dict) else None
    if type(remaining) is not int or remaining < 0:
        remaining = None
    paths = list(dict.fromkeys(p for p in (slots or ()) if valid_sim(p)))
    if valid_sim(current) and current not in paths:
        paths.append(current)
    active = {}
    for path in paths:
        try:
            value = get(path, SIM, 'Active')
            active[path] = value if type(value) is bool else None
        except Exception:
            active[path] = None
    # Do not use a snapshot straddling a modem reprobe or state transition.
    stable = (get(modem, MODEM, 'Sim') == current and
              get(modem, MODEM, 'UnlockRequired') == lock)
    if slots is not None:
        try:
            stable = stable and tuple(get(modem, MODEM, 'SimSlots')) == slots
        except Exception:
            stable = False
    return Snapshot(current, lock, remaining, slots, active.get(current),
                    tuple(active.get(p) for p in (slots or ())), stable)


def card_count(snapshot):
    """Count occupied reported positions, never union(SimSlots, currentSim)."""
    slots = snapshot.slots
    if slots is None or not slots or len(slots) > 2:
        return None
    if any(p != '/' and not valid_sim(p) for p in slots):
        return None
    occupied = [p for p in slots if p != '/']
    if len(set(occupied)) != len(occupied):
        return None
    return len(occupied)


def inventory_text(snapshot):
    count = card_count(snapshot)
    if count == 1:
        return '1 tarjeta detectada'
    if count == 2:
        return '2 tarjetas detectadas'
    if count == 0:
        return 'No hay tarjetas detectadas'
    return 'Estado de las tarjetas sin confirmar'


def classify(snapshot, send_blocked=False):
    """Return (kind, message). Only 'pin' may expose primary-PIN controls."""
    if send_blocked:
        return ('blocked', 'No se reenviará el PIN en esta ventana. Cierra y vuelve a abrir para comprobar el estado.')
    if not snapshot.stable:
        return ('checking', 'La SIM está actualizando su estado. Pulsa «Comprobar SIM».')
    if not valid_sim(snapshot.current) or card_count(snapshot) == 0:
        return ('unavailable', 'No hay una SIM principal disponible.')
    if snapshot.active is not True:
        return ('inactive', 'La SIM principal todavía no está activa. Pulsa «Comprobar SIM».')
    if snapshot.lock in (3, 5):
        return ('secondary', 'La tarjeta no solicita el PIN principal. PIN2 y PUK2 corresponden a funciones adicionales de esa tarjeta; no indican otra SIM.')
    if snapshot.lock == 1:
        return ('unlocked', 'La tarjeta no solicita el PIN principal.')
    if snapshot.lock == 4 or snapshot.remaining == 0:
        return ('puk', 'La tarjeta requiere el PUK. No se enviarán más PIN desde esta pantalla.')
    if snapshot.lock != 2:
        return ('unavailable', 'La tarjeta no está solicitando su PIN principal.')
    attempts = ('Intentos restantes: ' + str(snapshot.remaining)
                if snapshot.remaining is not None else 'El módem no informa de los intentos restantes.')
    return ('pin', 'Introduce el PIN de la SIM principal. ' + attempts)
