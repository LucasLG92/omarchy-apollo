#!/bin/sh
# SPDX-License-Identifier: MIT
# Source from the validated native initramfs AFTER mounting the physical root.
# The existing UFS allowlist, charger path and root identity checks stay first.
apollo_bind_generation() {
    apollo_root=$1
    apollo_run=$2
    apollo_selector=$3
    apollo_store=$apollo_root/var/lib/apollo/system-versions
    [ -f "$apollo_store/state-v1" ] || return 0
    [ -x "$apollo_selector" ] || return 0
    umask 077
    if ! "$apollo_selector" "$apollo_store" select > "$apollo_run/apollo-select"; then
        rm -f "$apollo_run/apollo-select"
        return 0
    fi
    { IFS= read -r apollo_id; IFS= read -r apollo_token; } < "$apollo_run/apollo-select"
    rm -f "$apollo_run/apollo-select"
    printf 'apollo-versioned-usr-1\n' > "$apollo_run/apollo-versioned-usr-v1"
    [ "$apollo_id" != - ] || return 0
    case "$apollo_id" in ''|*[!a-z0-9_-]*) return 0;; esac
    case "$apollo_token" in ''|*[!0-9a-f]*) return 0;; esac
    [ "${#apollo_token}" = 64 ] || return 0
    apollo_generation=$apollo_store/deployments/$apollo_id
    [ -f "$apollo_generation/usr/lib/systemd/system/apollo-deployment-health.service" ] || return 0
    # A mount failure always unwinds in reverse order to the physical system.
    if ! mount --bind "$apollo_generation/usr" "$apollo_root/usr"; then return 0; fi
    if ! mount --bind "$apollo_generation/opt" "$apollo_root/opt"; then
        umount "$apollo_root/usr" || return 1
        return 0
    fi
    if ! mount --bind "$apollo_generation/pacman-local" "$apollo_root/var/lib/pacman/local"; then
        umount "$apollo_root/opt" || return 1
        umount "$apollo_root/usr" || return 1
        return 0
    fi
    if [ -d "$apollo_generation/adapter-state" ]; then
        if ! mount --bind "$apollo_generation/adapter-state" "$apollo_root/var/lib/omamobile/omarchy-patches"; then
            umount "$apollo_root/var/lib/pacman/local" || return 1
            umount "$apollo_root/opt" || return 1
            umount "$apollo_root/usr" || return 1
            return 0
        fi
    fi
    printf '%s\n%s\n' "$apollo_id" "$apollo_token" > "$apollo_run/apollo-deployment-v1"
    mkdir -p "$apollo_run/systemd/system/multi-user.target.wants"
    ln -s /usr/lib/systemd/system/apollo-deployment-health.service \
        "$apollo_run/systemd/system/multi-user.target.wants/apollo-deployment-health.service" || return 1
    return 0
}
