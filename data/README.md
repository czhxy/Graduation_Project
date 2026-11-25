# data/ —— 数据工作区（不进 git）

> 这里只放数据与权重，不放代码、不放结果。整个目录已被 `.gitignore` 排除。

## 目录现状（2026-11-25 实测）

```
data/
├── raw/
│   ├── waterbird_stanford.tar.gz   # 官方压缩包，489,698,023 B，sha256 见下
│   ├── CUB_200_2011.tgz            # CUB 图像+标注包，1,150,585,339 B（不含掩码）
│   ├── segmentations.tgz           # CUB 分割掩码包，39,272,883 B（官方独立记录 w9d68-gec53）
│   ├── CUB_200_2011/               # 已解压：segmentations/ 全部 11,788 + images/ 抽样 20 张（供校验）
│   └── waterbirds/                 # ★ 解压后，只读
│       ├── 001.Black_footed_Albatross/ … 200.Common_Yellowthroat/   # 200 个 CUB 类别目录
│       ├── metadata.csv            # 11,788 行：img_id / img_filename / y / split / place / place_filename
│       └── segmentations/          # 11,788 个前景掩码 PNG（鸟=255），由 CUB 掩码按 img_filename 复制
├── weights/                        # CLIP ViT-B/16 权重缓存
├── cache/                          # HF / open_clip 下载缓存（可删，删了重下）
└── processed/
    └── swaps/                      # 规划中：同前景换景样本（两方向），只用于评测
```

`code/configs/base.yaml` 里的 `data_root` 指向 `data/raw/waterbirds`。

## 来源与校验

| 项 | 值 |
|---|---|
| 来源 | **Stanford 官方包** `waterbird_complete95_forest2water2.tar.gz`；原地址 `nlp.stanford.edu/data/dro/` 在本机不可达，经 Wayback Machine 2024-09-20 快照取得 |
| 文件 | `waterbird_stanford.tar.gz`，489,698,023 bytes |
| sha256 | `56c51b77f7d17283ac97003d973e9107e8af9ceebffcb0c8be14d024f846f951` |
| 校验 | 2026-11-24：tar 完整；11,788 张图像 0 缺失；四组数字与 WILDS 镜像版逐个一致 |

> 先前下载的 WILDS 镜像版（HF `pangwei/wilds-waterbirds`）与官方包**内容一致**（同样是 200 个类别目录 + metadata.csv、同样没有掩码），已删除以免重复占 467 MB。

### CUB-200-2011（前景掩码来源）

| 项 | 值 |
|---|---|
| 图像包 | `CUB_200_2011.tgz`，1,150,585,339 B，sha256 `0c685df5597a8b24909f6a7c9db6d11e008733779a671760afef78feb49bf081` |
| 掩码包 | `segmentations.tgz`，39,272,883 B，md5 `4d47ba1228eae64f2fa547c47bc65255`，sha256 `dc77f6cffea0cbe2e41d4201115c8f29a6320ecb04fffd2444f51b8066e4b84f` |
| 来源 | `data.caltech.edu`：图像包为记录 `65de6-vp158`，掩码包为独立记录 `w9d68-gec53` |
| 关键事实 | 记录 `65de6-vp158` 的 `CUB_200_2011.tgz` **不含** `segmentations/`，掩码必须另下 `w9d68-gec53` 的 `segmentations.tgz` |
| 校验 | tar 完整；掩码 11,788 个，与 metadata 一一对应、缺失 0 |

## 字段含义（易错）

- `y`：**1 = 水鸟，0 = 陆鸟**
- `place`：**1 = 水面背景，0 = 陆地背景**（官方包与 WILDS 包这一列同名；旧文档里写的 `confounding` 在本包里不存在）
- `split`：0 = train，1 = val，2 = test
- `img_filename`：相对 `data/raw/waterbirds/` 的路径，形如 `001.xxx/yyy.jpg`

## 四组样本数（2026-11-24 实测，见 `code/results/csv/group_stats.csv`）

| split | waterbird_on_water | waterbird_on_land | landbird_on_land | landbird_on_water | 合计 |
|---|---:|---:|---:|---:|---:|
| train | 1,057 | 56 | 3,498 | 184 | 4,795 |
| val | 133 | 133 | 467 | 466 | 1,199 |
| test | 642 | 642 | 2,255 | 2,255 | 5,794 |

训练集里 95% 的样本「类别—背景」一致（水鸟配水面 95%、陆鸟配陆地 95%），验证/测试集是 50/50 平衡的。**最差组是 train 的 waterbird_on_land（56 张）**。

## 掩码与数据状态（2026-11-25 更新）

- ✅ **前景掩码已解决**：两个 Waterbirds 包都不含 `segmentations/`，但 CUB 官方把掩码单独发布在记录
  `w9d68-gec53`。已下载 `segmentations.tgz` 并用 `code/scripts/02_make_masks.py` 按 `img_filename`
  生成 `data/raw/waterbirds/segmentations/*.png`，共 **11,788 个，缺失 0**。
- 校验口径：合成图与 CUB 原图**同尺寸、同位置**。合成图以 JPEG 保存，前景像素无法逐字节相等；
  改用容差判据——20 张抽样前景 MAE 中位数 **8.53**、背景 MAE 49~100，全部通过；掩码故意平移
  20 px 后前景 MAE 翻倍，证明对齐正确。详见 `data/raw/_mask_report.txt`。
- 掩码覆盖率（300 张抽样）：均值 0.131，最小 0.020，最大 0.483。W5 换景时按 5%~60% 过滤。
- **换景 donor 必须先去鸟**：对侧类别原图 × 掩码 → 鸟区 inpaint 修补 → 只取背景；否则会贴进第二只鸟。
  换景后前景像素必须逐像素不变，≥30 张/方向人工目检。
- 图像按 CUB 类别分目录，**不是** `images/` 平铺结构；读图按 `metadata.csv` 的 `img_filename` 拼路径即可。

## 校验清单（下载完立刻做）

- [x] 记录官方包名、下载日期、文件大小、sha256（已写进 `code/results/csv/data_manifest.csv`）
- [x] 统计各 split 的图像数（train 4,795 / val 1,199 / test 5,794）
- [x] `metadata.csv` 每条记录都能找到对应图像（缺失 0）
- [x] 四组样本数由 `scripts/01_stats_groups.py` 输出，不手工数
- [x] 三个 split 的类别/背景分布已打印核对

## 坑

- **不要**把数据放进 `code/` 或 `paper/`，否则 git、备份、打包全乱。
- **不要**手工改名或重排目录结构；读图一律走 `metadata.csv` 的 `img_filename`。
- 原始数据**只读**，任何清洗结果写入 `data/processed/`（若将来需要）。
- 别把整个数据集往 OneDrive 同步——几 GB 会把同步搞崩。

## 磁盘预算

| 项 | 实际/约 |
|---|---|
| Waterbirds 压缩包 + 解压 | 466 MB + ~1.1 GB |
| CUB 图像包 + 掩码包 + 解压（只解压掩码与 20 张抽样图） | 1.15 GB + 38 MB + ~65 MB |
| 前景掩码 `segmentations/` | 52 MB（11,788 个 PNG） |
| 换景样本 `processed/swaps/` | ~1–2 GB（两方向 × val/test） |
| CLIP ViT-B/16 权重 | 0.35~0.6 GB |
| conda 环境 | 6~8 GB |
| 结果与图表 | ~1 GB |
| **合计预留** | **20 GB** |
