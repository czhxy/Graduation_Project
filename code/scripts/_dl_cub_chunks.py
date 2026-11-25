# -*- coding: utf-8 -*-
"""CUB_200_2011.tgz 小分块下载：每块 12 MB，确保在签名 60s 有效期内完成。

用法：python _dl_cub_chunks.py
"""
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ORIG = "https://data.caltech.edu/records/65de6-vp158/files/CUB_200_2011.tgz"
TOTAL = 1_150_585_339
CHUNK = 12 << 20
NTHREAD = 8
DST = Path(r"C:\Users\cz\Desktop\Graduation_Project\data\raw\CUB_200_2011.tgz")
PARTS = Path(r"C:\Users\cz\Desktop\Graduation_Project\data\raw\_cub_parts")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_lock = threading.Lock()
_sig = {"url": None, "ts": 0.0}


def log(msg):
    with _lock:
        print(msg, flush=True)


def signed():
    with _lock:
        if _sig["url"] is None or time.time() - _sig["ts"] > 30:
            for _ in range(3):
                try:
                    out = subprocess.run(
                        ["curl.exe", "-sS", "-o", "NUL", "-w", "%{url_effective}", "-L",
                         "--max-time", "30", ORIG],
                        capture_output=True, text=True, timeout=45)
                    u = out.stdout.strip()
                    if u.startswith("http"):
                        _sig["url"], _sig["ts"] = u, time.time()
                        return u
                except Exception:
                    pass
                time.sleep(1)
            raise RuntimeError("签名失败")
        return _sig["url"]


def fetch_chunk(i):
    start = i * CHUNK
    end = min(start + CHUNK, TOTAL) - 1
    part = PARTS / f"{i:04d}"
    pos = start + (part.stat().st_size if part.exists() else 0)
    for attempt in range(40):
        if pos > end:
            return True
        try:
            req = urllib.request.Request(
                signed(), headers={"Range": f"bytes={pos}-{end}", "User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=45) as r:
                if r.status != 206:
                    raise RuntimeError(f"HTTP {r.status}")
                with open(part, "ab") as fh:
                    while pos <= end:
                        b = r.read(1 << 16)
                        if not b:
                            break
                        fh.write(b)
                        pos += len(b)
        except urllib.error.HTTPError as e:
            if e.code in (403, 401):
                with _lock:
                    _sig["url"] = None
            time.sleep(1 + attempt * 0.2)
        except Exception:
            time.sleep(1 + attempt * 0.2)
    return False


def main():
    PARTS.mkdir(parents=True, exist_ok=True)
    n = (TOTAL + CHUNK - 1) // CHUNK
    log(f"{n} 块 × {CHUNK/1e6:.0f} MB，{NTHREAD} 线程")
    t0 = time.time()
    ok = 0
    with ThreadPoolExecutor(max_workers=NTHREAD) as ex:
        for i, res in enumerate(ex.map(fetch_chunk, range(n))):
            ok += bool(res)
            if (i + 1) % 12 == 0:
                have = sum(p.stat().st_size for p in PARTS.iterdir())
                log(f"  {i+1}/{n} 块处理完，累计 {have/1e6:.0f} MB，"
                    f"{time.time()-t0:.0f}s")
    log(f"成功块 {ok}/{n}")

    with open(DST, "wb") as out:
        for i in range(n):
            p = PARTS / f"{i:04d}"
            out.write(p.read_bytes())
    size = DST.stat().st_size
    log(f"合并后 {size:,} / {TOTAL:,}")
    if size != TOTAL:
        raise SystemExit(1)
    log("完成")


if __name__ == "__main__":
    main()
