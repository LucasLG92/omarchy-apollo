"""Exercise only this process's 64 MiB of synthetic private anonymous pages."""
from pathlib import Path
import ctypes, hashlib, json, mmap, re, struct, time

zram = Path('/sys/block/zram0')
algorithm = (zram/'comp_algorithm').read_text().strip()
assert '[zstd]' in algorithm, 'Requested zstd backend is not selected'
swaps = Path('/proc/swaps').read_text().splitlines()[1:]
assert len(swaps) == 1 and swaps[0].split()[0] == '/dev/zram0', 'Unexpected active swap device'
available = next(int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()
                 if line.startswith('MemAvailable:'))
assert available > 1024**3, 'Keep a large margin for the desktop'
length = 64*1024**2

def stats():
    numbers = list(map(int,(zram/'mm_stat').read_text().split()))
    return dict(zip(('original_bytes','compressed_bytes','allocated_bytes'), numbers[:3]))

def process_swap():
    return next(int(line.split()[1])*1024 for line in Path('/proc/self/status').read_text().splitlines()
                if line.startswith('VmSwap:'))

before = stats()
with mmap.mmap(-1, length, flags=mmap.MAP_PRIVATE|mmap.MAP_ANONYMOUS) as memory:
    body = (b'Apollo synthetic memory roundtrip; no user data. '*100)[:4088]
    body = body.ljust(4088,b'.')
    for page in range(length//4096):
        memory[page*4096:(page+1)*4096] = struct.pack('<Q',page)+body
    expected = hashlib.sha256(memory).hexdigest()
    # Python does not expose this Linux advice on every build. Verify its value
    # against the installed UAPI before using libc on this allocation alone.
    header = Path('/usr/include/asm-generic/mman-common.h').read_text()
    match = re.search(r'^#define\s+MADV_PAGEOUT\s+(\d+)\b',header,re.M)
    assert match and int(match[1]) == 21
    libc = ctypes.CDLL(None,use_errno=True)
    libc.madvise.argtypes = [ctypes.c_void_p,ctypes.c_size_t,ctypes.c_int]
    libc.madvise.restype = ctypes.c_int
    address = ctypes.addressof(ctypes.c_char.from_buffer(memory))
    assert libc.madvise(address,length,21) == 0, 'madvise failed: '+str(ctypes.get_errno())
    deadline = time.monotonic()+5
    while time.monotonic() < deadline and process_swap() < length//2:
        time.sleep(0.1)
    swapped = process_swap()
    compressed = stats()
    actual = hashlib.sha256(memory).hexdigest()
    result = {'kernel_package_release':21,'algorithm_selected':'zstd',
              'synthetic_private_bytes':length,'process_swapped_bytes_before_readback':swapped,
              'roundtrip_hash_matches':actual == expected,
              'zram_stats_before':before,'zram_stats_after_pageout':compressed,
              'only_active_swap_is_zram':True,'swap_reset_performed':False,
              'system_memory_pressure_test':False,'real_workload_benchmark':False}
    assert actual == expected, 'Synthetic memory changed after swap-in'
    assert swapped >= length//2, 'Not enough of this process was actually swapped out'
    assert compressed['original_bytes']-before['original_bytes'] >= length//2, 'No corresponding zram writes'
result['passed'] = True
print(json.dumps(result,indent=2))
