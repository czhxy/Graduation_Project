# -*- coding: utf-8 -*-
"""从 CUB-200-2011 的分割掩码生成 Waterbirds 的前景掩码（鸟 = 255）。

依据：官方 generate_waterbirds.py 的合成方式
    img_black = CUB 图 × CUB 掩码
    combined  = img_black + place × (1 - 掩码)
合成图与 CUB 原图**同尺寸**、鸟的位置与比例不变，所以
    Waterbirds 的前景掩码 == 同一张图的 CUB 掩码（不需要任何几何参数）。
本脚本据此把 CUB 掩码按 Waterbirds 的 img_filename 复制成
    data/raw/waterbirds/segmentations/<img_filename 的 .png 版本>
并抽样做像素级校验：掩码内合成图应与 CUB 原图接近（合成图存为 JPEG，存在有损重编码误差），
掩码外应与 CUB 原图明显不同。

用法（在 code/ 目录下）：
    python scripts/02_make_masks.py --config configs/base.yaml
产物：
    data/raw/waterbirds/segmentations/**
    data/raw/_mask_report.txt
"""
import argparse
import csv
import hashlib
import sys
import tarfile
from pathlib import Path

import numpy as np
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
CUB_TGZ = ROOT / "data" / "raw" / "CUB_200_2011.tgz"
SEG_TGZ = ROOT / "data" / "raw" / "segmentations.tgz"   # 官方记录 w9d68-gec53（CUB-200-2011 Segmentations）
CUB_DIR = ROOT / "data" / "raw" / "CUB_200_2011"
WB = ROOT / "data" / "raw" / "waterbirds"
REPORT = ROOT / "data" / "raw" / "_mask_report.txt"
N_CHECK = 20

lines = []


def log(msg=""):
    lines.append(str(msg))
    print(msg)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.parse_args()

    rows = list(csv.DictReader(open(WB / "metadata.csv", newline="", encoding="utf-8")))
    log(f"[1] Waterbirds 条目 {len(rows):,}")

    seg_dst = WB / "segmentations"
    seg_dst.mkdir(parents=True, exist_ok=True)

    if (CUB_DIR / "segmentations").exists():
        log("[2] CUB segmentations 已解压，跳过")
    else:
        if not SEG_TGZ.exists():
            raise SystemExit(f"缺少掩码包：{SEG_TGZ}（官方记录 w9d68-gec53 的 segmentations.tgz）")
        log(f"[2] 图像包：{CUB_TGZ.name}  {CUB_TGZ.stat().st_size:,} bytes")
        log(f"    sha256：{sha256(CUB_TGZ)}")
        log(f"    掩码包：{SEG_TGZ.name}  {SEG_TGZ.stat().st_size:,} bytes")
        log(f"    sha256：{sha256(SEG_TGZ)}")
        CUB_DIR.mkdir(parents=True, exist_ok=True)
        with tarfile.open(SEG_TGZ, "r:gz") as tf:
            members = [m for m in tf.getmembers()
                       if m.name.startswith("segmentations/") and m.name.lower().endswith(".png")]
            log(f"    只解压 segmentations/：{len(members):,} 个 png")
            for m in members:
                m.name = m.name.replace("segmentations/", "", 1)
                tf.extract(m, CUB_DIR / "segmentations", filter="data")

    # 生成掩码
    copied, missing = 0, []
    for r in rows:
        rel = r["img_filename"].replace(".jpg", ".png")
        src = CUB_DIR / "segmentations" / rel
        if not src.exists():
            missing.append(rel)
            continue
        dst = seg_dst / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            arr = (np.asarray(Image.open(src).convert("L")) > 127).astype(np.uint8) * 255
            Image.fromarray(arr).save(dst)
        copied += 1
    log(f"[3] 生成掩码 {copied:,} 个；缺失 {len(missing)}")
    if missing:
        log("    缺失示例：" + ", ".join(missing[:3]))

    # 抽样：从 CUB 包里取这 20 张原图，做像素级校验
    step = max(1, len(rows) // N_CHECK)
    sample = rows[::step][:N_CHECK]
    want = {"CUB_200_2011/images/" + r["img_filename"]: r["img_filename"] for r in sample}
    img_dir = CUB_DIR / "images"
    with tarfile.open(CUB_TGZ, "r:gz") as tf:
        for m in tf.getmembers():
            if m.name in want:
                rel = want[m.name]
                out = img_dir / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                m.name = rel
                tf.extract(m, img_dir, filter="data")

    log("[4] 抽样校验：掩码内合成图应接近 CUB 原图（JPEG 重编码容差内），掩码外应明显不同")
    ok = bad = 0
    fg_maes = []
    for r in sample:
        rel = r["img_filename"]
        seg_p = seg_dst / rel.replace(".jpg", ".png")
        cub_p = img_dir / rel
        wb_p = WB / rel
        if not (seg_p.exists() and cub_p.exists()):
            continue
        m = np.asarray(Image.open(seg_p)) > 127
        comp = np.asarray(Image.open(wb_p).convert("RGB")).astype(np.int16)
        cub = np.asarray(Image.open(cub_p).convert("RGB")).astype(np.int16)
        if comp.shape != cub.shape:
            log(f"    {rel[:44]:44s} 尺寸不符 {comp.shape} vs {cub.shape}")
            bad += 1
            continue
        d = np.abs(comp - cub)
        fg = float(d[m].mean())
        bg = float(d[~m].mean())
        # 合成图以 JPEG 保存，前景无法与原图逐字节相等；判据=前景差异小且远小于背景差异
        good = fg <= 20 and fg < bg
        ok += int(good)
        bad += int(not good)
        fg_maes.append(fg)
        log(f"    {rel[:44]:44s} {comp.shape[1]}x{comp.shape[0]}  "
            f"前景MAE {fg:5.2f} / 背景MAE {bg:5.2f}  {'通过' if good else '异常'}")
    if fg_maes:
        log(f"    结论：{ok} 张通过 / {bad} 张异常；前景 MAE 中位数 {np.median(fg_maes):.2f}")

    # 前景占比分布
    ratios = []
    for r in rows[::max(1, len(rows) // 300)][:300]:
        p = seg_dst / r["img_filename"].replace(".jpg", ".png")
        if p.exists():
            ratios.append((np.asarray(Image.open(p)) > 127).mean())
    if ratios:
        log(f"[5] 前景占比（{len(ratios)} 张抽样）：均值 {np.mean(ratios):.3f}，"
            f"最小 {np.min(ratios):.3f}，最大 {np.max(ratios):.3f}")

    REPORT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
