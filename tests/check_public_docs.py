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
    for trial in ("r9", "r10", "r11", "r12"):
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
    haptics = records["r12"]
    assert haptics["kernel_release"] == "7.1.0-apollo-native-r6"
    assert haptics["user_confirmed_physical_vibration"]
    assert haptics["user_reported_strength"] == "very low"
    assert haptics["active_local_user_haptic_device_access_verified"]
    assert not haptics["haptic_device_world_writable"]
    assert haptics["feedbackd_initially_missed_device_after_rule_change"]
    assert haptics["feedbackd_after_restart_opened_haptic_device"]
    assert haptics["runtime_in_test_image"] == "20261101-4"
    assert haptics["ram_only_haptic_rule_added_during_test"]
    assert not haptics["whole_runtime_v5_boot_tested"]
    assert haptics["infrared_lirc_device_detected"]
    assert haptics["infrared_feature_mask_hex"] == "0x302"
    assert haptics["infrared_test_operation"] == "GET_FEATURES only"
    for field in ("infrared_signal_transmitted", "infrared_optical_emission_verified",
                  "infrared_remote_control_verified", "calls_placed", "messages_sent"):
        assert haptics[field] is False, field
    assert "userspace_image_sha256" not in haptics and "boot_image_sha256" not in haptics


def input_patch_provenance():
    directory = ROOT / "patches/rebase-4.5"
    origin = json.loads((directory / "linux-apollo-input-origin.json").read_text(encoding="utf-8"))
    patch = (directory / origin["patch_file"]).read_bytes()
    assert hashlib.sha256(patch).hexdigest() == origin["patch_sha256"]
    lines = patch.splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if line.startswith(b"@@ -0,0 +1,760 @@")) + 1
    driver_lines = lines[start:start + 760]
    assert len(driver_lines) == 760 and all(line.startswith(b"+") for line in driver_lines)
    driver = b"".join(line[1:] for line in driver_lines)
    blob_header = b"blob " + str(len(driver)).encode() + b"\0"
    assert hashlib.sha1(blob_header + driver).hexdigest() == origin["aw8697_driver_git_blob"]
    assert b"SPDX-License-Identifier: GPL-2.0-only" in driver
    for author in (b"Armandas Kvietkus", b"Griffin Kroah-Hartman", b"AWINIC Technology"):
        assert author in driver, "Retain the original driver copyright notices"
    assert origin["aw8697_driver_license"] == "GPL-2.0-only"
    assert origin["apollo_board_license"] == "GPL-2.0-only OR BSD-2-Clause"
    assert origin["kernel_driver_is_review_patch_v3_not_upstream_merged_claim"]
    assert not origin["private_android_tree_in_patch"] and not origin["private_unit_calibration_in_patch"]
    assert not origin["ir_inactive_tail_tests_on_hardware"]


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
    input_patch_provenance()
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
