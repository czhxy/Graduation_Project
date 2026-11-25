# -*- coding: utf-8 -*-
"""多线程分块下载 CUB_200_2011.tgz（Caltech 签名直链单连接会被限速）。"""
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ORIG = "https://data.caltech.edu/records/65de6-vp158/files/CUB_200_2011.tgz"
TOTAL = 1_150_585_339
NCHUNK = 8
DST = Path(r"C:\Users\cz\Desktop\Graduation_Project\data\raw\CUB_200_2011.tgz")
PARTS = Path(r"C:\Users\cz\Desktop\Graduation_Project\data\raw\_cub_parts")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_lock_signer = __import__("threading").Lock()
_signed = {"url": None, "ts": 0.0}


def log(msg):
    print(msg, flush=True)


def signed_url():
    with _lock_signer:
        if _signed["url"] is None or time.time() - _signed["ts"] > 40:
            # 只取 1 字节：签名直链与区间无关，避免每次刷新把整个文件下到 NUL
            out = subprocess.run(
                ["curl.exe", "-sS", "-o", "NUL", "-w", "%{url_effective}", "-L",
                 "-r", "0-0", "--max-time", "40", ORIG],
                capture_output=True, text=True, timeout=60)
            _signed["url"] = out.stdout.strip()
            _signed["ts"] = time.time()
        return _signed["url"]


def worker(idx, start, end):
    part = PARTS / f"part{idx:02d}"
    pos = start + (part.stat().st_size if part.exists() else 0)
    fails = 0
    with open(part, "ab") as fh:
        while pos < end:
            try:
                url = signed_url()
                req = urllib.request.Request(
                    url, headers={"Range": f"bytes={pos}-{end - 1}",
                                  "User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    if r.status != 206:
                        raise RuntimeError(f"HTTP {r.status}")
                    while pos < end:
                        # 只读到本块末尾，避免越过 end 造成分块超长、合并后错位
                        chunk = r.read(min(1 << 18, end - pos))
                        if not chunk:
                            break
                        fh.write(chunk)
                        pos += len(chunk)
                fh.flush()
                fails = 0
            except Exception as e:
                fails += 1
                if fails % 5 == 1:
                    log(f"  [chunk {idx}] {type(e).__name__}，已 {pos - start:,} / {end - start:,}")
                if fails > 60:
                    return pos
                time.sleep(2)
    return pos


def main():
    PARTS.mkdir(parents=True, exist_ok=True)
    chunk = TOTAL // NCHUNK
    jobs = []
    for i in range(NCHUNK):
        s = i * chunk
        e = TOTAL if i == NCHUNK - 1 else (i + 1) * chunk
        jobs.append((i, s, e))
    log(f"开始：{NCHUNK} 块，每块约 {chunk/1e6:.0f} MB")
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=NCHUNK) as ex:
        futs = [ex.submit(worker, i, s, e) for i, s, e in jobs]
        done = [f.result() for f in futs]
    log(f"各块结束位置：{done}")
    elapsed = time.time() - t0
    log(f"耗时 {elapsed/60:.1f} 分钟")

    # 合并前逐块核对大小，防止并发写入/越界导致分块超长
    bad = []
    for i, s, e in jobs:
        sz = (PARTS / f"part{i:02d}").stat().st_size if (PARTS / f"part{i:02d}").exists() else 0
        if sz != e - s:
            bad.append((i, sz, e - s))
    if bad:
        for i, sz, want in bad:
            log(f"!! part{i:02d} 大小 {sz:,} != 期望 {want:,}")
        log("!! 分块大小不符，拒绝合并（删除 _cub_parts 后重下）")
        raise SystemExit(1)

    with open(DST, "wb") as out:
        for i, _, _ in jobs:
            with open(PARTS / f"part{i:02d}", "rb") as f:
                while True:
                    b = f.read(1 << 22)
                    if not b:
                        break
                    out.write(b)
    size = DST.stat().st_size
    log(f"合并后 {size:,} / {TOTAL:,}")
    if size != TOTAL:
        log("!! 不完整")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
