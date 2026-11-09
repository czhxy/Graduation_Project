# data/ —— 数据工作区（不进 git）

> 这里只放数据与权重，不放代码、不放结果。整个目录已被 `.gitignore` 排除。

## 目录约定

```
data/
├── raw/
│   └── waterbirds/          # ★ 原始数据集，只读，不改结构
│       ├── images/          # 或官方包内实际结构
│       ├── metadata.csv     # 图像 → 类别 / 背景 / split 的标签表
│       └── segmentations/   # 分割掩码（可选，判断背景区域时要用）
├── weights/                 # CLIP ViT-B/16 权重缓存
└── cache/                   # HF / open_clip 下载缓存（可删，删了重下）
```

`code/configs/base.yaml` 里的 `data_root` 指向 `data/raw/waterbirds`。

## 校验清单（下载完立刻做）

- [ ] 记录官方包名、下载日期、文件大小、MD5（写进 `code/results/csv/data_manifest.csv`）
- [ ] 统计各 split 的图像数，与官方 README 声明的数量一致
- [ ] `metadata.csv` 能按 `split` 分组，且每条记录都能找到对应图像文件（无缺失、无多余）
- [ ] 四组样本数由 `scripts/01_stats_groups.py` 输出，**不要手工数**
- [ ] 三个 split 的类别/背景分布打印出来看一眼（多数是不是压倒性？）

## 坑

- **不要**把数据放进 `code/` 或 `paper/`，否则 git、备份、打包全乱。
- **不要**手工改名或重排目录结构，官方脚本与公开代码默认按原结构读。
- 原始数据**只读**，任何清洗结果写入 `data/processed/`（若将来需要）。
- 别把整个数据集往 OneDrive 同步——几 GB 会把同步搞崩，数据用移动硬盘或本地盘备份。

## 磁盘预算

| 项 | 约 |
|---|---|
| Waterbirds 图像 + 掩码 | 1~2 GB |
| CLIP ViT-B/16 权重（两种格式各一份） | 0.6~1.2 GB |
| conda 环境 | 6~8 GB |
| 结果与图表 | ~1 GB |
| **合计预留** | **15 GB** |
