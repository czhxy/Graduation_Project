# -*- coding: utf-8 -*-
"""校验 Waterbirds（Stanford 官方包）并统计四组样本数（对应手册 S28 + S29）。

用法（在 code/ 目录下）：
    python scripts/01_stats_groups.py --config configs/base.yaml
    python scripts/01_stats_groups.py            # 不传 config 时用默认路径

产物：
    data/raw/waterbirds/{001.*…200.*, metadata.csv}
    code/results/csv/data_manifest.csv
    code/results/csv/group_stats.csv
报告：data/raw/_waterbirds_report.txt

说明：Stanford 官方包（waterbird_complete95_forest2water2）的 metadata.csv 列为
    img_id, img_filename, y, split, place, place_filename
其中 place=1 表示水面背景、place=0 表示陆地背景（等价于旧文档里的 confounding 列）。
本包**不含分割掩码**，图片按 CUB 类别分目录存放，不是 images/ 平铺结构。
压缩包顶层目录为 waterbird_complete95_forest2water2/。
"""
import argparse
import csv
import hashlib
import re
import shutil
import sys
import tarfile
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "data" / "raw" / "waterbird_stanford.tar.gz"
DEFAULT_DEST = ROOT / "data" / "raw" / "waterbirds"
EXPECTED_SHA = "56c51b77f7d17283ac97003d973e9107e8af9ceebffcb0c8be14d024f846f951"
CSV_DIR = ROOT / "code" / "results" / "csv"
REPORT = ROOT / "data" / "raw" / "_waterbirds_report.txt"

# y=1 水鸟, y=0 陆鸟；place=1 水面, place=0 陆地
ORDER = ["waterbird_on_water", "waterbird_on_land", "landbird_on_land", "landbird_on_water"]
GROUPS = {("1", "1"): "waterbird_on_water", ("1", "0"): "waterbird_on_land",
          ("0", "0"): "landbird_on_land", ("0", "1"): "landbird_on_water"}
SPLIT = {"0": "train", "1": "val", "2": "test"}

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


def dest_from_config(config_path):
    if not config_path:
        return DEFAULT_DEST
    text = Path(config_path).read_text(encoding="utf-8")
    m = re.search(r"data_root:\s*(\S+)", text)
    if not m:
        return DEFAULT_DEST
    p = Path(m.group(1).replace("/", "\\"))
    return (Path(config_path).resolve().parent / p).resolve()


def prepare(dest):
    """校验并解压（只做一次）。"""
    if (dest / "metadata.csv").exists():
        log("[0] 数据已解压，跳过校验与解压")
        return
    if not ARCHIVE.exists():
        log(f"[!] 找不到 {ARCHIVE}，也没有已解压的数据")
        raise SystemExit(1)

    size = ARCHIVE.stat().st_size
    log(f"[1] 压缩包：{ARCHIVE.name}  {size:,} bytes（{size / 1024 / 1024:.1f} MB）")
    digest = sha256(ARCHIVE)
    log(f"[2] SHA256：{digest}")
    log(f"    期望：{EXPECTED_SHA}")
    if digest != EXPECTED_SHA:
        log("    [X] 校验失败，停止（文件可能没下完整）")
        REPORT.write_text("\n".join(lines), encoding="utf-8")
        raise SystemExit(1)
    log("    [OK] 校验通过")

    log("[3] 解压")
    tmp = ROOT / "data" / "raw" / "_extract"
    if tmp.exists():
        shutil.rmtree(tmp)
    with tarfile.open(ARCHIVE, "r:gz") as tf:
        names = tf.getnames()
        log(f"    条目 {len(names)}，顶层 {sorted({n.split('/')[0] for n in names})[:5]} …")
        try:
            tf.extractall(tmp, filter="data")
        except TypeError:
            tf.extractall(tmp)

    meta = next(tmp.rglob("metadata.csv"), None)
    if meta is None:
        log("    [X] 包内没有 metadata.csv")
        REPORT.write_text("\n".join(lines), encoding="utf-8")
        raise SystemExit(1)

    log(f"[4] 移动到 {dest.relative_to(ROOT)}")
    dest.mkdir(parents=True, exist_ok=True)
    for child in dest.iterdir():
        if child.name == ".gitkeep":
            continue
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    for child in meta.parent.iterdir():
        shutil.move(str(child), str(dest / child.name))
    shutil.rmtree(tmp, ignore_errors=True)

    with open(CSV_DIR / "data_manifest.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["包名", "来源", "下载日期", "大小_bytes", "sha256", "解压位置", "说明"])
        w.writerow([ARCHIVE.name,
                    "Stanford 官方包 waterbird_complete95_forest2water2.tar.gz；原地址 nlp.stanford.edu/data/dro/ 本机不可达，经 Wayback Machine 2024-09-20 快照取得",
                    date.today().isoformat(), size, digest, "data/raw/waterbirds",
                    "11,788 图；图片按 CUB 类别分目录；metadata 用 place 列表示背景；不含分割掩码"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    args = ap.parse_args()
    dest = dest_from_config(args.config)

    prepare(dest)

    with open(dest / "metadata.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    cols = list(rows[0].keys())
    bg_col = "place" if "place" in cols else "confounding"
    log("[5] metadata.csv")
    log(f"    列名：{cols}")
    log(f"    背景标签列：{bg_col}（1=水面，0=陆地）")
    log(f"    总行数：{len(rows):,}")

    table = defaultdict(Counter)
    for r in rows:
        table[SPLIT.get(r["split"], r["split"])][GROUPS[(r["y"], r[bg_col])]] += 1

    log("[6] 四组样本数（实测）")
    log("    split      " + "".join(f"{g:>22s}" for g in ORDER) + f"{'合计':>9s}")
    for sp in ("train", "val", "test"):
        log(f"    {sp:10s} " + "".join(f"{table[sp][g]:>22,}" for g in ORDER)
            + f"{sum(table[sp][g] for g in ORDER):>9,}")

    # 图像齐全性：img_filename 形如 "001.xxx/yyy.jpg"
    missing = [r["img_filename"] for r in rows if not (dest / r["img_filename"]).exists()]
    log("[7] 图像齐全性")
    log(f"    metadata 引用 {len(rows):,} 张，缺失 {len(missing)} 张")
    log(f"    分割掩码：{'有' if (dest / 'segmentations').exists() else '无（本包不含）'}")

    CSV_DIR.mkdir(parents=True, exist_ok=True)
    with open(CSV_DIR / "group_stats.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["split"] + ORDER + ["total"])
        for sp in ("train", "val", "test"):
            w.writerow([sp] + [table[sp][g] for g in ORDER] + [sum(table[sp][g] for g in ORDER)])
    log("[8] 已写 code/results/csv/group_stats.csv")

    REPORT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
