# -*- coding: utf-8 -*-
"""断点续传下载 CUB_200_2011.tgz（Caltech 签名重定向对 curl -C - 不友好）。

用法：python download_cub.py
"""
import hashlib
import os
import sys
import time
import urllib.request
from pathlib import Path

URL = "https://data.caltech.edu/records/65de6-vp158/files/CUB_200_2011.tgz"
OUT = Path(r"C:\Users\cz\Desktop\Graduation_Project\data\raw\CUB_200_2011.tgz")
TOTAL = 1_150_585_339

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def log(msg):
    print(msg, flush=True)


def attempt(pos, fh):
    req = urllib.request.Request(URL, headers={"Range": f"bytes={pos}-",
                                               "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        if r.status == 200 and pos > 0:
            log(f"  服务器返回 200（不支持续传），从 0 重来")
            fh.seek(0)
            fh.truncate()
            pos = 0
        elif r.status not in (200, 206):
            raise RuntimeError(f"HTTP {r.status}")
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)
            pos += len(chunk)
            if pos % (50 << 20) < (1 << 20):
                log(f"  {pos/1e6:7.1f} MB / {TOTAL/1e6:.1f} MB  ({pos/TOTAL:5.1%})")
    return pos


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pos = OUT.stat().st_size if OUT.exists() else 0
    if pos > TOTAL:
        OUT.unlink()
        pos = 0
    log(f"起点 {pos/1e6:.1f} MB / {TOTAL/1e6:.1f} MB")
    with open(OUT, "ab" if pos else "wb") as fh:
        for i in range(60):
            try:
                pos = attempt(pos, fh)
                fh.flush()
                if pos >= TOTAL:
                    break
                log(f"  连接结束于 {pos/1e6:.1f} MB，续传（第 {i+1} 次）")
            except Exception as e:
                log(f"  异常：{type(e).__name__}: {e}；3 秒后重试")
                time.sleep(3)
                pos = OUT.stat().st_size
                fh.seek(pos)
    size = OUT.stat().st_size
    log(f"完成：{size:,} bytes")
    if size != TOTAL:
        log("!! 大小不符，未完成")
        raise SystemExit(1)
    h = hashlib.sha256()
    with open(OUT, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    log(f"sha256={h.hexdigest()}")


if __name__ == "__main__":
    main()
