# code/ —— 代码工作区

> 这里是唯一写代码的地方。`docs/` 只读，`data/` 只存数据，`paper/` 只写论文。

## 目录职责

| 路径 | 放什么 | 不放什么 |
|---|---|---|
| `configs/` | `base.yaml` + 每个实验一个 `exp_*.yaml` | 硬编码的参数、路径 |
| `src/data/` | Dataset、四组统计、数据校验 | 模型代码 |
| `src/models/` | CLIP 加载、hook 管理、头输出读写 | 训练循环（本课题不训练） |
| `src/scoring/` | 文本分解、头级评分与排序 | 抑制逻辑 |
| `src/intervene/` | 定向抑制、随机抑制 | 评分逻辑 |
| `src/eval/` | 指标计算、分组统计、结果导出 | 画图（画图放 scripts） |
| `scripts/` | 可执行入口，按编号排序 | 被 import 的库代码 |
| `notebooks/` | 探索性分析、临时可视化 | 论文要用的正式结果 |
| `results/logs/` | 每次运行的日志（不进 git） | 手工整理的结论 |
| `results/csv/` | ★ 论文所有数字的唯一来源（进 git） | 大文件 |
| `results/figures/` | 图（300dpi png + pdf）（不进 git） | — |
| `tests/` | 简单自检脚本 | 完整单测体系 |

## 脚本编号约定

```
scripts/
├── 00_check_env.py        # 环境自检（W1）
├── 01_stats_groups.py     # 四组样本统计（W2）
├── 02_make_masks.py       # 由 CUB segmentation 生成前景掩码（W5）
├── 03_make_swaps.py       # 同前景换景样本（两方向，W5）
├── 04_baseline.py         # 零样本基线 + 换景分数 + 背景识别基线（W4–W5）
├── 05_head_scoring.py     # LTC 评分 + 水面/陆地双向选头 + LTC 合并集合（W7–W9）
├── 06_intervene.py        # 单独/并集/LTC/随机抑制（W10）
├── 07_scan_k.py           # 验证集选 k 与方案（W10）
├── 08_main_results.py     # 测试集 6 组主实验 + 同 k 对比（W11）
├── 09_background_probe.py # 背景识别三口径复评（W12）
└── 10_make_tables.py      # 由 results/csv 生成论文表格（W14–W18）
```

> 编号是规划；当前已存在 `00_check_env.py`、`01_stats_groups.py`、`02_make_masks.py`。
> 新增脚本按上表编号，避免与已有文件冲突。

## 三条硬规矩

1. **数字可溯源**：论文里每个数字 → `results/csv/xxx.csv` 的某一行 → 某条命令 → 某个 `run_id` + 日志。这条链不能断。
2. **配置驱动**：跑实验只改 `configs/*.yaml`，不改代码；同一实验必须能用一行命令重现。
3. **种子与命名**：所有随机种子从 `configs` 读；结果文件名含 `run_id`（如 `k10_zero_seed42`），
   禁止 `final`、`new`、`test2`、`最终版` 这类命名（三个月后你自己都分不清）。

## 起步

```bash
# 1) 激活环境
conda activate clipbg
# 2) 自检
python scripts/00_check_env.py
# 3) 统计四组（第 7 周）
python scripts/01_stats_groups.py --config configs/base.yaml
```

依赖见 `requirements.txt`；环境搭建细节见 `../docs/04_软件与环境配置.docx`。
