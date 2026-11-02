#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Offline publication checks. No device access, downloads or personal data."""
from pathlib import Path
import ast
import hashlib
import json
import re
import subprocess
import struct
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

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
    for trial in ("r9", "r10", "r11", "r12", "r13"):
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
    sensors = records["r13"]
    assert sensors["runtime"] == "20261101-6" and sensors["whole_runtime_v6_boot_tested"]
    assert sensors["wifi_connection_verified"] and sensors["https_bound_to_wifi_interface_succeeded"]
    assert sensors["https_test_url"] == "https://omarchy.org/" and sensors["https_test_status"] == 200
    for field in ("network_ssid_recorded_in_export", "network_addresses_recorded_in_export",
                  "network_password_recorded_in_export", "before_after_performance_comparison_available",
                  "proximity_available", "button_event_missing_feedback_warning", "calls_placed", "messages_sent"):
        assert sensors[field] is False, field
    assert sensors["missing_allowed_scratch_write_failure_reproduced_with_actual_arm64_rpc_vfs"]
    assert sensors["synthetic_candidate_assertions_passed"] == 26
    assert sensors["scratch_file_generated_in_phone_ram"] and sensors["scratch_file_private_mode"] == "0600"
    assert sensors["missing_scratch_errors_in_collected_boot_log"] == 0
    assert sensors["observation_seconds"] == 20.97 and sensors["missing_scratch_errors_in_observation"] == 0
    assert sensors["feedbackd_opened_haptic_device_without_manual_restart"]
    assert sensors["haptic_udev_rule_present_on_cold_start"] and sensors["active_local_user_rw_haptic_access"]


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


def sensor_patch_provenance():
    directory = ROOT / "patches/rebase-4.5"
    origin = json.loads((directory / "hexagonrpc-scratch-origin.json").read_text(encoding="utf-8"))
    patch = (directory / origin["patch_file"]).read_bytes()
    assert hashlib.sha256(patch).hexdigest() == origin["patch_sha256"]
    assert origin["modified_file"] == "hexagonrpcd/apps_std.c"
    assert origin["file_copyright"] == "2023 The Sensor Shell Contributors"
    assert origin["file_license"] == "GPL-3.0-or-later"
    assert origin["upstream_commit"] == "93f3467dcfe1601bb70547611866a069ae914de5"
    assert origin["board_patch_commit"] == "4c52c8bc8f8bd23a0e31dcd944a15f838777c3e2"
    assert origin["patch_application_to_pinned_source_verified"]
    assert origin["source_copyright_and_license_header_unchanged"]
    assert not origin["device_calibration_in_patch"] and not origin["private_network_data_in_patch"]
    license_text = (ROOT / "LICENSES/GPL-3.0-or-later.txt").read_bytes()
    assert hashlib.sha256(license_text).hexdigest() == origin["copying_sha256"]


def original_boot_review():
    data = json.loads((ROOT / "docs/evidence/2026-11-01-r16.json").read_text(encoding="utf-8"))
    for field in ("independent_reproduction", "device_identifiers_included", "raw_logs_included",
                  "private_camera_images_included", "calibration_or_firmware_included",
                  "capture_text_metadata_present", "capture_is_reference_or_html_mockup",
                  "final_r16_human_display_confirmation_specifically_obtained",
                  "performance_or_boot_time_comparison_available", "sddm_pam_login_tested_on_phone",
                  "local_password_or_pin_configured", "qt_virtualkeyboard_required",
                  "plymouth_touch_luks_unlock_implemented", "theme_selected_for_permanent_phone_boot",
                  "autologin_or_pam_changed", "full_desktop_trial", "private_calibration_staged",
                  "userdata_formatted", "permanent_installation_complete",
                  "full_phone_functionality_verified", "raw_boot_logs_or_identifiers_exported"):
        assert data[field] is False, ("R16", field)
    for field in ("physical_native_plymouth_daemon_verified", "physical_drm_device_opened",
                  "physical_active_vt_verified", "native_kms_framebuffer_captured",
                  "capture_visually_reviewed", "capture_contains_generic_branding_only",
                  "daemon_diagnostic_trace_disabled", "target_arm64_sddm_theme_loaded_in_test_mode",
                  "sddm_test_did_not_authenticate", "temporary_bootstrap_only",
                  "original_boot_readback_verified", "original_dtbo_readback_verified",
                  "android_boot_completed_verified"):
        assert data[field] is True, ("R16", field)
    assert data["ufs_nodes_read_only"] == 122 and data["xkb_errors_in_collected_rescue_log"] == 0
    assert data["observed_daemon_rss_kib_one_sample"] == 18304
    directory = ROOT / "experiments/original-boot-v2"
    manifest = json.loads((directory / "source-manifest.json").read_text(encoding="utf-8"))
    assert data["omarchy_design_commit"] == manifest["upstream_commit"] == "5978d93ae7da0a325b7493501911e3f1266cadd3"
    assert manifest["assets_modified"] is False
    for original, info in manifest["original_sddm_assets"].items():
        if not original.endswith(".png"):
            continue
        content = (directory / "native/sddm/omarchy-apollo-original" / Path(original).name).read_bytes()
        assert hashlib.sha256(content).hexdigest() == info["sha256"]
        assert hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest() == info["git_blob"]
    for name, blob in manifest["original_plymouth_asset_blobs"].items():
        content = (directory / "native/plymouth/omarchy-apollo-original" / name).read_bytes()
        assert hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest() == blob
    for kind in ("sddm", "plymouth"):
        license_text = (directory / "native" / kind / "omarchy-apollo-original/LICENSE-Omarchy").read_bytes()
        assert hashlib.sha256(license_text).hexdigest() == "717ba1949502290f8e47688ae2e323acd06c8ca47aec9f7596b15f678c1af4a2"
    qml = json.loads((directory / "review/qml-review.json").read_text(encoding="utf-8"))
    arm = json.loads((directory / "review/arm64-sddm.json").read_text(encoding="utf-8"))
    parser = json.loads((directory / "review/plymouth-review.json").read_text(encoding="utf-8"))
    browser = json.loads((directory / "review/browser-review.json").read_text(encoding="utf-8"))
    main_hash = hashlib.sha256((directory / "native/sddm/omarchy-apollo-original/Main.qml").read_bytes()).hexdigest()
    keyboard_hash = hashlib.sha256((directory / "native/sddm/omarchy-apollo-original/MobileKeyboard.qml").read_bytes()).hexdigest()
    assert main_hash == qml["native_main_sha256"] == arm["main_qml_sha256"]
    assert keyboard_hash == qml["keyboard_sha256"] == arm["keyboard_qml_sha256"]
    assert len(qml["checks"]) == 17 and all(c["passed"] for c in qml["checks"]) and not qml["messages"]
    assert len(browser["checks"]) == 6 and all(c["passed"] for c in browser["checks"])
    assert not qml["pam_authentication_tested"] and not arm["pam_authentication_tested"]
    assert arm["actual_arm64_sddm_test_mode_load_passed"] and arm["package_integrity_files"] == 35
    assert not arm["system_theme_selection_or_authentication_changed"]
    assert parser["actual_upstream_parser_passed"] and parser["upstream_parser_version"] == "26.134.222"
    assert not parser["drm_render_tested"] and not parser["phone_boot_tested"]
    assert hashlib.sha256((directory / "native/plymouth/omarchy-apollo-original/omarchy-apollo-original.script").read_bytes()).hexdigest() == parser["script_sha256"]
    assert (directory / "previews/login-initial-432.png").read_bytes() == (directory / "previews/upstream-reference-432.png").read_bytes()
    capture = (ROOT / "media/apollo-boot-r16.png").read_bytes()
    assert len(capture) == 15296 and hashlib.sha256(capture).hexdigest() == data["capture_sha256"]
    assert capture[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", capture[16:24]) == (data["capture_width"], data["capture_height"]) == (1080, 2400)
    cursor, chunks = 8, []
    while cursor < len(capture):
        length = struct.unpack(">I", capture[cursor:cursor + 4])[0]
        chunks.append(capture[cursor + 4:cursor + 8])
        cursor += 12 + length
    assert cursor == len(capture) and chunks[0] == b"IHDR" and chunks[-1] == b"IEND"
    assert set(chunks) <= {b"IHDR", b"sRGB", b"IDAT", b"IEND"}, "No personal/text metadata in R16 capture"
    html = (directory / "preview.html").read_text(encoding="utf-8")
    class PreviewParser(HTMLParser):
        def handle_starttag(self, tag, attrs):
            assert tag not in {"input", "textarea", "form"}, "Offline preview must not collect credentials"
            for key, value in attrs:
                if key in {"src", "href"}:
                    assert value and (value.startswith("data:image/png;base64,") or value.startswith("#"))
    PreviewParser().feed(html)
    assert "connect-src 'none'" in html and "form-action 'none'" in html
    assert not re.search(r"fetch\s*\(|XMLHttpRequest|WebSocket|localStorage|document\.cookie", html)
    helper = (directory / "tools/capture_splash.c").read_text(encoding="utf-8")
    assert "SPDX-License-Identifier: MIT" in helper and "/etc/apollo/ram-splash-probe" in helper and "xiaomi,apollo" in helper
    assert "PROT_READ" in helper and "PROT_WRITE" not in helper
    assert not re.search(r"\b(?:drmSetMaster|drmModeSetCrtc|drmModeAtomicCommit)\s*\(", helper)
    ast.parse((directory / "stage.py").read_text(encoding="utf-8"))


def sim_trial_boundaries():
    data = json.loads((ROOT / "docs/evidence/2026-11-01-r17.json").read_text(encoding="utf-8"))
    assert data["trial"] == "R17" and data["evidence_type"] == "sanitized supervised-device result summary"
    for field in ("systemd_pid1_verified", "sim_available_for_tests", "sim_object_detected", "sim_pin_required",
                  "signed_local_pin_dialog_installed_and_launched_in_ram",
                  "manual_fastboot_buttons_required_for_recovery",
                  "limited_fastboot_rejected_download_before_partition_write",
                  "original_dtbo_restored_in_full_bootloader", "android_boot_completed_verified",
                  "original_boot_readback_verified", "original_dtbo_readback_verified"):
        assert data[field] is True, ("R17", field)
    for field in ("independent_reproduction", "device_identifiers_included", "raw_logs_included",
                  "private_camera_images_included", "calibration_or_firmware_included",
                  "sim_unlock_completed_verified", "ordinary_network_registration_verified",
                  "physical_to_logical_sim_slot_mapping_verified", "pin_dialog_user_completion_confirmed",
                  "calls_tested", "sms_tested", "cellular_data_tested", "calls_or_messages_sent_by_agent",
                  "pin_received_by_agent", "subscriber_identifiers_exported",
                  "sim_pin_protection_disabled_or_changed", "calibration_partitions_written",
                  "automatic_android_return_reliable", "userdata_formatted", "permanent_installation_complete",
                  "sddm_pam_login_tested_on_phone", "full_phone_functionality_verified"):
        assert data[field] is False, ("R17", field)


def sim_registration_and_ui_review():
    data = json.loads((ROOT / "docs/evidence/2026-11-01-r18.json").read_text(encoding="utf-8"))
    assert data["trial"] == "R18" and data["registration_state"] == "home"
    for field in ("user_entered_sim_pin_on_handset", "sim_access_pin_unlocked_verified",
                  "ordinary_network_registration_verified", "lte_access_technology_reported",
                  "nr5g_access_technology_reported", "packet_service_attached_reported",
                  "pin2_reported_separately_from_sim_access_pin", "voice_interface_present",
                  "messaging_interface_present", "root_pin_ui_only_in_supervised_ram_session",
                  "this_trial_returned_automatically_without_requesting_buttons",
                  "original_dtbo_restored", "android_boot_completed_verified",
                  "original_boot_readback_verified", "original_dtbo_readback_verified"):
        assert data[field] is True, ("R18", field)
    for field in ("independent_reproduction", "device_identifiers_included", "raw_logs_included",
                  "private_camera_images_included", "calibration_or_firmware_included",
                  "pin_received_or_logged_by_agent", "actual_5g_throughput_measured",
                  "cellular_ip_internet_tested", "physical_to_logical_sim_slot_mapping_verified",
                  "pin2_or_puk_entered", "pin2_message_fix_phone_tested",
                  "user_call_attempt_result_confirmed", "call_audio_verified", "sms_tested",
                  "calls_or_messages_sent_by_agent", "subscriber_ids_numbers_or_operator_exported",
                  "modem_general_authorization_policy_changed", "local_credentials_or_pam_changed",
                  "screen_or_pin_captured", "private_calibration_exported",
                  "manual_fastboot_buttons_required_for_recovery", "automatic_return_reliability_proven",
                  "userdata_formatted", "permanent_installation_complete",
                  "sddm_pam_login_tested_on_phone", "full_phone_functionality_verified"):
        assert data[field] is False, ("R18", field)
    assert data["phone_ui_package_tested"] == "apollo-sim-unlock 0.1.2-1"
    assert data["pin2_message_fix_candidate"] == "apollo-sim-unlock 0.1.3-1"
    assert data["max_call_objects_in_bounded_observations"] == 0
    directory = ROOT / "experiments/sim-unlock"
    candidate = json.loads((directory / "candidate.json").read_text(encoding="utf-8"))
    review = json.loads((directory / "arm64-synthetic-review.json").read_text(encoding="utf-8"))
    source = (directory / "apollo-sim-unlock.py").read_bytes()
    assert hashlib.sha256(source).hexdigest() == candidate["source_sha256"]
    assert candidate["package"] == data["pin2_message_fix_candidate"] and not candidate["phone_tested"]
    assert candidate["radio_pin_attempts_in_synthetic_test"] == 0
    assert not candidate["logs_pin_or_reads_subscriber_ids"]
    assert review["real_arm64_gtk_gio_loaded"] and review["synthetic_modem_only"]
    assert review["real_radio_pin_attempts"] == 0 and not review["subscriber_properties_queried"]
    assert review["pin2_puk2_not_mistaken_for_access_pin"]
    license_text = (directory / "LICENSE").read_text(encoding="utf-8")
    assert "MIT License" in license_text and "Copyright (c) 2026 Apollo contributors" in license_text
    tree = ast.parse(source.decode("utf-8"))
    app = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "SimUnlock")
    properties = {
        node.args[2].value for node in ast.walk(app)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name) and node.func.value.id == "self"
        and node.func.attr == "get" and len(node.args) == 3 and isinstance(node.args[2], ast.Constant)
    }
    assert properties == {"Sim", "UnlockRequired", "UnlockRetries"}, "Do not query subscriber/operator properties"
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                   and node.func.id in {"print", "open", "eval", "exec"} for node in ast.walk(tree))
    # Exercise only the classification method with fake property reads.
    # GTK is not imported and no bus or radio object exists in this test.
    method = next(node for node in app.body if isinstance(node, ast.FunctionDef) and node.name == "refresh")
    namespace = {"MODEM": "org.freedesktop.ModemManager1.Modem",
                 "__builtins__": {"dict": dict, "isinstance": isinstance, "str": str}}
    exec(compile(ast.Module(body=[method], type_ignores=[]), "<SIM refresh classification>", "exec"), namespace)
    class Control:
        def set_sensitive(self, value):
            self.sensitive = value
        def set_text(self, value):
            self.text = value
    class FakeModem:
        def __init__(self, lock, retries, blocked):
            self.values = {"UnlockRequired": lock, "UnlockRetries": {2: retries}}
            self.modem = "/synthetic"
            self.send_blocked = blocked
            self.button, self.entry, self.keypad, self.status = (Control() for _ in range(4))
        def get(self, path, interface, prop):
            assert path == self.modem and interface == namespace["MODEM"]
            return self.values[prop]
    for lock, retries, blocked, ready in (
        (1, 3, False, False), (2, 3, False, True), (3, 3, False, False),
        (4, 3, False, False), (5, 3, False, False), (2, 0, False, False),
        (2, 3, True, False), (0, 3, False, False),
    ):
        fake = FakeModem(lock, retries, blocked)
        namespace["refresh"](fake)
        assert fake.ready is ready and fake.button.sensitive is ready, (lock, retries, blocked)


def outgoing_call_trial_boundaries():
    data = json.loads((ROOT / "docs/evidence/2026-11-01-r19.json").read_text(encoding="utf-8"))
    assert data["trial"] == "R19" and data["runtime"] == "20261101-6"
    for field in ("sim_ui_normal_gpg_alpm_integrity_verified", "native_sim_ui_window_process_verified",
                  "modem_registered", "lte_access_technology_reported", "nr5g_access_technology_reported",
                  "dialer_opened_without_number_or_dial_uri", "outgoing_call_manually_dialed_by_user",
                  "user_confirmed_connection_and_audible_voicemail", "outgoing_call_active_verified",
                  "downlink_audio_heard_by_user", "this_trial_returned_automatically_without_requesting_buttons",
                  "android_boot_completed_verified", "original_boot_readback_verified",
                  "original_dtbo_readback_verified"):
        assert data[field] is True, ("R19", field)
    for field in ("independent_reproduction", "device_identifiers_included", "raw_logs_included",
                  "private_camera_images_included", "calibration_or_firmware_included",
                  "dismissed_notice_origin_confirmed", "pin2_vs_sim2_message_identified",
                  "pin2_ui_fix_human_acceptance_verified", "sim_access_pin_submission_retested_with_0_1_3",
                  "sim_access_pin_required", "current_sim_proxy_matches_slot_array",
                  "physical_sim_card_count_verified", "physical_to_logical_sim_slot_mapping_verified",
                  "call_object_path_values_exported", "call_number_or_name_read",
                  "subscriber_ids_numbers_operator_or_apn_exported", "screen_or_audio_files_exported",
                  "pin_received_or_stored_by_agent", "call_placed_by_agent", "sms_sent_by_agent",
                  "microphone_uplink_verified", "incoming_calls_verified", "sms_verified",
                  "cellular_ip_internet_verified", "actual_5g_throughput_measured", "call_aec_verified",
                  "volte_call_path_verified", "manual_fastboot_buttons_required_for_recovery",
                  "automatic_return_reliability_proven", "userdata_formatted", "permanent_installation_complete",
                  "sddm_pam_login_tested_on_phone", "full_phone_functionality_verified"):
        assert data[field] is False, ("R19", field)
    assert data["sim_ui_package_loaded"] == "apollo-sim-unlock 0.1.3-1"
    assert data["unlock_required_enum"] == 3 and data["unlock_required_label"] == "SIM_PIN2"
    assert [data[key] for key in ("reported_sim_slot_entries", "occupied_slot_entries", "empty_slot_entries", "active_sim_count_reported")] == [2, 1, 1, 1]
    assert data["dialer"] == "GNOME Calls 51.1" and data["call_observation_seconds"] == 65
    assert data["max_call_objects_observed"] == 1 and data["call_state_query_errors"] == 0
    assert data["call_state_names_observed"] == ["DIALING", "ACTIVE"] and data["call_state_codes_observed"] == [1, 4]
    assert data["call_direction_name"] == "OUTGOING" and data["call_direction_code"] == 2
    assert data["queried_call_properties"] == ["State", "Direction", "StateReason"]
    load = json.loads((ROOT / "experiments/sim-unlock/phone-load-r19.json").read_text(encoding="utf-8"))
    assert load["trial"] == "R19" and load["historical_candidate_snapshot_trial"] == "R18"
    assert load["native_phone_window_process_verified"] and load["normal_gpg_alpm_integrity_verified"]
    assert not load["pin2_ui_fix_human_acceptance_verified"]
    assert not load["physical_to_logical_sim_slot_mapping_verified"] and not load["full_phone_functionality_verified"]


def internal_root_and_owner_setup_review():
    data = json.loads((ROOT / "docs/evidence/2026-11-02-r20.json").read_text(encoding="utf-8"))
    assert data["trial"] == "R20" and data["review_date"] == "2026-11-02"
    assert data["evidence_type"] == "sanitized supervised-device result summary"
    for field in ("internal_ext4_root_boot_verified", "systemd_and_native_hardware_target_verified",
                  "native_desktop_human_confirmed", "initial_16_gib_image_verified_complete_before_write",
                  "full_post_transfer_readback_match_verified_before_first_rw_boot",
                  "root_filesystem_expanded_to_its_partition", "protected_firmware_and_calibration_partitions_verified",
                  "own_private_calibration_provisioned", "android_userdata_reformatted_for_native_root",
                  "owner_layout_no_duplicate_osk_and_second_field_human_accepted", "local_owner_credential_saved",
                  "owner_ready_marker_verified_as_boolean", "passwd_status_p_verified_as_boolean",
                  "r5_profile_installed_via_normal_gpg_alpm",
                  "r5_autoclose_only_after_success_arm64_synthetic_pass_reported", "kernel_still_started_from_ram",
                  "later_reviewed_internal_root_cellular_ipv4_https_test", "wifi_off_during_cellular_https_test",
                  "https_request_bound_to_cellular_interface"):
        assert data[field] is True, ("R20", field)
    for field in ("independent_reproduction", "device_identifiers_included", "raw_logs_included",
                  "unit_image_or_credential_hashes_included", "private_calibration_or_firmware_included",
                  "credential_value_or_password_hash_read_by_agent", "r5_autoclose_human_acceptance_verified",
                  "next_sddm_login_with_new_credential_verified", "administrative_polkit_auth_with_new_credential_verified",
                  "native_boot_committed_to_boot_partition", "standalone_persistent_boot_verified",
                  "next_boot_visual_validation_complete", "android_super_cleanup_complete",
                  "permanent_installation_complete", "all_hardware_functionality_verified",
                  "regular_mi10t_variant_validated", "cellular_ipv6_verified",
                  "generic_sim_apn_autoprovisioning_validated", "cellular_throughput_or_5g_speed_measured",
                  "subscriber_operator_apn_ip_or_network_identity_exported", "browser_screenshot_exported"):
        assert data[field] is False, ("R20", field)
    assert data["native_profile_revision"] == "20261101-5"
    assert data["r5_autoclose_delay_ms"] == 600 and data["cellular_ipv4_https_status"] == 204
    directory = ROOT / "experiments/owner-setup"
    review = json.loads((directory / "review.json").read_text(encoding="utf-8"))
    assert review["source_revision"] == "native profile 20261101-5 (r5)"
    assert review["synthetic_actual_arm64_gtk_pass_reported_by_project_controller"]
    assert not review["synthetic_gtk_rerun_by_publication_agent"]
    assert review["synthetic_test_overrides_real_credential_sink"]
    assert review["real_pam_operations_in_synthetic_test"] == review["radio_or_subscriber_queries_in_synthetic_test"] == 0
    assert not review["r5_human_autoclose_acceptance_verified"]
    for name, checksum in review["source_sha256"].items():
        assert name in {"owner-setup.py", "omarchy.css", "test_owner_setup_synthetic.py"}
        assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == checksum, name
    assert set(review["source_sha256"]) == {"owner-setup.py", "omarchy.css", "test_owner_setup_synthetic.py"}
    assert (directory / "assets/logo.png").read_bytes() == (ROOT / "experiments/original-boot-v2/native/sddm/omarchy-apollo-original/logo.png").read_bytes()
    assert "Copyright (c) David Heinemeier Hansson" in (directory / "assets/LICENSE-Omarchy").read_text(encoding="utf-8")
    assert (directory / "LICENSE").read_bytes() == (ROOT / "LICENSE").read_bytes()
    tree = ast.parse((directory / "owner-setup.py").read_text(encoding="utf-8"))
    harness = ast.parse((directory / "test_owner_setup_synthetic.py").read_text(encoding="utf-8"))
    app = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "OwnerSetup")
    synthetic = next(node for node in harness.body if isinstance(node, ast.ClassDef) and node.name == "SyntheticOwner")
    assert any(isinstance(node, ast.FunctionDef) and node.name == "set_credential" for node in synthetic.body)
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                   and node.func.id in {"OwnerSetup", "eval", "exec"} for node in ast.walk(harness))
    # Exercise completion callbacks only: no GTK import, real app execution,
    # account command, privileged sink, D-Bus connection or radio exists here.
    methods = [node for node in app.body if isinstance(node, ast.FunctionDef)
               and node.name in {"finished", "close_after_success"}]
    assert len(methods) == 2
    class FakeGLib:
        SOURCE_REMOVE = False
        def __init__(self):
            self.timers = []
        def timeout_add(self, delay, callback):
            self.timers.append((delay, callback))
    timer = FakeGLib()
    namespace = {"GLib": timer, "__builtins__": {}}
    exec(compile(ast.Module(body=methods, type_ignores=[]), "<owner completion callbacks>", "exec"), namespace)
    class Control:
        def set_sensitive(self, value):
            self.sensitive = value
        def set_visible(self, value):
            self.visible = value
        def set_text(self, value):
            self.text = value
        def close(self):
            self.closed = True
    class FakeApp:
        def __init__(self):
            self.busy, self.completed, self.quit_called = True, False, False
            self.save, self.close, self.keypad, self.status, self.win = (Control() for _ in range(5))
            self.entries = [Control(), Control()]
            self.win.closed = False
        def close_after_success(self):
            return namespace["close_after_success"](self)
        def quit(self):
            self.quit_called = True
    failure = FakeApp()
    assert namespace["finished"](failure, False) is timer.SOURCE_REMOVE
    assert not failure.busy and not failure.completed and not timer.timers
    assert failure.save.sensitive and failure.keypad.sensitive and all(e.sensitive for e in failure.entries)
    assert namespace["close_after_success"](failure) is timer.SOURCE_REMOVE
    assert not failure.win.closed and not failure.quit_called
    success = FakeApp()
    assert namespace["finished"](success, True) is timer.SOURCE_REMOVE
    assert success.completed and not success.busy and len(timer.timers) == 1
    assert not success.save.visible and not success.close.visible
    assert not success.win.closed and not success.quit_called
    delay, callback = timer.timers[0]
    assert delay == 600 and callback() is timer.SOURCE_REMOVE
    assert success.win.closed and success.quit_called


def installed_native_boot_boundaries():
    directory = ROOT / "docs/evidence"
    login = json.loads((directory / "2026-11-02-login-v6.json").read_text(encoding="utf-8"))
    assert login["actual_sddm_pam_login_verified"] and login["user_entered_new_local_credential_on_handset"]
    assert login["sddm_autologin_user_empty_verified"] and login["ordinary_user_wayland_socket_verified"]
    assert not login["administrative_polkit_auth_with_new_credential_verified"]
    assert not login["boot_visual_revision_6_human_accepted"]
    assert not login["standalone_persistent_boot_verified"], "Earlier snapshot retains its scope"
    assert not login["credential_value_or_account_hash_read_or_exported"]
    data = json.loads((directory / "2026-11-02-native-boot-v7.json").read_text(encoding="utf-8"))
    assert data["review_date"] == "2026-11-02" and data["boot_visual_revision"] == 7
    assert data["evidence_type"] == "sanitized supervised-device result summary"
    assert data["supersedes_installation_state_in"] == ["2026-11-02-r20.json", "2026-11-02-login-v6.json"]
    for field in ("native_os_installation_completed_on_development_unit", "native_boot_written_to_boot_partition",
                  "normal_boot_without_fastboot_boot_verified", "repeated_normal_native_boot_verified",
                  "third_reported_normal_boot_after_android_cleanup_verified",
                  "systemd_internal_ext4_root_verified_after_normal_boot", "firmware_calibration_guard_verified",
                  "boot_and_recovery_expected_image_prefix_readback_verified",
                  "android_userdata_reformatted_for_native_root", "android_super_cleared",
                  "android_metadata_cleared", "android_cache_cleared",
                  "user_entered_local_credential_after_normal_boot", "actual_sddm_pam_login_after_normal_boot_verified",
                  "sddm_autologin_user_empty_verified", "original_sddm_theme_selected_verified",
                  "ordinary_user_wayland_socket_verified", "normal_boot_desktop_human_confirmed_without_shell_restart",
                  "black_desktop_after_live_gesture_upgrade_observed",
                  "live_upgrade_black_desktop_resolved_by_official_quickshell_restart",
                  "gesture_home_human_verified", "gesture_hold_recents_human_verified",
                  "boot_graphics_proof_marker_retained_and_checked", "fresh_profile_creation_after_normal_boot_verified",
                  "cellular_auto_profile_active_route_verified", "https_request_bound_to_cellular_with_wifi_off",
                  "earlier_modem_restart_while_two_project_profiles_eligible_observed",
                  "older_temporary_profile_autoconnect_disabled", "following_normal_boot_cellular_connection_verified",
                  "latest_post_cleanup_cold_boot_sim_access_pin_required", "wifi_function_after_cleanup_reported",
                  "standalone_persistent_boot_verified", "permanent_installation_complete"):
        assert data[field] is True, ("native boot7", field)
    for field in ("independent_reproduction", "entire_boot_recovery_partition_hashes_claimed",
                  "administrative_polkit_auth_with_new_credential_verified", "persistent_desktop_startup_failure_established",
                  "gesture_finetuning_complete", "unwanted_keyboard_popup_fully_resolved",
                  "boot_visual_logo_human_confirmed", "generic_any_sim_or_operator_autoprovisioning_validated",
                  "latest_cold_boot_sim_pin_unlock_confirmed", "cellular_data_retested_after_latest_cold_pin_boot",
                  "cellular_ipv6_verified", "cellular_throughput_or_5g_speed_measured",
                  "complete_daily_driver_or_all_hardware_verified", "public_end_to_end_installer_validated",
                  "regular_mi10t_variant_validated", "device_identifiers_included", "raw_logs_included",
                  "credential_value_or_account_hash_read_or_exported", "operator_apn_ip_or_network_identity_exported",
                  "phone_screenshots_exported", "private_calibration_firmware_or_unit_images_included"):
        assert data[field] is False, ("native boot7", field)
    assert data["automatic_cellular_profile_candidate_revision"] == "r2"
    assert data["operator_count_tested"] == 1 and data["cellular_ipv4_https_status"] == 204
    assert data["latest_installed_sim_ui_package"] == "apollo-sim-unlock 0.2.1-1"
    assert data["latest_sim_ui_compact_without_large_lock"]
    assert data["latest_sim_ui_uses_gtk_button_password_entry_buffer_and_own_keypad"]
    assert not data["latest_sim_ui_has_gtk_editable_or_osk_surface"]
    assert data["sim_state_core_byte_identical_to_controller_reviewed_baseline"]
    assert data["classification_preflight_send_close_methods_ast_identical_count"] == 13
    assert data["classification_synthetic_checks_passed"] == 18
    assert data["arm64_gtk_synthetic_checks_passed"] == 17
    assert not data["new_sim_ui_source_included"]
    assert not data["new_sim_ui_human_pin_entry_after_cold_boot_verified"]
    assert data["latest_cold_boot_primary_access_pin_enum"] == 2
    assert not data["latest_cold_boot_user_wayland_session_verified"]
    assert data["latest_native_profile_package"] == "apollo-native-profile 20261101-6"
    assert data["sim_launcher_wait_180_seconds_timeout_before_login_observed"]
    assert data["sim_launcher_wait_fix_installed_via_normal_gpg_alpm"]
    assert data["sim_launcher_waits_for_user_session_then_checks_unlock"]
    assert data["sim_launcher_wait_offline_checks_passed"] == 7
    assert data["owner_launcher_wait_unchanged_seconds"] == 180
    assert data["sim_pin_service_resumed_after_failed_state_only"]
    assert not data["live_sim_form_replaced_for_launcher_fix"]
    assert not data["human_pin_entry_after_launcher_wait_fix_verified"]
    assert not data["new_launcher_source_included"]


def cold_boot_sim_and_desktop_recurrence_boundaries():
    directory = ROOT / "docs/evidence"
    name = "2026-11-02-cold-boot-sim-desktop.json"
    previous = json.loads((directory / "2026-11-02-native-boot-v7.json").read_text(encoding="utf-8"))
    assert previous["superseded_desktop_and_sim_state_by"] == name
    data = json.loads((directory / name).read_text(encoding="utf-8"))
    assert data["evidence_type"] == "sanitized supervised-device result summary"
    assert data["supersedes_desktop_and_sim_state_in"] == "2026-11-02-native-boot-v7.json"
    for field in ("native_boot_and_internal_root_installation_remain_verified", "actual_pam_login_after_cold_boot_verified",
                  "human_entered_primary_sim_pin_only_on_handset", "human_sim_pin_entry_with_0_2_1_after_cold_boot_verified",
                  "primary_sim_access_pin_no_longer_required", "fresh_auto_profile_active",
                  "https_request_bound_to_cellular_interface", "wifi_connected_during_bound_cellular_test",
                  "human_confirmed_network_coverage", "recurring_black_desktop_center_after_cold_boot_login_observed",
                  "bar_and_search_pill_visible_while_center_black", "home_model_loaded_during_failure",
                  "normal_gpg_alpm_qkk_installation_verified", "official_quickshell_restart_recovery_verified",
                  "controller_review_confirmed_wallpaper_clock_and_8_icons_recovered",
                  "human_basic_home_recents_and_keyboard_close_acceptance_verified"):
        assert data[field] is True, ("cold-boot follow-up", field)
    for field in ("independent_reproduction", "cellular_is_default_route_while_wifi_preferred",
                  "other_sim_or_operator_coverage_verified", "cellular_ipv6_verified", "throughput_or_5g_speed_measured",
                  "startup_rendering_root_cause_identified", "definitive_startup_fix_verified",
                  "hyprland_restarted_for_this_recovery", "active_pin_forms_present_during_restart",
                  "private_recovery_capture_read_by_publication_agent", "private_recovery_capture_exported",
                  "full_gesture_keyboard_finetuning_complete", "last_app_close_in_recents_returns_home_verified",
                  "administrative_polkit_auth_verified", "full_phone_daily_driver_acceptance_verified",
                  "new_ui_launcher_or_shell_source_payload_included", "pin_value_or_account_hash_read_or_exported",
                  "device_subscriber_operator_apn_ip_or_network_identity_exported",
                  "raw_logs_or_per_unit_geometry_exported", "phone_capture_exported",
                  "private_calibration_firmware_or_unit_images_included"):
        assert data[field] is False, ("cold-boot follow-up", field)
    assert data["installed_sim_ui_package"] == "apollo-sim-unlock 0.2.1-1"
    assert data["remaining_unlock_enum"] == 3 and data["remaining_unlock_label"] == "SIM_PIN2"
    assert data["modem_state_enum"] == 11 and data["modem_state_label"] == "connected"
    assert data["registration_state"] == "home" and data["cellular_ipv4_https_status"] == 204
    assert data["quickshell_processes_observed_during_failure"] == 1
    assert data["normal_application_windows_observed_during_failure"] == 0
    assert data["installed_mobile_shell_revision_label"] == ".8"
    assert data["installed_gesture_keyboard_revision_label"] == "r2"
    assert data["controller_reported_offline_checks"] == {"integrated_touch": 14, "qt": 14, "helper": 9, "plugin_compile": 5}


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
    sensor_patch_provenance()
    original_boot_review()
    sim_trial_boundaries()
    sim_registration_and_ui_review()
    outgoing_call_trial_boundaries()
    internal_root_and_owner_setup_review()
    installed_native_boot_boundaries()
    cold_boot_sim_and_desktop_recurrence_boundaries()
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
