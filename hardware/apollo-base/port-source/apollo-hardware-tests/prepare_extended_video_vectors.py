from pathlib import Path
import hashlib,json,subprocess,time

root=Path('/root/apollo-build/video-vectors-v1')
host=Path('${APOLLO_REPO:?Set APOLLO_REPO to the checkout path}/work/video-vectors-v1')
root.mkdir(exist_ok=True); host.mkdir(exist_ok=True)
cases=[
    ('hevc-720p-b',1280,720,60,'hevc','libx265',
     ['-preset','fast','-x265-params','pools=4:frame-threads=2:log-level=error'], 'hevc_v4l2m2m','v4l2h265dec'),
    ('vp9-480p-causal',640,480,30,'ivf','libvpx-vp9',
     ['-deadline','realtime','-cpu-used','8','-row-mt','1','-lag-in-frames','0','-auto-alt-ref','0'], 'vp9_v4l2m2m','v4l2vp9dec'),
    ('vp9-720p-altref',1280,720,60,'ivf','libvpx-vp9',
     ['-deadline','good','-cpu-used','5','-row-mt','1','-lag-in-frames','25','-auto-alt-ref','1'], 'vp9_v4l2m2m','v4l2vp9dec'),
    ('h264-2160p',3840,2160,30,'h264','libx264',
     ['-preset','ultrafast','-tune','zerolatency'], 'h264_v4l2m2m','v4l2h264dec'),
    ('hevc-2160p',3840,2160,30,'hevc','libx265',
     ['-preset','ultrafast','-x265-params','pools=4:frame-threads=2:bframes=0:log-level=error'], 'hevc_v4l2m2m','v4l2h265dec'),
    ('h264-720p-long',1280,720,900,'h264','libx264',
     ['-preset','ultrafast','-tune','zerolatency'], 'h264_v4l2m2m','v4l2h264dec'),
]
manifest={'generator':'FFmpeg synthetic testsrc2, no audio','cases':[]}
for name,width,height,frames,fmt,encoder,options,decoder,gst in cases:
    extension={'hevc':'hevc','h264':'h264','ivf':'ivf'}[fmt]
    file=root/(name+'.'+extension)
    reference=root/(name+'.framemd5')
    args=['ffmpeg','-hide_banner','-nostdin','-loglevel','error','-y','-f','lavfi',
          '-i',f'testsrc2=size={width}x{height}:rate=30','-frames:v',str(frames),
          '-an','-threads','4','-c:v',encoder,*options,'-pix_fmt','yuv420p','-f',fmt,str(file)]
    started=time.monotonic()
    subprocess.run(args,check=True,timeout=180)
    subprocess.run(['ffmpeg','-hide_banner','-nostdin','-loglevel','error','-y','-i',str(file),
                    '-fps_mode','passthrough','-pix_fmt','yuv420p','-f','framemd5',str(reference)],check=True,timeout=90)
    expected=[line for line in reference.read_text().splitlines() if line and not line.startswith('#')]
    assert len(expected)==frames,(name,len(expected))
    import shutil
    for item in (file,reference): shutil.copyfile(item,host/item.name)
    manifest['cases'].append({'name':name,'width':width,'height':height,'fps':30,'frames':frames,
        'format':fmt,'decoder':decoder,'gst_decoder':gst,'file':file.name,'reference':reference.name,
        'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'bytes':file.stat().st_size,
        'reference_sha256':hashlib.sha256(reference.read_bytes()).hexdigest(),
        'encoder_arguments':args[args.index('-c:v'):],'generation_seconds':round(time.monotonic()-started,2)})
    print('Prepared',name,frames,'frames',flush=True)
(host/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('All synthetic video vectors and CPU references prepared')
