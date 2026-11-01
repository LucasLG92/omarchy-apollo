#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Offline publication checks. No device access, downloads or personal data."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import urllib.parse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def tracked_files():
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT, check=True, capture_output=True,
    )
    return sorted(set(p.decode("utf-8") for p in result.stdout.split(b"\0") if p))


def document_links(path):
    text = path.read_text(encoding="utf-8")
    # Code samples are not rendered navigation.
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    targets = re.findall(r"!?\[[^\]]*\]\(([^\s)]+)(?:\s+\"[^\"]*\")?\)", text)
    targets += re.findall(r"(?:href|src)=[\"']([^\"']+)[\"']", text)
    for target in targets:
        parsed = urllib.parse.urlsplit(target)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        local = (path.parent / urllib.parse.unquote(parsed.path)).resolve()
        if not local.is_relative_to(ROOT):
            raise AssertionError(f"Link escapes repository: {path.relative_to(ROOT)}")
        if not local.exists():
            raise AssertionError(f"Broken link in {path.relative_to(ROOT)}: {target}")


def svg_assets(files):
    for name in files:
        if not name.endswith(".svg"):
            continue
        path = ROOT / name
        svg = ET.parse(path).getroot()
        if name == "media/hero.svg":
            assert svg.attrib["viewBox"] == "0 0 1280 640"
            assert svg.attrib.get("role") == "img"
            assert svg.find("{http://www.w3.org/2000/svg}title") is not None
            assert svg.find("{http://www.w3.org/2000/svg}desc") is not None
        for element in svg.iter():
            assert element.tag.rsplit("}", 1)[-1] not in {"script", "foreignObject"}, name
            assert not any(key.lower().startswith("on") for key in element.attrib), name
            for key, value in element.attrib.items():
                if key.rsplit("}", 1)[-1] == "href":
                    assert value.startswith("#"), name


def evidence_boundaries():
    records = {}
    for trial in ("r9", "r10", "r11"):
        data = json.loads((ROOT / f"docs/evidence/2026-11-01-{trial}.json").read_text(encoding="utf-8"))
        assert data["evidence_type"] == "sanitized supervised-device result summary"
        for field in (
            "permanent_installation_complete", "userdata_formatted",
            "full_phone_functionality_verified", "independent_reproduction",
            "device_identifiers_included", "raw_logs_included",
            "private_camera_images_included", "calibration_or_firmware_included",
        ):
            assert data[field] is False, (trial, field)
        assert data["sim_available"] is False
        assert data["original_boot_readback_verified"] is True
        assert data["original_dtbo_readback_verified"] is True
        records[trial] = data
    assert records["r9"]["all_four_cameras_delivered_640x480_frames"]
    assert not records["r9"]["torch_visible_light_confirmed_by_user"]
    assert not records["r9"]["main_optical_focus_quality_verified"]
    assert records["r10"]["physical_cma_mebibytes"] == 256
    assert [v["actual_rgb_dimensions"] for v in records["r10"]["native_rgb_captures"]] == [[3000, 2256], [4200, 3120]]
    assert not records["r10"]["full_108_megapixel_mode_available"]
    assert not records["r10"]["standalone_reboot_reliability_proven"]
    latest = records["r11"]
    assert latest["active_user_voice_permission_passed"] and latest["active_user_message_permission_passed"]
    assert latest["daemon_administration_still_requires_admin_authentication"]
    assert latest["firmware_changes_still_require_admin_authentication"]
    assert latest["read_only_call_list_succeeded"]
    assert latest["pending_authentication_jobs"] == 0
    assert not latest["calls_placed"] and not latest["messages_sent"]
    assert not latest["wifi_connection_confirmed"] and not latest["bluetooth_pairing_tested"]


def privacy_tripwires(files):
    # Tripwires supplement manual review; they cannot prove that arbitrary
    # screenshots, prose or diagnostics contain no personal information.
    patterns = (
        r"-----BEGIN(?: [A-Z]+)? PRIVATE KEY-----",
        r"\bgh[pousr]_[A-Za-z0-9]{30,}\b",
        r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{40,}\b",
        r"(?i)\b[A-Z]:[\\/]Users[\\/](?!Public\b|user\b|<)",
        r"(?i)\b(?:imei|imsi|iccid)\s*[:=]\s*[\"']?[0-9]{8,}",
        r"(?i)\b(?:adb|fastboot)(?:\.exe)?\s+-s\s+[a-f0-9]{8,}\b",
    )
    for name in files:
        path = ROOT / name
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError:
            continue
        assert not any(re.search(pattern, text) for pattern in patterns), f"Review possible private data: {name}"
    assert not any(Path(name).suffix in {".img", ".sqfs", ".squashfs", ".bin", ".tar", ".gz", ".zst"} for name in files)
    assert not any(part in {"private", "logs"} for name in files for part in Path(name).parts)


def source_manifest(files):
    manifest = json.loads((ROOT / "SOURCE-SHA256.json").read_text(encoding="utf-8"))
    expected = {name for name in files if name != "SOURCE-SHA256.json"}
    assert set(manifest) == expected, "Source manifest must cover every public file except itself"
    for name, checksum in manifest.items():
        assert re.fullmatch(r"[0-9a-f]{64}", checksum), name
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == checksum, name


def main():
    files = tracked_files()
    for name in files:
        if name.endswith(".md"):
            document_links(ROOT / name)
    svg_assets(files)
    evidence_boundaries()
    privacy_tripwires(files)
    source_manifest(files)
    print(f"Public checks passed: {len(files)} files, links, SVGs, evidence boundaries, privacy tripwires and source hashes.")
    print("These checks do not establish device functionality or replace manual privacy review.")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, KeyError, ValueError, ET.ParseError) as error:
        print(f"Publication check failed: {error}", file=sys.stderr)
        raise SystemExit(1)
