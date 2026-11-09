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
├── 00_check_env.py        # 环境自检（第 1 周）
├── 01_stats_groups.py     # 四组样本统计（第 7 周）
├── 02_baseline.py         # 零样本基线评测（第 8 周）
├── 03_head_scoring.py     # 头级评分与排序（第 10~11 周）
├── 04_intervene.py        # 定向抑制 / 随机抑制（第 12~13 周）
├── 05_scan_k.py           # 抑制头数扫描（第 14 周）
├── 06_main_results.py     # 测试集主结果（第 15 周）
├── 07_ablation.py         # 补充消融（第 18 周）
└── 08_make_tables.py      # 由 results/csv 生成论文表格（第 16~19 周）
```

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
