#!/usr/bin/python3
"""Capture/discard real Apollo camera buffers through PipeWire, without files."""
import argparse
import gc
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import gi
gi.require_version('Gst','1.0')
from gi.repository import Gst

EXPECTED_NAMES={'Apollo Main Rear Camera','Apollo Front Camera',
                'Apollo Ultrawide Camera','Apollo Macro Camera'}


def graph():
    return json.loads(subprocess.check_output(['pw-dump'],text=True,timeout=5))


def sources(objects):
    return [n['info']['props'] for n in objects
            if n.get('info',{}).get('props',{}).get('media.class')=='Video/Source'
            and n['info']['props'].get('device.api')=='libcamera']


def cma_free_kib():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('CmaFree:'):
            return int(line.split()[1])
    return None


def capture(serial,frames):
    assert str(serial).isdecimal()
    pipeline=Gst.parse_launch('pipewiresrc client-name=OmarchyApolloCameraCheck target-object='+str(serial)
        +' num-buffers='+str(frames)+' ! video/x-raw,width=640,height=480 ! fakesink name=discard sync=false enable-last-sample=false')
    observed={'frames':0,'sizes':set(),'timestamps':[],'caps':None}
    def observe(pad,probe):
        buffer=probe.get_buffer()
        observed['frames']+=1
        observed['sizes'].add(buffer.get_size())
        observed['timestamps'].append(buffer.pts)
        if observed['caps'] is None:
            caps=pad.get_current_caps()
            observed['caps']=caps.to_string() if caps else None
        return Gst.PadProbeReturn.OK
    probe_id=pipeline.get_by_name('discard').get_static_pad('sink').add_probe(Gst.PadProbeType.BUFFER,observe)
    started=time.monotonic()
    eos=False
    try:
        assert pipeline.set_state(Gst.State.PLAYING)!=Gst.StateChangeReturn.FAILURE,'Pipeline could not start'
        message=pipeline.get_bus().timed_pop_filtered(20*Gst.SECOND,Gst.MessageType.ERROR|Gst.MessageType.EOS)
        assert message is not None,'Camera stream timed out'
        assert message.type!=Gst.MessageType.ERROR,'Camera pipeline reported an error; inspect local diagnostics separately'
        eos=message.type==Gst.MessageType.EOS
    finally:
        pipeline.get_by_name('discard').get_static_pad('sink').remove_probe(probe_id)
        pipeline.set_state(Gst.State.NULL)
        change,state,pending=pipeline.get_state(5*Gst.SECOND)
        assert state==Gst.State.NULL,'Camera pipeline did not release its stream'
    timestamps=observed['timestamps']
    assert eos and observed['frames']==frames,'Wrong camera buffer count'
    assert observed['sizes'] and min(observed['sizes'])>=640*480*3,'Camera buffers are incomplete'
    assert all(value!=Gst.CLOCK_TIME_NONE for value in timestamps),'Camera buffer has no timestamp'
    assert all(a<b for a,b in zip(timestamps,timestamps[1:])),'Camera timestamps did not advance'
    return {'frames':observed['frames'],'caps':observed['caps'],
            'buffer_sizes':sorted(observed['sizes']),'timestamps_advance':True,
            'stream_released':True,'elapsed_seconds':round(time.monotonic()-started,3)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cycles',type=int,default=3)
    parser.add_argument('--frames',type=int,default=30)
    args=parser.parse_args()
    assert 1<=args.cycles<=10 and 2<=args.frames<=120
    assert 1000<=os.getuid()<65534 and os.geteuid()==os.getuid(),'Run in the local desktop account, without sudo'
    runtime=Path('/run/user')/str(os.getuid())
    assert runtime.is_dir() and runtime.stat().st_uid==os.getuid()
    assert subprocess.check_output(['omarchy-hw-platform'],text=True).strip()=='aarch64-apollo'
    before=graph();cameras=sources(before)
    assert len(cameras)==4,'Expected all four Apollo camera sources'
    assert {n.get('node.description') for n in cameras}==EXPECTED_NAMES,'Install the Apollo camera naming policy first'
    source_ids={n['id'] for n in before if n.get('info',{}).get('props',{}).get('media.class')=='Video/Source'}
    assert not any(n['type']=='PipeWire:Interface:Link' and n.get('info',{}).get('output-node-id') in source_ids
                   and n['info'].get('state')=='active' for n in before),'Close camera applications before testing'
    Gst.init(None)
    memory_before=cma_free_kib()
    results=[]
    for cycle in range(1,args.cycles+1):
        for camera in sorted(cameras,key=lambda n:n['node.description']):
            try:
                result=capture(camera['object.serial'],args.frames)
                # Drop PyGObject callback cycles before opening another sensor.
                gc.collect()
            except Exception as error:
                raise RuntimeError('Cycle '+str(cycle)+', '+camera['node.description']
                                   +', CmaFree='+str(cma_free_kib())+' KiB') from error
            results.append({'cycle':cycle,'camera':camera['node.description'],
                            'cma_free_after_kib':cma_free_kib(),**result})
            print(json.dumps({'completed_cycle':cycle,'camera':camera['node.description'],
                              'frames':result['frames'],'cma_free_kib':cma_free_kib()}),file=sys.stderr,flush=True)
    after=graph()
    assert len(sources(after))==4,'A camera disappeared after stream cleanup'
    assert not any(str(n.get('info',{}).get('props',{}).get('application.process.id'))==str(os.getpid())
                   and n.get('info',{}).get('props',{}).get('media.class')=='Stream/Input/Video' for n in after),'A test stream remains'
    print(json.dumps({'camera_stream_tests_passed':len(results),'frames_per_open':args.frames,
                     'camera_count':4,'cycles':args.cycles,'results':results,
                     'all_four_sources_remain':True,'images_saved':False,'physical_display_used':False,
                     'cma_free_before_kib':memory_before,'cma_free_after_kib':cma_free_kib(),
                     'optical_quality_tested':False,'snapshot_ui_acceptance_tested':False},indent=2))


if __name__=='__main__':
    main()
