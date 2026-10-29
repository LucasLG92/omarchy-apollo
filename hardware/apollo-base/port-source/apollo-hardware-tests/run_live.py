from pathlib import Path
import argparse
import datetime
import hashlib
import json
import re
import socket
import shlex
import subprocess
import sys
import threading
import time

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / 'work' / 'python-deps'))
import serial
from serial.tools import list_ports
TOOLS = Path(__import__('os').environ['APOLLO_PLATFORM_TOOLS'])
DEVICE = __import__('os').environ['APOLLO_SERIAL']
parser = argparse.ArgumentParser()
parser.add_argument('--from-bootloader', action='store_true')
parser.add_argument('--image-set-directory', type=Path)
parser.add_argument('--hardware-audit', action='store_true')
parser.add_argument('--modem-audit', action='store_true')
parser.add_argument('--video-audit', action='store_true')
parser.add_argument('--video-extended-audit-only', action='store_true')
parser.add_argument('--video-player-audit-only', action='store_true')
parser.add_argument('--quiet-regression-audit-only', action='store_true')
parser.add_argument('--clock-player-audit-only', action='store_true')
parser.add_argument('--clock-regression-audit-only', action='store_true')
parser.add_argument('--backlight-regression-audit-only', action='store_true')
parser.add_argument('--apr-regression-audit-only', action='store_true')
parser.add_argument('--focus-supply-audit-only', action='store_true')
parser.add_argument('--focus-stream-audit-only', action='store_true')
parser.add_argument('--focus-matrix-audit-only', action='store_true')
parser.add_argument('--hold-native-diagnostics', action='store_true')
parser.add_argument('--focus-clock-regression-audit-only', action='store_true')
parser.add_argument('--focus-trace-startup-audit-only', action='store_true')
parser.add_argument('--suspend-audit', action='store_true')
parser.add_argument('--camera-audit-only', action='store_true')
parser.add_argument('--camera-stress-audit', action='store_true')
parser.add_argument('--gps-audit', action='store_true')
parser.add_argument('--fingerprint-audit', action='store_true')
parser.add_argument('--wifi-audit', action='store_true')
parser.add_argument('--wifi-audit-only', action='store_true')
parser.add_argument('--network-location-audit-only', action='store_true')
parser.add_argument('--location-startup-audit-only', action='store_true')
parser.add_argument('--no-host-clock', action='store_true')
parser.add_argument('--audio-audit-only', action='store_true')
parser.add_argument('--iris-diagnostic-module', type=Path)
args = parser.parse_args()
if args.focus_trace_startup_audit_only:
    assert args.hardware_audit
    args.no_host_clock=True
if args.hold_native_diagnostics:
    args.video_player_audit_only=True
    args.no_host_clock=True
if args.focus_clock_regression_audit_only:
    args.video_player_audit_only=True
    args.camera_stress_audit=True
    args.no_host_clock=True
if args.clock_regression_audit_only:
    args.quiet_regression_audit_only=True
if args.quiet_regression_audit_only:
    args.video_player_audit_only=True
    args.camera_stress_audit=True
    args.location_startup_audit_only=True
    args.no_host_clock=True
if args.clock_player_audit_only:
    args.video_player_audit_only=True
    args.no_host_clock=True
if args.backlight_regression_audit_only:
    args.video_player_audit_only=True
    args.no_host_clock=True
if args.apr_regression_audit_only:
    args.video_player_audit_only=True
    args.no_host_clock=True
if args.focus_matrix_audit_only:
    args.focus_supply_audit_only=True
if args.focus_stream_audit_only:
    args.focus_supply_audit_only=True
if args.focus_supply_audit_only:
    args.video_player_audit_only=True
    args.no_host_clock=True
if args.audio_audit_only and (BASE / 'work/quiet-mode.requested').exists():
    raise SystemExit('Audio playback checks disabled by the user request for silent work')
if args.gps_audit:
    args.modem_audit = True
if args.location_startup_audit_only:
    args.network_location_audit_only = True
if args.network_location_audit_only:
    args.modem_audit = True
    args.wifi_audit = True
OUT = BASE / 'outputs/arch-apollo'
BACKUP = OUT / 'recovery-backup'
EXPERIMENTAL = OUT / 'experimental'
manifest = json.loads((BACKUP / 'manifest.json').read_text())
dtbo = BACKUP / 'dtbo.img'
assert hashlib.sha256(dtbo.read_bytes()).hexdigest() == manifest['partitions']['dtbo']['sha256']
image_directory=(args.image_set_directory or EXPERIMENTAL).resolve()
image = image_directory / 'boot-live.img'
rootfs = image_directory / 'arch-apollo-live.sqfs'
if (EXPERIMENTAL / '.building').exists() or (image_directory / '.building').exists():
    raise SystemExit('Image build is still in progress; nothing changed')
live_set = json.loads((image_directory / 'live-set.json').read_text())
for file in (image, rootfs):
    with file.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if file.stat().st_size != live_set[file.name]['size'] or digest != live_set[file.name]['sha256']:
        raise SystemExit('Incomplete or mismatched image set; nothing changed')
assert image.stat().st_size < manifest['partitions']['boot']['size']

def command(tool, *args, required=True, timeout=60):
    process = subprocess.run([str(TOOLS / (tool + '.exe')), '-s', DEVICE, *args],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    output = process.stdout.decode(errors='replace')
    print(tool, ' '.join(args), '\n' + output, flush=True)
    if required and process.returncode: raise RuntimeError(output)
    return output

def present():
    result = subprocess.run([str(TOOLS / 'fastboot.exe'), 'devices'], capture_output=True, timeout=8)
    return DEVICE in result.stdout.decode(errors='replace')

def wait_bootloader(seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if present(): return True
        time.sleep(2)
    return False

upload_done = threading.Event()
stop_upload = threading.Event()
upload_failure = []
audit_done = threading.Event()
audit_started = False
audit_result = {}
tag = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')

def hardware_audit():
    report = EXPERIMENTAL / ('hardware-' + tag)
    report.mkdir(exist_ok=True)
    ssh = ['ssh', '-i', str(BASE / 'work/ssh/apollo_live'),
           '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5',
           '-o', 'StrictHostKeyChecking=accept-new',
           '-o', 'UserKnownHostsFile=' + str(BASE / ('work/ssh/hosts-' + tag)),
           'apollo@172.16.42.1']
    monitors = []
    logs = []
    try:
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            ready = subprocess.run([*ssh, 'true'], capture_output=True)
            if ready.returncode == 0: break
            time.sleep(3)
        else:
            raise RuntimeError('USB SSH did not become ready: ' + ready.stderr.decode(errors='replace'))
        # Update diagnostics in the RAM overlay so tests do not require
        # rebuilding/transferring the entire OS after every script change.
        subprocess.run([*ssh, 'cat > /tmp/apollo-audit-update'],
                       input=(BASE / 'work/apollo-hardware-audit').read_bytes(),
                       capture_output=True, timeout=15, check=True)
        test_password = Path(__import__('os').environ['APOLLO_TEST_PASSWORD_FILE']).read_bytes().strip() + b'\n'
        subprocess.run([*ssh, 'sudo -S -p "" install -m755 /tmp/apollo-audit-update /usr/local/sbin/apollo-hardware-audit'],
                       input=test_password, capture_output=True, timeout=15, check=True)
        if (BASE / 'work/quiet-mode.requested').exists():
            check='runuser -u apollo -- env XDG_RUNTIME_DIR=/run/user/1001 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1001/bus systemctl --user mask --runtime --now pipewire.service pipewire.socket pipewire-pulse.service pipewire-pulse.socket wireplumber.service'
            subprocess.run([*ssh, 'sudo -S -p "" '+check],input=test_password,capture_output=True,timeout=15,check=True)
        if args.wifi_audit or args.wifi_audit_only:
            from private_wifi import load, keyfile
            profile=keyfile(load(BASE / 'work/current-wifi.dpapi'))
            if args.clock_regression_audit_only:
                profile=profile.replace(b'autoconnect=true\n',b'autoconnect=false\n',1)
            subprocess.run([*ssh,'umask 077; cat > /tmp/apollo-wifi-private.nmconnection'],input=profile,
                           capture_output=True,timeout=15,check=True)
            subprocess.run([*ssh,'sudo -S -p "" install -Dm600 /tmp/apollo-wifi-private.nmconnection /run/NetworkManager/system-connections/apollo-wifi.nmconnection'],
                           input=test_password,capture_output=True,timeout=15,check=True)
            subprocess.run([*ssh,'rm -f /tmp/apollo-wifi-private.nmconnection'],capture_output=True,timeout=10,check=True)
            subprocess.run([*ssh,'cat > /tmp/apollo-network-audit'],input=(BASE/'work/apollo-network-audit').read_bytes(),
                           capture_output=True,timeout=15,check=True)
            subprocess.run([*ssh,'sudo -S -p "" install -m755 /tmp/apollo-network-audit /usr/local/sbin/apollo-network-audit'],
                           input=test_password,capture_output=True,timeout=15,check=True)
        if args.video_extended_audit_only:
            subprocess.run([*ssh,'cat > /tmp/apollo-video-extended-audit'],
                           input=(BASE/'work/apollo-video-extended-audit').read_bytes(),
                           capture_output=True,timeout=15,check=True)
            subprocess.run([*ssh,'sudo -S -p "" install -m755 /tmp/apollo-video-extended-audit /usr/local/sbin/apollo-video-extended-audit'],
                           input=test_password,capture_output=True,timeout=15,check=True)
            fixture=BASE/'work/video-vectors-v1'
            subprocess.run([*ssh,'mkdir -p /tmp/apollo-video-vectors-v1'],capture_output=True,timeout=10,check=True)
            for file in sorted(fixture.iterdir()):
                assert file.is_file() and re.fullmatch(r'[a-z0-9.-]+',file.name)
                subprocess.run([*ssh,'cat > /tmp/apollo-video-vectors-v1/'+file.name],input=file.read_bytes(),
                               capture_output=True,timeout=45,check=True)
        if args.video_player_audit_only:
            name='apollo-video-player-audit'
            subprocess.run([*ssh,'cat > /tmp/'+name],input=(BASE/'work'/name).read_bytes(),capture_output=True,timeout=15,check=True)
            subprocess.run([*ssh,'sudo -S -p "" install -m755 /tmp/'+name+' /usr/local/sbin/'+name],
                           input=test_password,capture_output=True,timeout=15,check=True)
            subprocess.run([*ssh,'mkdir -p /tmp/apollo-video-vectors-v1'],capture_output=True,timeout=10,check=True)
            file=BASE/'work/video-vectors-v1/h264-720p-long.mp4'
            subprocess.run([*ssh,'cat > /tmp/apollo-video-vectors-v1/'+file.name],input=file.read_bytes(),
                           capture_output=True,timeout=45,check=True)
        if args.clock_player_audit_only or args.clock_regression_audit_only:
            name='apollo-clock-audit'
            subprocess.run([*ssh,'cat > /tmp/'+name],input=(BASE/'work'/name).read_bytes(),capture_output=True,timeout=15,check=True)
            subprocess.run([*ssh,'sudo -S -p "" install -m755 /tmp/'+name+' /usr/local/sbin/'+name],
                           input=test_password,capture_output=True,timeout=15,check=True)
        if args.backlight_regression_audit_only:
            name='apollo-backlight-audit'
            subprocess.run([*ssh,'cat > /tmp/'+name],input=(BASE/'work'/name).read_bytes(),capture_output=True,timeout=15,check=True)
            subprocess.run([*ssh,'sudo -S -p "" install -m755 /tmp/'+name+' /usr/local/sbin/'+name],
                           input=test_password,capture_output=True,timeout=15,check=True)
        if args.apr_regression_audit_only:
            name='apollo-apr-dma-audit'
            subprocess.run([*ssh,'cat > /tmp/'+name],input=(BASE/'work'/name).read_bytes(),capture_output=True,timeout=15,check=True)
            subprocess.run([*ssh,'sudo -S -p "" install -m755 /tmp/'+name+' /usr/local/sbin/'+name],
                           input=test_password,capture_output=True,timeout=15,check=True)
            module=(BASE/'work/apr-dma-audit/apollo_apr_dma_audit.ko').read_bytes()
            subprocess.run([*ssh,'cat > /tmp/apollo-apr-dma-audit.ko'],input=module,capture_output=True,timeout=15,check=True)
            subprocess.run([*ssh,'sudo -S -p "" install -m644 /tmp/apollo-apr-dma-audit.ko /run/apollo-apr-dma-audit.ko'],
                           input=test_password,capture_output=True,timeout=15,check=True)
            audit_result['apr_audit_module_sha256']=hashlib.sha256(module).hexdigest()
        if args.focus_supply_audit_only:
            name='apollo-focus-matrix-audit' if args.focus_matrix_audit_only else 'apollo-focus-supply-audit'
            subprocess.run([*ssh,'cat > /tmp/'+name],input=(BASE/'work'/name).read_bytes(),capture_output=True,timeout=15,check=True)
            subprocess.run([*ssh,'sudo -S -p "" install -m755 /tmp/'+name+' /usr/local/sbin/'+name],
                           input=test_password,capture_output=True,timeout=15,check=True)
            module=(BASE/'work/focus-supply-audit/apollo_focus_supply_audit.ko').read_bytes()
            subprocess.run([*ssh,'cat > /tmp/apollo-focus-supply-audit.ko'],input=module,capture_output=True,timeout=15,check=True)
            subprocess.run([*ssh,'sudo -S -p "" install -m644 /tmp/apollo-focus-supply-audit.ko /run/apollo-focus-supply-audit.ko'],
                           input=test_password,capture_output=True,timeout=15,check=True)
            audit_result['focus_supply_module_sha256']=hashlib.sha256(module).hexdigest()
        if args.focus_clock_regression_audit_only or args.focus_trace_startup_audit_only:
            name='apollo-focus-normal-audit'
            audit_result['focus_normal_audit_sha256']=hashlib.sha256((BASE/'work'/name).read_bytes()).hexdigest()
            subprocess.run([*ssh,'cat > /tmp/'+name],input=(BASE/'work'/name).read_bytes(),capture_output=True,timeout=15,check=True)
            subprocess.run([*ssh,'sudo -S -p "" install -m755 /tmp/'+name+' /usr/local/sbin/'+name],
                           input=test_password,capture_output=True,timeout=15,check=True)
        if args.focus_trace_startup_audit_only:
            name='apollo-focus-trace-audit'
            audit_result['focus_trace_audit_sha256']=hashlib.sha256((BASE/'work'/name).read_bytes()).hexdigest()
            subprocess.run([*ssh,'cat > /tmp/'+name],input=(BASE/'work'/name).read_bytes(),capture_output=True,timeout=15,check=True)
            subprocess.run([*ssh,'sudo -S -p "" install -m755 /tmp/'+name+' /usr/local/sbin/'+name],
                           input=test_password,capture_output=True,timeout=15,check=True)
        if args.network_location_audit_only:
            native_wait=subprocess.run([*ssh, 'test -x /usr/bin/apollo-wait-loc'],capture_output=True,timeout=10)
            if native_wait.returncode:
                content=(BASE/'work/apollo-wait-loc').read_bytes()
                assert content[:4]==b'\x7fELF' and int.from_bytes(content[18:20],'little')==183
                subprocess.run([*ssh, 'cat > /tmp/apollo-wait-loc'], input=content,
                               capture_output=True, timeout=15, check=True)
                subprocess.run([*ssh, 'sudo -S -p "" install -m755 /tmp/apollo-wait-loc /usr/local/sbin/apollo-wait-loc'],
                               input=test_password, capture_output=True, timeout=15, check=True)
                config=b'[Service]\nExecStartPre=-/usr/local/sbin/apollo-wait-loc\n'
                subprocess.run([*ssh, 'cat > /tmp/apollo-loc-ready.conf'],input=config,
                               capture_output=True, timeout=15, check=True)
                subprocess.run([*ssh, 'sudo -S -p "" install -Dm644 /tmp/apollo-loc-ready.conf /run/systemd/system/ModemManager.service.d/20-apollo-loc-ready.conf'],
                               input=test_password, capture_output=True, timeout=15, check=True)
            subprocess.run([*ssh, 'cat > /tmp/apollo-desktop-gps-audit'],
                           input=(BASE/'work/apollo-desktop-gps-audit').read_bytes(),
                           capture_output=True, timeout=15, check=True)
            subprocess.run([*ssh, 'sudo -S -p "" install -m755 /tmp/apollo-desktop-gps-audit /usr/local/sbin/apollo-desktop-gps-audit'],
                           input=test_password, capture_output=True, timeout=15, check=True)
            for name in ('apollo-geoclue-audit', 'apollo-geoclue-client-audit', 'apollo-geoclue-dbus-audit', 'apollo_geoclue_reference.py'):
                subprocess.run([*ssh, 'cat > /tmp/'+name], input=(BASE/'work'/name).read_bytes(),
                               capture_output=True, timeout=15, check=True)
                subprocess.run([*ssh, 'sudo -S -p "" install -m755 /tmp/'+name+' /usr/local/sbin/'+name],
                               input=test_password, capture_output=True, timeout=15, check=True)
        if args.camera_stress_audit:
            subprocess.run([*ssh, 'cat > /tmp/apollo-camera-stress'], input=(BASE / 'work/apollo-camera-stress').read_bytes(),
                           capture_output=True, timeout=15, check=True)
            subprocess.run([*ssh, 'sudo -S -p "" install -m755 /tmp/apollo-camera-stress /usr/local/sbin/apollo-camera-stress'],
                           input=test_password, capture_output=True, timeout=15, check=True)
        if args.gps_audit:
            subprocess.run([*ssh, 'cat > /tmp/apollo-location-audit'], input=(BASE / 'work/apollo-location-audit').read_bytes(),
                           capture_output=True, timeout=15, check=True)
            subprocess.run([*ssh, 'sudo -S -p "" install -m755 /tmp/apollo-location-audit /usr/local/sbin/apollo-location-audit'],
                           input=test_password, capture_output=True, timeout=15, check=True)
            if (BASE / 'work/apollo-gnss-probe').exists():
                probe_data = (BASE / 'work/apollo-gnss-probe').read_bytes()
                assert probe_data[:4] == b'\x7fELF' and int.from_bytes(probe_data[18:20], 'little') == 183
                subprocess.run([*ssh, 'cat > /tmp/apollo-gnss-probe'], input=probe_data,
                               capture_output=True, timeout=15, check=True)
                subprocess.run([*ssh, 'sudo -S -p "" install -m755 /tmp/apollo-gnss-probe /usr/local/sbin/apollo-gnss-probe'],
                               input=test_password, capture_output=True, timeout=15, check=True)
        if args.fingerprint_audit:
            for name in ('apollo-fingerprint-audit', 'qsee-supplicant', 'qsee-app-loader', 'apollo-fpc-info'):
                content = (BASE / 'work' / name).read_bytes()
                if name != 'apollo-fingerprint-audit':
                    assert content[:4] == b'\x7fELF' and int.from_bytes(content[18:20], 'little') == 183
                subprocess.run([*ssh, 'cat > /tmp/' + name], input=content,
                               capture_output=True, timeout=15, check=True)
                subprocess.run([*ssh, 'sudo -S -p "" install -m755 /tmp/' + name + ' /usr/local/sbin/' + name],
                               input=test_password, capture_output=True, timeout=15, check=True)
            subprocess.run([*ssh, 'mkdir -p /tmp/apollo-fpc-firmware'], capture_output=True, check=True)
            for firmware in sorted((BASE / 'work/phone-next/fpc-firmware').glob('fpcapo.*')):
                assert re.fullmatch(r'fpcapo\.(mdt|b0[0-7])', firmware.name)
                subprocess.run([*ssh, 'cat > /tmp/apollo-fpc-firmware/' + firmware.name], input=firmware.read_bytes(),
                               capture_output=True, timeout=20, check=True)
            for name in ('apollo-fpc-gpio.ko', 'apollo-fpc-test.dtbo'):
                if (BASE / 'work' / name).exists():
                    subprocess.run([*ssh, 'cat > /tmp/' + name], input=(BASE / 'work' / name).read_bytes(),
                                   capture_output=True, timeout=15, check=True)
        if args.iris_diagnostic_module:
            module_data = args.iris_diagnostic_module.read_bytes()
            subprocess.run([*ssh, 'cat > /tmp/apollo-iris-diagnostic.ko'], input=module_data,
                           capture_output=True, timeout=15, check=True)
            module_path = '/usr/lib/modules/7.1.0/kernel/drivers/media/platform/qcom/iris/qcom-iris.ko'
            subprocess.run([*ssh, 'sudo -S -p "" install -m644 /tmp/apollo-iris-diagnostic.ko ' + module_path],
                           input=test_password, capture_output=True, timeout=15, check=True)
            audit_result['diagnostic_iris_module_sha256'] = hashlib.sha256(module_data).hexdigest()
        if args.audio_audit_only:
            subprocess.run([*ssh, 'cat > /tmp/apollo-audio-update'], input=(BASE / 'work/apollo-audio-sweep').read_bytes(),
                           capture_output=True, timeout=15, check=True)
            subprocess.run([*ssh, 'sudo -S -p "" install -m755 /tmp/apollo-audio-update /usr/local/sbin/apollo-audio-sweep'],
                           input=test_password, capture_output=True, timeout=15, check=True)
        for name, follow in [('kernel-live', 'dmesg --follow --color=never'),
                             ('journal-live', 'journalctl -b -f -o short-monotonic --no-pager')]:
            log = (report / (name + '.txt')).open('wb', buffering=0)
            logs.append(log)
            monitor = subprocess.Popen([*ssh, 'sudo -S -p "" ' + follow],
                                       stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT)
            monitor.stdin.write(test_password)
            monitor.stdin.close()
            monitors.append(monitor)
        phases = (['cameras'] if args.camera_audit_only else ['basic']) + (['camera-stress'] if args.camera_stress_audit else []) + (['video'] if args.video_audit else []) + (['suspend'] if args.suspend_audit else []) + (['modem'] if args.modem_audit else []) + (['navigation'] if args.gps_audit else [])
        if args.fingerprint_audit:
            phases.insert(next((i for i, p in enumerate(phases) if p in ('modem', 'navigation')), len(phases)), 'fingerprint')
        if args.audio_audit_only: phases = ['audio']
        if args.wifi_audit: phases += ['network']
        if args.wifi_audit_only: phases = ['network']
        if args.network_location_audit_only: phases = ['network', 'modem', 'desktop-gps', 'geoclue']
        if args.location_startup_audit_only: phases = ['network', 'location-startup']
        if args.video_extended_audit_only: phases = ['video-extended']
        if args.video_player_audit_only: phases = ['video-player']
        if args.quiet_regression_audit_only: phases = ['network','location-startup','video-player','suspend','camera-stress']
        if args.clock_player_audit_only: phases = ['clock','video-player']
        if args.clock_regression_audit_only: phases.insert(0,'clock')
        if args.backlight_regression_audit_only: phases = ['backlight','video-player','suspend','backlight-resume']
        if args.apr_regression_audit_only: phases = ['apr-dma','video-player','suspend']
        if args.focus_supply_audit_only: phases = ['focus-supply','video-player','suspend']
        if args.focus_stream_audit_only: phases = ['focus-stream','video-player','suspend']
        if args.focus_matrix_audit_only: phases = ['focus-matrix','video-player','suspend']
        if args.hold_native_diagnostics: phases = []
        if args.focus_clock_regression_audit_only: phases = ['focus-normal','cameras-no-save','video-player','suspend','focus-resume','camera-stress']
        if args.focus_trace_startup_audit_only: phases = ['focus-trace']
        with (report / 'audit-console.txt').open('wb') as log:
            for phase in phases:
                print('Native audit phase:', phase, flush=True)
                if phase == 'suspend':
                    # Sleep disconnects USB. Run this check as a detached unit,
                    # then reconnect instead of treating a TCP reset as failure.
                    check = '/usr/local/sbin/apollo-hardware-audit --suspend > /run/apollo-audit/suspend-host-console.txt 2>&1; echo $? > /run/apollo-audit/suspend-host-exit'
                    launch = shlex.join(['systemd-run', '--unit=apollo-suspend-audit', '--collect', '--no-block', '/bin/bash', '-c', check])
                    subprocess.run([*ssh, 'sudo -S -p "" ' + launch], input=test_password,
                                   stdout=log, stderr=subprocess.STDOUT, timeout=15, check=True)
                    deadline = time.monotonic() + 65
                    while time.monotonic() < deadline:
                        time.sleep(2)
                        probe = subprocess.run([*ssh, 'cat /run/apollo-audit/suspend-host-exit'], capture_output=True, timeout=10)
                        if probe.returncode == 0:
                            command_exit = int(probe.stdout.strip())
                            subprocess.run([*ssh, 'cat /run/apollo-audit/suspend-host-console.txt'], stdout=log, stderr=subprocess.STDOUT, timeout=10, check=True)
                            break
                    else:
                        raise RuntimeError('Suspend check did not reconnect within 65 seconds')
                else:
                    result = subprocess.run([*ssh, 'sudo -n /usr/local/sbin/apollo-hardware-audit --' + phase],
                                            stdout=log, stderr=subprocess.STDOUT, timeout=(850 if phase=='video-extended' else 650 if phase in ('desktop-gps','location-startup') else 520 if phase == 'basic' else 450))
                    command_exit = result.returncode
                audit_result[phase + '_exit'] = command_exit
                if command_exit == 255:
                    raise RuntimeError('USB SSH lost during phase ' + phase)
                with (report / ('hardware-' + phase + '.tar.gz')).open('wb') as archive:
                    subprocess.run([*ssh, 'sudo -S -p "" tar -C /run -czf - apollo-audit'],
                                   input=test_password, stdout=archive, stderr=subprocess.PIPE, timeout=60, check=True)
                print('Native reports saved after phase:', phase, flush=True)
        audit_result['report_directory'] = str(report)
        if args.hold_native_diagnostics:
            (report/'native-diagnostic-ready.json').write_text(json.dumps({'tag':tag,'live_images':live_set,
                'maximum_hold_seconds':600,'release_file':'release-native'},indent=2)+'\n')
            print('Native diagnostic window ready:',report.name,flush=True)
            deadline=time.monotonic()+600
            while time.monotonic()<deadline and not (report/'release-native').exists() and not stop_upload.is_set():
                time.sleep(1)
            audit_result['diagnostic_window_released']=(report/'release-native').exists()
            with (report/'hardware-diagnostics.tar.gz').open('wb') as archive:
                subprocess.run([*ssh,'sudo -S -p "" tar -C /run -czf - apollo-audit'],input=test_password,
                    stdout=archive,stderr=subprocess.PIPE,timeout=60,check=True)
        print('Native hardware reports downloaded:', report.name, flush=True)
        # The overlay is entirely in RAM; firmware and userdata are unmounted.
        subprocess.run([*ssh, 'sudo -S -p "" /usr/local/sbin/reboot-bootloader'],
                       input=test_password, capture_output=True, timeout=20)
    except Exception as error:
        audit_result['error'] = str(error)
        print('Hardware audit issue:', error, flush=True)
    finally:
        for monitor in monitors:
            monitor.terminate()
            try: monitor.wait(timeout=5)
            except subprocess.TimeoutExpired: monitor.kill()
        for log in logs: log.close()
        audit_done.set()
def upload():
    deadline = time.monotonic() + 200
    connection = None
    while time.monotonic() < deadline and not stop_upload.is_set():
        try:
            connection = socket.create_connection(('172.16.42.1', 2323), timeout=2)
            break
        except OSError:
            time.sleep(2)
    if connection is None:
        upload_failure.append('USB network did not become reachable')
        return
    try:
        connection.settimeout(60)
        sent = 0
        report = 0
        with rootfs.open('rb') as stream:
            while block := stream.read(4 * 1024 * 1024):
                if stop_upload.is_set(): return
                connection.sendall(block)
                sent += len(block)
                if sent - report >= 256 * 1024 * 1024:
                    print('Live desktop transfer:', round(sent / rootfs.stat().st_size * 100), '%', flush=True)
                    report = sent
        connection.shutdown(socket.SHUT_WR)
        print('Live desktop transfer complete', flush=True)
        upload_done.set()
    except OSError as error:
        upload_failure.append(str(error))
    finally:
        connection.close()

if not args.from_bootloader:
    command('adb', 'wait-for-device', timeout=60)
    for attempt in range(20):
        completed = command('adb', 'shell', 'getprop', 'sys.boot_completed', required=False, timeout=8)
        if completed.strip() == '1':
            break
        time.sleep(3)
    else:
        raise SystemExit('Android boot is not complete; nothing changed')
    command('adb', 'reboot', 'bootloader')
if not wait_bootloader(40): raise SystemExit('Bootloader not detected; nothing changed')
# Enumeration and even partition size can precede usable UFS/download state.
# Use the same two-snapshot guard before erasing as before restoring DTBO.
subprocess.run([sys.executable,str(BASE/'work/restore_dtbo_checked.py'),'hardware-'+tag,'--preflight'],
               timeout=300,check=True)
changed = False
console = None
state = {'desktop_running': False, 'rootfs_verified_on_phone': False, 'live_images': live_set,
         'image_set_directory':str(image_directory),
         'host_clock_injection_enabled': not args.no_host_clock}
try:
    changed = True
    command('fastboot', 'erase', 'dtbo')
    command('fastboot', 'boot', str(image), timeout=90)
    uploader = threading.Thread(target=upload, daemon=True)
    uploader.start()
    started = time.monotonic()
    buffer = bytearray()
    last_check = 0
    checks = 0
    switching_at = None
    desktop_at = None
    return_requested = False
    early_trace_sent = False
    log_name = ('hardware-' + tag + '-serial.log') if args.hardware_audit else 'live-serial.log'
    with (EXPERIMENTAL / log_name).open('wb', buffering=0) as log:
        while time.monotonic() - started < (1600 if args.video_extended_audit_only else 1500 if args.modem_audit else 1000 if args.hardware_audit else 680):
            if present():
                print('Returned to bootloader', flush=True)
                break
            if console is None:
                for port in list_ports.comports():
                    if port.vid == 0x1d6b and port.pid == 0x0104:
                        try:
                            console = serial.Serial(port.device, 115200, timeout=0.3)
                            print('Live USB console:', port.device, flush=True)
                        except serial.SerialException:
                            pass
            if console is not None:
                try:
                    data = console.read(65536)
                    if data:
                        buffer.extend(data)
                        log.write(data)
                    if b'ARCH-LIVE-IMAGE-VERIFIED' in buffer:
                        state['rootfs_verified_on_phone'] = True
                    if args.focus_trace_startup_audit_only and not early_trace_sent and b'APOLLO-LIVE-UPLOAD-READY' in buffer:
                        setup=(BASE/'work/setup_focus_trace.sh').read_text(encoding='utf-8')
                        state['focus_trace_setup_sha256']=hashlib.sha256(setup.encode()).hexdigest()
                        console.write(('\nsh -c '+shlex.quote(setup)+' || echo APOLLO_FOCUS_TRACE_SETUP_FAILED\n').encode())
                        early_trace_sent=True
                        print('Installing filtered startup tracing in RAM',flush=True)
                    if args.focus_trace_startup_audit_only and early_trace_sent:
                        state['early_focus_trace_setup_acknowledged']=b'\r\nAPOLLO_FOCUS_TRACE_SETUP_OK\r\n' in buffer
                    if b'STARTING-ARCH-SYSTEMD-AND-KDE' in buffer and switching_at is None and not return_requested:
                        switching_at = time.monotonic()
                        print('Arch systemd is starting on the phone', flush=True)
                    if switching_at and not return_requested and time.monotonic() - switching_at > 20 and time.monotonic() - last_check > 25:
                        date = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                        clock_command = "date -u -s '" + date + "'" if checks == 0 and not args.no_host_clock else 'date -u'
                        query = "\necho APOLLO_ARCH_STATUS; " + clock_command + "; cat /etc/os-release; uname -r; systemctl is-active sddm; pgrep -a -x kwin_wayland; pgrep -a -x plasmashell; nmcli device; journalctl -b -u sddm --no-pager -n 35; echo APOLLO_ARCH_STATUS_END\n"
                        console.write(query.encode())
                        last_check = time.monotonic()
                        checks += 1
                    if not return_requested and (b'plasmashell --no-respawn' in buffer or b'/usr/bin/plasmashell' in buffer):
                        if desktop_at is None:
                            desktop_at = time.monotonic()
                            state['desktop_running'] = True
                            print('KDE plasmashell process detected', flush=True)
                    if args.hardware_audit and switching_at and not audit_started and time.monotonic() - switching_at > 45:
                        audit_started = True
                        threading.Thread(target=hardware_audit, daemon=True).start()
                        print('Running native hardware audit over USB SSH', flush=True)
                    finished = audit_done.is_set() if args.hardware_audit else ((switching_at and checks >= 6 and time.monotonic() - last_check > 12) or (desktop_at and time.monotonic() - desktop_at > 45))
                    if finished and not return_requested:
                        console.write(b'\necho RETURNING_TO_BOOTLOADER; sync; /usr/local/sbin/reboot-bootloader\n')
                        print('Desktop diagnostics collected; returning to bootloader', flush=True)
                        return_requested = True
                        switching_at = None
                        desktop_at = None
                    if upload_failure:
                        print('Upload issue:', upload_failure[-1], flush=True)
                        console.write(b'\n/sbin/reboot-bootloader\n')
                        break
                except serial.SerialException:
                    console.close()
                    console = None
            time.sleep(0.5)
    state['upload_completed'] = upload_done.is_set()
    state['upload_errors'] = upload_failure
    state['hardware_audit'] = audit_result
    result_name = ('hardware-' + tag + '-result.json') if args.hardware_audit else 'live-result.json'
    (EXPERIMENTAL / result_name).write_text(json.dumps(state, indent=2), encoding='utf-8')
finally:
    stop_upload.set()
    if changed and not present() and console is not None:
        try:
            console.write(b'\nsystemctl reboot --reboot-argument=bootloader\n')
        except serial.SerialException:
            pass
    if console is not None: console.close()
    if changed:
        if present() or wait_bootloader(30):
            # Require a stable product, exact partition size and sufficient
            # download limit. Product alone can precede UFS initialization.
            subprocess.run([sys.executable,str(BASE/'work/restore_dtbo_checked.py'),'hardware-'+tag],
                           timeout=300,check=True)
            print('Original Android DTBO restored through checked recovery', flush=True)
        else:
            raise SystemExit('Manual bootloader entry is needed to restore the original DTBO')
