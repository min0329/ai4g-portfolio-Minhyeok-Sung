# Stream a big S3 object to stdout using parallel ranged curl requests, in order.
import subprocess, sys, concurrent.futures as cf
url, size = sys.argv[1], int(sys.argv[2]); CH = 64 << 20; W = 10
def get(i):
    a = i * CH; b = min(size, a + CH) - 1
    for t in range(6):
        p = subprocess.run(["curl", "-sS", "-f", "-m", "300", "-r", f"{a}-{b}", url], capture_output=True)
        if p.returncode == 0 and len(p.stdout) == b - a + 1: return p.stdout
    raise SystemExit(f"chunk {i} failed")
n = (size + CH - 1) // CH
out = sys.stdout.buffer
with cf.ThreadPoolExecutor(W) as ex:
    futs = {}
    for i in range(min(n, W * 2)): futs[i] = ex.submit(get, i)
    for i in range(n):
        data = futs.pop(i).result()
        if i + W * 2 < n: futs[i + W * 2] = ex.submit(get, i + W * 2)
        out.write(data)
        if i % 16 == 0: print(f"chunk {i}/{n}", file=sys.stderr, flush=True)
