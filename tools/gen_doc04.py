# -*- coding: utf-8 -*-
"""gen_doc04.py —— 生成《04_软件与环境配置.docx》

严格复用 docx_kit 的排版函数；周次口径来自 plan_spec。
输出：<项目根>/docs/04_软件与环境配置.docx（路径由 __file__ 推导，不写死盘符）

2026-11-24 修订：按实测环境（Anaconda3 2026.07 / Python 3.12 / torch 2.7.0+cu126 /
驱动 621.24 / 数据落项目内 data/）与新版 27 周任务书（两条捷径、换景、并集抑制）重写事实。
"""
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))
import docx_kit as K          # noqa: E402
import plan_spec as P         # noqa: E402

# 代码块排版收紧：去掉空行（每行都占版面高度），保留段落注释保证可读
_orig_code_block = K.code_block


def _compact_code_block(document, text, size=8.5):
    return _orig_code_block(document, text.replace("\n\n", "\n"), size=size)


K.code_block = _compact_code_block

OUT = ROOT / "docs" / "04_软件与环境配置.docx"
DOC_NAME = "04 · 软件与环境配置"

# ===================================================================== 代码块
CODE_CONDA_RC = r'''
# C:\Users\<用户名>\.condarc（本机还没有这个文件，需要新建）：conda 走清华镜像
channels:
  - defaults
show_channel_urls: true
default_channels:
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r
custom_channels:
  conda-forge: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
'''

CODE_INSTALL = r'''
# 0) 全程在开始菜单的「Anaconda Prompt」里操作：conda 不在 PATH，
#    普通 PowerShell / cmd 里敲 conda 一定报「不是内部或外部命令」。
#    本机已有 Anaconda3 2026.07（F:\anaconda，conda 26.5.3），S02 装 Miniconda 整步跳过。

# 1) 建环境（Python 3.12）并激活；提示符前应出现 (clipbg)
conda create -n clipbg python=3.12 -y
conda activate clipbg
python -c "import sys; print(sys.executable)"   # 期望 F:\anaconda\envs\clipbg\python.exe
python -V                                        # 期望 Python 3.12.x

# 2) pip 换清华源，然后装 PyTorch —— 必须指向 pytorch 官方 cu126 源，
#    因为 PyPI / 国内镜像上的 Windows 版 torch 是 CPU-only，装完 cuda 不可用
python -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
python -m pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn
python -m pip install torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu126

# 3) 其余依赖（分三批，出错好定位）
#    open_clip_torch / timm / transformers 不写死小版本，以「能加载 ViT-B-16 权重」为准
python -m pip install open_clip_torch timm transformers
python -m pip install numpy==1.26.4 "scipy<2" pandas scikit-learn
python -m pip install Pillow opencv-python tqdm pyyaml matplotlib seaborn

# 4) 最重要的一次检查：是不是 GPU 版（期望 2.7.0+cu126 True 12.6）
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.version.cuda)"

# 5) 留证据：论文附录与日后重装都靠这两个文件
python -m pip freeze > requirements-lock.txt
conda env export --no-builds > environment.yml
'''

CODE_SELFCHECK = r'''
# code/scripts/00_check_env.py
# 用法：python scripts/00_check_env.py              只查环境（第 1 周）
#       python scripts/00_check_env.py --with-clip  加 open_clip 加载与吞吐（第 3 周）
import argparse, platform, time
import torch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-clip", action="store_true")
    ap.add_argument("--batch", type=int, default=8)
    args = ap.parse_args()
    gb = lambda n: f"{n / 1024 ** 3:.2f} GB"

    print("1) Python :", platform.python_version(), "|", platform.platform())
    print("2) PyTorch:", torch.__version__, "| 编译 CUDA:", torch.version.cuda)
    ok = torch.cuda.is_available()
    print("3) CUDA 可用:", ok)
    if not ok:
        print("   [失败] 多半装成了 CPU 版 torch 或驱动异常")
        return
    dev = torch.device("cuda:0")
    p = torch.cuda.get_device_properties(0)
    print("4) GPU:", p.name, "| 显存", gb(p.total_memory),
          f"({p.total_memory / 1024 ** 2:.0f} MiB) | sm_{p.major}{p.minor}")

    a, b = torch.randn(1024, 1024, device=dev), torch.randn(1024, 1024, device=dev)
    torch.cuda.synchronize()
    c = a @ b
    torch.cuda.synchronize()
    print("5) 随机张量前向(1024x1024 matmul): OK | 均值 %.4f" % c.mean().item())

    x, w = torch.randn(4096, 768, device=dev), torch.randn(768, 768, device=dev)
    for _ in range(5):
        x @ w
    torch.cuda.synchronize()
    t0, n = time.time(), 20
    for _ in range(n):
        x @ w
    torch.cuda.synchronize()
    print(f"6) 稠密矩阵乘吞吐: {2 * 4096 * 768 * 768 * n / (time.time() - t0) / 1e12:.1f} TFLOPS")

    if args.with_clip:
        import open_clip
        print("7) open_clip 加载测试（首次会下载约 0.6 GB 权重）")
        model, _, _ = open_clip.create_model_and_transforms("ViT-B-16", pretrained="openai")
        model = model.to(dev).eval()
        for q in model.parameters():
            q.requires_grad_(False)          # 冻结：本课题不做任何训练
        tok = open_clip.get_tokenizer("ViT-B-16")
        xb = torch.randn(args.batch, 3, 224, 224, device=dev)
        with torch.no_grad():
            txt = model.encode_text(tok(["a photo of a waterbird.",
                                         "a photo of a landbird."]).to(dev))
            txt = txt / txt.norm(dim=-1, keepdim=True)
            fe = model.encode_image(xb)
            fe = fe / fe.norm(dim=-1, keepdim=True)
            for _ in range(3):
                model.encode_image(xb)
            torch.cuda.synchronize()
            t0, n = time.time(), 10
            for _ in range(n):
                model.encode_image(xb)
            torch.cuda.synchronize()
        print("   特征形状:", tuple(fe.shape), "| 相似度(随机图):", (fe @ txt.T * 100).tolist())
        print(f"   真实吞吐: {args.batch * n / (time.time() - t0):.1f} img/s"
              f" | 峰值显存 {gb(torch.cuda.max_memory_allocated(0))}")
        print("   [OK] 冻结 + 前向 + 文本相似度 全链路可用")

    print("SELF-CHECK PASS")


if __name__ == "__main__":
    main()
'''

CODE_DATASET_TREE = r'''
<项目根>\data\
├── raw\
│   ├── waterbird_stanford.tar.gz        # 官方 Waterbirds 包（489,698,023 B）
│   ├── CUB_200_2011.tgz                 # CUB 图像+标注包（1,150,585,339 B，不含掩码）
│   ├── segmentations.tgz                # CUB 掩码包（39,272,883 B，独立记录 w9d68-gec53）
│   └── waterbirds\                      # 官方包解压到这里（11,788 张）
│       ├── 001.Black_footed_Albatross\  # …一直到 200.Common_Yellowthroat\
│       ├── ...                          # 共 200 个 CUB 类别目录，里面是 jpg
│       ├── metadata.csv                 # 每张图的 y / place / split（核心表）
│       └── segmentations\               # ★ 已生成：11,788 个前景掩码（鸟=255）
├── processed\
│   └── swaps\                           # ★ 同前景换景样本（03_make_swaps.py，只评测）
├── weights\                             # CLIP ViT-B/16 权重（约 0.6 GB）
└── cache\                               # huggingface / open_clip 下载缓存
'''

CODE_DATASET_STATS = r'''
# code/scripts/01_stats_groups.py（节选：只用标准库，环境刚建好就能跑）
import csv
from collections import Counter
from pathlib import Path

ROOT = Path(r"..\data\raw\waterbirds")                   # 从 code\ 目录运行
SPLIT = {"0": "train", "1": "val", "2": "test"}
COMBOS = [("0", "0"), ("0", "1"), ("1", "0"), ("1", "1")]  # (y, place) 四组
NAME = {("0", "0"): "陆鸟/陆地", ("0", "1"): "陆鸟/水面",
        ("1", "0"): "水鸟/陆地", ("1", "1"): "水鸟/水面"}

rows = list(csv.DictReader(ROOT.joinpath("metadata.csv").open(encoding="utf-8", newline="")))
print(f"metadata.csv: {len(rows)} 行 | 字段 = {list(rows[0].keys())}")
cnt = Counter((r["split"], r["y"], r["place"]) for r in rows)

print("\n{:<6}".format("split") + "".join(f"{NAME[c]:>10}" for c in COMBOS) + f"{'合计':>8}")
for sid, sname in SPLIT.items():
    nums = [cnt[(sid, y, p)] for y, p in COMBOS]
    print(f"{sname:<6}" + "".join(f"{v:>10}" for v in nums) + f"{sum(nums):>8}")
    print(f"   └ 最小组 {min(nums)} 张，占比 {min(nums) / max(sum(nums), 1):.2%}")

# 图像按 CUB 类别分目录，img_filename 形如 "001.Black_footed_Albatross/xxx.jpg"
missing = [r["img_filename"] for r in rows if not (ROOT / r["img_filename"]).exists()]
print(f"\n缺失图像: {len(missing)} 张" + (f" | 例 {missing[:3]}" if missing else " | 校验通过"))
'''

CODE_CLIP_LOAD = r'''
# code/scripts/check_clip.py（临时脚本，跑通后并入 04_baseline.py）
import os
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")   # 权重走 HF 镜像
os.environ.setdefault("HF_HOME", r"..\data\cache\huggingface")

import torch, open_clip
from PIL import Image
DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
CACHE = r"..\data\cache\clip"

# 路径一：在线（首次自动下载，之后读缓存）
model, _, preprocess = open_clip.create_model_and_transforms(
    "ViT-B-16", pretrained="openai", cache_dir=CACHE)
# 路径二：离线（权重已下载成 .bin，直接指文件路径）
# model, _, preprocess = open_clip.create_model_and_transforms(
#     "ViT-B-16", pretrained=r"..\data\weights\open_clip_pytorch_model.bin")

tokenizer = open_clip.get_tokenizer("ViT-B-16")
model = model.to(DEV).eval()
for p in model.parameters():          # 冻结：本课题不做任何训练
    p.requires_grad_(False)

PROMPTS = ["a photo of a waterbird.", "a photo of a landbird."]
IMAGE = r"..\data\raw\waterbirds\001.Black_footed_Albatross\<文件名>.jpg"

with torch.no_grad():
    txt = model.encode_text(tokenizer(PROMPTS).to(DEV))
    txt = txt / txt.norm(dim=-1, keepdim=True)
    feat = model.encode_image(preprocess(Image.open(IMAGE)).unsqueeze(0).to(DEV))
    feat = feat / feat.norm(dim=-1, keepdim=True)
print("相似度(×100):", {p: round(s, 3) for p, s in zip(PROMPTS, (feat @ txt.T * 100)[0].tolist())})
'''

CODE_PROJECT_TREE = r'''
Graduation_Project\           # 项目根：只放 README.md / CLAUDE.md / 进度.md / .gitignore
├── docs\                      # 指引文档 00~07（只读，00~06 由 tools\ 重生成）
├── code\                      # ★ 代码工作区（下面这一整块都在它里面）
│   ├── configs\               # base.yaml（4060 默认）+ exp_*.yaml（extends 覆盖）
│   ├── src\                   # data\ models\ scoring\ intervene\ eval\
│   ├── scripts\               # 00_check_env … 10_make_tables（编号见下表）
│   ├── results\               # logs\（不进 git） csv\（★ 数字唯一来源） figures\
│   ├── notebooks\  tests\
│   ├── requirements.txt
│   └── README.md
├── data\                      # 数据本体，不进 git：raw\waterbirds\ weights\ cache\
├── paper\                     # 论文：00_开题\ 01_文献翻译\ 02_正文\ 03_图表\ 04_答辩\ 05_文献\
├── report\                    # 每周进度汇报（W03_… 按周编号，规范见 report\README.md）
└── .gitignore                 # 排除 data\ results\logs\ results\figures\ ~$* 等
'''

CODE_GIT = r'''
git init
git config user.name "你的名字"
git config user.email "你的邮箱"
# ★ 先建 .gitignore 再 add，否则数据进了历史很难清。内容建议：
#   data/  results/logs/  results/figures/  __pycache__/  *.pyc
#   .ipynb_checkpoints/  *.bin  *.pth  .vscode/
git add .
git commit -m "chore: 初始化项目骨架（代码/数据/结果分离）"
'''

CODE_SEED = r'''
# src/utils/seed.py —— 一个地方管所有随机源
import os, random
import numpy as np, torch


def seed_everything(seed: int = 42) -> None:
    """本课题不做训练，但『随机选头对照』必须可复现。"""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed); np.random.seed(seed)
    torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True   # 做对照实验时开
    torch.backends.cudnn.benchmark = False
'''

# ===================================================================== 文档
doc = K.new_doc(header_text=DOC_NAME)

K.cover(
    doc,
    kicker="毕业设计工程实施文档 · 04 / 06",
    title="软件与环境配置",
    subtitle="Transformer 大模型图像分类中的背景依赖分析与抑制研究",
    metas=[
        ("课题名称", "Transformer 大模型图像分类中的背景依赖分析与抑制研究"),
        ("学院 / 专业", "电子与信息工程学院 · 电子信息工程（本科）"),
        ("研究对象", "冻结的 CLIP ViT-B/16（只做前向推理与注意力头干预，不训练）"),
        ("目标数据", "Waterbirds 二分类（水鸟 / 陆鸟），11,788 图、四组样本统计"),
        ("目标机器", "本机 Windows x64 + RTX 4060 Laptop 8 GB；实验室 RTX 3090 24 GB"),
        ("排期归属", "阶段一（W1–W3），环境搭建集中在 W1"),
        ("文档版本", "v2.0 · 2026-11-24"),
    ],
    footer_note="凡标注「需自行核对」的版本号、文件名与网址，使用前请以官方页面为准；"
                "本文不写未经核实的绝对地址。",
)

# --------------------------------------------------------------- 导读
K.callout(doc, "先看结论", [
    "本机 8 GB 显存够用：全程冻结 CLIP ViT-B/16、只做前向推理与推理期头干预，显存占用约 1.2–2 GB（推导见 1.3）。"
    "真正的短板是 15.6 GB 内存；磁盘不紧张——数据与权重按项目内 data/ 落地（Waterbirds 约 1 GB、权重约 0.6 GB），"
    "C 盘剩约 53 GB、F 盘剩约 87 GB，放代码与 conda 环境（在 F:\\anaconda\\envs）都够。"
    "本机已装 Anaconda3 2026.07，不必再装 Miniconda，直接用开始菜单的「Anaconda Prompt」；"
    "F 盘留作 pip/HF 缓存与备份的备选。本文只管「环境能不能跑、跑得对不对」，"
    "命令按「复制粘贴就能用」写，并说明每一步为什么；方案、实验、文献、写作、答辩见 01–06 其余文档。",
], kind="ok")

# --------------------------------------------------------------- 一、硬件
K.h1(doc, "一、硬件方案：两套机器，一套代码")
K.p(doc, "本课题的实际需求是：加载约 1.5 亿参数的双塔模型、抓中间层激活、修改注意力头输出。"
         "这三件事都在推理阶段完成、不涉及反向传播，算力需求比「训练大模型」低一到两个数量级。")

K.h2(doc, "1.1 本机家底（实测）")
K.table(doc,
        ["部件", "实测规格", "对本课题的意义"],
        [
            ["GPU", "RTX 4060 Laptop，8188 MiB，驱动 621.24（2026-11-15 实测）",
             "主力运算；8 GB 跑 fp32/fp16 推理都够"],
            ["CPU", "i9-13900H，14 核 20 线程", "图像解码；num_workers 给 4–6"],
            ["内存", "15.6 GB", "比显卡更紧：多进程读图 + 缓存很快吃满"],
            ["磁盘 C", "剩余约 53 GB（2026-11-15 实测）", "放代码与文档；conda 环境不在这里"],
            ["磁盘 F", "剩余约 87 GB（2026-11-15 实测）", "Anaconda 本体与 clipbg 环境、pip/HF 缓存、备份"],
            ["已有 / 缺失", "Windows x64；Anaconda3 2026.07（F:\\anaconda，conda 26.5.3，base Python 3.14.6）；"
                            "系统 Python 3.12.5；git 2.49.0；无 CUDA Toolkit（nvcc 不在 PATH）",
             "conda 不在 PATH，用开始菜单「Anaconda Prompt」；系统 Python 不动（第 3 节）；"
             "CUDA Toolkit 不装（2.2）"],
        ],
        widths=[2.4, 6.8, 6.8], font_size=9, first_col_bold=True, zebra=True)
K.caption(doc, "表 1-1  本机硬件与软件实测清单")
K.p(doc, "两条要记住的边界：① F:\\anaconda\\envs\\pytorch 是另一个学习项目的环境，不要删、不要往里装本项目依赖；"
         "② 本项目环境叫 clipbg，按 3.3 另行新建。base 环境（Python 3.14.6）只当启动器，任何项目包都不装进 base。")

K.h2(doc, "1.2 两套方案的分工")
K.p(doc, "方案 A 本机、方案 B 服务器，不是二选一而是前后接力：调试要反复改代码、随时看报错，远程做效率极低；"
         "流水线一旦稳定，多 seed 重复实验就是纯算力问题。")
K.table(doc,
        ["维度", "方案 A：本机 4060 Laptop（8 GB）", "方案 B：实验室 3090（24 GB）"],
        [
            ["角色", "开发机：写代码、调流水线、看错误样本", "跑量机：k 选择 / 同 k 主实验、多 seed 重复"],
            ["优势", "随时可用、改一行立刻能试", "显存 3 倍、全量实验快 3–4 倍"],
            ["限制", "显存 8 GB、内存 15.6 GB，不适合长跑", "要 SSH、排队、环境迁移、数据同步"],
            ["batch", "fp16 64（保守 32）；fp32 32；调试先 8", "fp16 256（保守 128）；fp32 128"],
            ["承担", "基线单次评测、k 选择冒烟、换景样本合成与目检、可视化",
             "k 选择全档；并集 / 单独 / LTC / 随机四条抑制链路的重复实验与最终数字"],
            ["耗时", "测试集一次评测 40–70 秒（第 8 节）", "同一次 10–25 秒"],
        ],
        widths=[2.0, 7.0, 7.0], font_size=9, first_col_bold=True)
K.caption(doc, "表 1-2  两套算力方案对比（batch 与耗时为量级建议，以实测标定为准；★ 结论：A 拉通、B 加速）")

K.h2(doc, "1.3 为什么 8 GB 显存就够：一笔一笔算")
K.rich(doc, [
    ("（1）权重。", {"bold": True}),
    ("ViT-B/16 输入 224×224、patch 16×16 → 196 token + CLS 共 197，宽 768，12 层 12 头、每头 64 维。"
     "单层约 7.1 M 参数（注意力 768×2304≈1.77 M、投影 0.59 M、MLP 768→3072→768≈4.72 M），12 层约 85 M；"
     "视觉塔 86 M，fp32 即 86 M×4 B≈0.34 GB，文本塔 63 M≈0.25 GB。", {}),
])
K.rich(doc, [
    ("（2）激活。", {"bold": True}),
    ("单样本单层三块：隐状态 197×768×4 B≈0.58 MB、注意力矩阵 12×197×197×4 B≈1.86 MB、"
     "MLP 中间 197×3072×4 B≈2.42 MB，峰值 3–5 MB/样本。batch=32 约 0.1–0.16 GB，batch=128 约 0.4–0.6 GB。", {}),
])
K.rich(doc, [
    ("（3）固定开销。", {"bold": True}),
    ("CUDA context、cuDNN 工作区与显存碎片约 0.5–0.8 GB。三项合计 batch=32 约 1.2–1.6 GB、"
     "batch=128 约 1.5–2.0 GB，8 GB 有 4–5 倍余量。", {}),
])
K.callout(doc, "抓激活与做干预的四条纪律（W1 就养成）", [
    "① 只抓需要的层：12 层全存 32 个样本仅 0.22 GB，但存成全库就是几十 GB 文件。"
    "② 抓到就 .detach().cpu()：留在 GPU 上是「越跑越慢最后 OOM」最常见的原因。"
    "③ forward hook 的返回值会替换该层输出——这是修改注意力头的入口，且在 torch.no_grad() 下仍生效，"
    "所以「冻结 + 干预」不需要反向传播。"
    "④ 干预本身几乎不占显存：主操作是 mean ablation（把选中头状态换成该数据集上的均值），"
    "144 个头全存也就 144×768×4 B≈0.4 MB；真正吃显存的是 batch 与激活，不是干预。",
], kind="info")

K.h2(doc, "1.4 本地开发 → 服务器跑全量：代码一行不改")
K.p(doc, "前提守住三条：① 路径全从 config 读，代码里不出现 C:\\ 或 /home/，统一 pathlib；② 设备用 "
         "torch.device(\"cuda\" if torch.cuda.is_available() else \"cpu\") 自动判断；③ 结果按 run_id 落盘。"
         "这样迁移只改 4 个值：batch_size（32→128）、num_workers（4→8）、"
         "data_root（data/raw/waterbirds → /data/waterbirds）、cache_dir（data/cache → /data/cache）。")
K.p(doc, "迁移五步：本机 commit 推送 → 服务器 clone 并按第 3 节重建环境 → 改 server3090.yaml → 服务器上先跑 "
         "00_check_env.py（不能省，两台机器环境不一定一样）→ nohup / tmux 起批处理，日志写进 results/logs。")

# --------------------------------------------------------------- 二、软件栈
K.h1(doc, "二、软件栈：把版本钉死")
K.p(doc, "不锁版本时，半年后重装一次 torch 可能已跳两级、numpy 到 2.x，当初跑出主结果的那个脚本直接报错。"
         "原则是「装定住的版本」：① 大版本锁死、小版本给区间；② torch 与 torchvision 整对装（编译期绑定，"
         "配错报 nms 缺失）；③ numpy < 2.0（复现代码多用 1.x 接口，2.x 删了 np.float_ 等，opencv 也容易装不上）。")
K.h2(doc, "2.1 版本锁定表")
K.table(doc,
        ["包 / 组件", "建议版本", "锁定理由", "装错的后果"],
        [
            ["Python", "3.12.x（推荐）",
             "pip 缓存里已有 torch 2.7.0+cu126 的 cp312 wheel（2.58 GB），可命中缓存；该组合已在本机实测通过",
             "改 3.10 则缓存作废，需重下约 2.5 GB"],
            ["conda 环境", "clipbg（Python 3.12）",
             "与 base 3.14.6、系统 Python 3.12.5 隔离；不复用 F:\\anaconda\\envs\\pytorch",
             "污染别人的项目环境，结论不可复现"],
            ["torch", "2.7.0+cu126（已实测）", "驱动 621.24 支持 cu126；轮子自带 CUDA 运行时", "装成 CPU 版 → cuda 不可用"],
            ["torchvision", "0.22.0+cu126（已实测）", "与 torch 2.7.0 严格配对", "报错或 nms 算子缺失"],
            ["open_clip_torch / timm", "以能加载 ViT-B-16 为准（open_clip_torch ≥2.20；timm 1.x）",
             "HF 加载与模型接口稳定；timm 决定 ViT 实现", "缺 ViT-B-16 映射；与 timm 冲突"],
            ["transformers", "以能加载 ViT-B-16 为准（4.x）", "只做交叉验证，不需新特性", "与 torch 版本耦合报错"],
            ["numpy", "1.26.x（<2）", "1.x 最后一档稳定版", "2.x 让老代码 import 崩，opencv 也可能装不上"],
            ["scipy", "1.11–1.14", "Spearman 排序相关（两组头排序稳定性）", "新版要求 numpy≥2，互相打架"],
            ["pandas", "2.0–2.2", "读 metadata.csv、汇总结果 csv", "同上"],
            ["Pillow", "10–11", "读 jpg / 写掩码与换景图", "过旧读不了 jpg"],
            ["opencv-python", "4.x（headless 版亦可）", "掩码形态学处理 + inpaint 给 donor 背景去鸟（换景要用）",
             "与 numpy 2.x 组合容易 import 失败"],
            ["scikit-learn", "1.3–1.6", "统计指标与简单分析（可选）", "新版对 numpy 有硬要求"],
            ["matplotlib / seaborn", "3.7–3.9 / 0.13", "柱状图、k 曲线、144 头热力图", "中文变方框；新旧不兼容"],
            ["tqdm / PyYAML", "4.66+ / 6.0+", "进度条、读写 config", "无"],
            ["jupyter", "1.x（可选）", "交互看错误样本与换景样例", "—"],
        ],
        widths=[2.9, 3.0, 6.3, 3.8], font_size=8.2, first_col_bold=True, zebra=True)
K.caption(doc, "表 2-1  软件栈版本锁定表（torch/torchvision 为已实测组合；其余给区间，以 pip freeze 实际输出为准）")
K.p(doc, "若真踩到坑：torchvision 与 torch 不配 → 整对卸载、按 pytorch.org 官方命令重装；装成 CPU 版 → "
         "见第 3 节；numpy 被别的包升到 2.x → 装 numpy<2 后立刻重新 freeze，把上限写进 requirements。"
         "注意 code/requirements.txt 只是参考清单（里面没列 opencv-python），torch 一律按 3.4 的命令单独装。")

K.h2(doc, "2.2 为什么不需要装 CUDA Toolkit")
K.p(doc, "PyTorch 的 cu126 轮子已内含所需 CUDA 运行时，只要驱动够新就能用；nvcc 只有自己编译 CUDA 算子时才需要，"
         "本课题不做。所以「nvcc 不在 PATH」不是问题，装 Toolkit 反而容易污染环境。本机驱动 621.24（2026-11-15 实测）"
         "足以驱动 cu126 轮子；驱动与 CUDA 版本的对应关系以 NVIDIA 官方兼容性表为准（请自行核对）。")

K.h2(doc, "2.3 为什么跳过 Miniconda：直接用已有的 Anaconda")
K.p(doc, "本机已装 Anaconda3 2026.07（F:\\anaconda，conda 26.5.3，base Python 3.14.6）。"
         "Anaconda 与 Miniconda 只是预装包数量不同，conda 命令与用法完全一样，所以手册 S02「安装 Miniconda」"
         "整步跳过——再装一遍只会多一套 Python 和一份 PATH 冲突风险。")
K.p(doc, "三条纪律：① 一律用开始菜单里的「Anaconda Prompt」（conda 不在 PATH 是刻意为之，普通 PowerShell 里敲 conda "
         "本来就会报错）；② base 环境只当启动器，任何项目包都不装进 base；③ F:\\anaconda\\envs\\pytorch 是另一个"
         "学习项目的环境（Python 3.12 + torch 2.7.0），不要删、不要往里装本项目依赖、也不要拿它当 clipbg 用——"
         "本项目环境按 3.3 新建。")

# --------------------------------------------------------------- 三、安装
K.h1(doc, "三、安装步骤（Windows，按顺序复制粘贴）")
K.p(doc, "命令全部在「Anaconda Prompt」里执行（都是单行，不必关心换行差异）。本机已有 Anaconda3 2026.07、"
         "系统 Python 3.12.5 与 git 2.49.0，缺 CUDA Toolkit：Miniconda 跳过（S02）、系统 Python 保持不动"
         "（混用是事故源头）、git 跳过、Toolkit 不装。")
K.h2(doc, "3.1 确认 Anaconda Prompt 可用（S02：跳过 Miniconda 安装）")
K.num(doc, 1, "开始菜单搜「Anaconda Prompt」并打开（不要用普通 PowerShell / cmd，conda 不在 PATH 里）。")
K.num(doc, 2, "执行 conda --version 应输出 26.5.3；where.exe conda 应指到 F:\\anaconda\\Scripts\\conda.exe。")
K.num(doc, 3, "执行 python -V 若输出 3.14.6，说明还在 base 环境——base 只当启动器，不要往里装包，下一步就新建 clipbg。")
K.p(doc, "报「conda 不是内部或外部命令」是正常现象：说明用的是普通终端，换 Anaconda Prompt 即可。")
K.h2(doc, "3.2 配置镜像、建环境、装依赖（S03–S06）")
K.p(doc, "为什么配镜像：本机 .condarc 目前还不存在（2026-11-15 实测），conda 仍走境外 defaults，"
         "建环境时解析 repodata 会明显变慢。镜像只加速下载，包内容由哈希保证不变。")
K.code_block(doc, CODE_CONDA_RC, size=8.5)
K.p(doc, "为什么用 3.12 而不是 3.10：pip 缓存里已有 torch 2.7.0+cu126 的 cp312 wheel（2.58 GB），用 3.12 时几乎不下载；"
         "并且 Python 3.12.16 + torch 2.7.0+cu126 + torchvision 0.22.0+cu126 这套组合已在本机 RTX 4060 上实测通过"
         "（cuda 可用、00_check_env.py 打到 SELF-CHECK PASS）。若坚持 3.10，代价是缓存作废、重下约 2.5 GB，"
         "而且没有本机实测记录。")
K.code_block(doc, CODE_INSTALL, size=8)
K.p(doc, "关键点：Windows 上 PyPI 与国内镜像是 CPU-only 版 torch，装完 torch.cuda.is_available() 会是 False，"
         "必须从官方 CUDA 索引装 cu126 轮子——「镜像不等于万能」的典型例子。官方源超时就挂代理，或加 "
         "-f https://download.pytorch.org/whl/cu126/torch_stable.html 只从官方源找大文件，别退回镜像装 CPU 版。"
         "第 4 步打印 2.7.0+cu126、True、12.6 就算打通。")
K.h2(doc, "3.3 装完立刻自检（S07）")
K.p(doc, "按第 4 章的 00_check_env.py 跑一遍，末行出现 SELF-CHECK PASS 才算 S06–S07 全部结束。"
         "把输出重定向存进 code/results/logs/env_<日期>.txt，这是「这台机器当时是什么环境」的唯一证据。")

# --------------------------------------------------------------- 四、自检
K.h1(doc, "四、环境自检：一条命令确认「能用」")
K.p(doc, "环境问题必须在 W1 暴露。等 W5 做换景样本时才发现 torch 是 CPU 版，损失的是整周。"
         "下面这份脚本三十秒跑完，输出存进 results/logs/ 作为两台机器的一致性证据。")
K.h2(doc, "4.1 脚本全文")
K.code_block(doc, CODE_SELFCHECK, size=7.6)
K.p(doc, "W1 建好环境后先跑 python scripts/00_check_env.py；装好 CLIP 权重后再跑 "
         "python scripts/00_check_env.py --with-clip（脚本头注释仍按旧排期写着「第 3 周」，新版 27 周把权重下载"
         "压到了 W1，以本文的 W1 为准）。"
         "存档写法（两个终端都支持）：python scripts\\00_check_env.py > results\\logs\\env_<日期>.txt 2>&1。"
         "末行出现 SELF-CHECK PASS 才算通过。")
K.h2(doc, "4.2 判读与通过判据")
K.bullet(doc, [("第 1–4 项：", {"bold": True}),
               ("Python 显示 3.14.6（base）或 3.12.5（系统 Python）→ conda activate 没生效；"
                "PyTorch 编译 CUDA 为 None → 装成 CPU 版（回 3.2 重装）；"
                "CUDA 为 False → 先查 nvidia-smi 与驱动（应为 621.24）；GPU 名/显存不符 → 可能用了核显或远程会话。", {})])
K.bullet(doc, [("第 5–7 项：", {"bold": True}),
               ("随机张量前向报 CUDA error → 驱动与运行时版本不匹配；open_clip 报 HTTP 错误/卡住 → 设 HF_ENDPOINT "
                "或走离线路径。", {})])
K.p(doc, "第 6 项的 TFLOPS 要和同机已测的约 7.4 TFLOPS 比一量级（Python 3.12.16 + torch 2.7.0+cu126，"
         "2026-11-15 实测，与本节脚本第 6 项同口径）：同量级说明 GPU 版真在算；差十倍以上先怀疑装成了 CPU 版。")
K.p(doc, "五条通过判据：① 七项全正常且第 3 项为 True；② 记下 TFLOPS 与真实 img/s，替换第 8 节估算；"
         "③ 两台机器各跑一遍存档；④ 两个锁版本文件已提交；⑤ 用 Dataset + DataLoader 在 GPU 上跑一次 100 张图"
         "真实前向（随机张量只验证算子，不验证数据管线）。")

# --------------------------------------------------------------- 五、数据
K.h1(doc, "五、数据准备：Waterbirds")
K.p(doc, "Waterbirds 由 Sagawa 等在 GroupDRO（ICLR 2020）中提出：图像源自 CUB-200-2011，合成为水鸟/陆鸟两类，"
         "每张图另有背景标注（水面/陆地），样本于是切成 2×2 四组，其中「水鸟+陆地」「陆鸟+水面」极少，"
         "是标准组偏移设定。要特别注意：它**不附带分割掩码**——官方包只有图像与 metadata.csv，"
         "前景掩码得从 CUB-200-2011 的 segmentations 生成（见 5.4）。掩码用来做同前景换景与「只留前景 / 只留背景」"
         "对照，W5–W6 会直接用到。")
K.callout(doc, "数据来源与已经核实的事实", [
    "来源：Waterbirds 随 GroupDRO 论文与 WILDS 数据集系列公开提供，官方包名 "
    "waterbird_complete95_forest2water2.tar.gz，入口见论文作者主页与 WILDS 站点（地址请自行核对）。",
    "本机已核实（2026-11-24）：包大小 489,698,023 B，sha256 "
    "56c51b77f7d17283ac97003d973e9107e8af9ceebffcb0c8be14d024f846f951；解压到 data/raw/waterbirds/ 后 "
    "metadata.csv 共 11,788 行、引用 11,788 张图、缺失 0 张；包内**没有 segmentations/**。",
    "底线：别从网盘拿数据。metadata.csv 被改过（排序、删行）四组统计就对不上，而你后面所有准确率与最差组"
    "结论都建立在这张表上。解压与校验记录见 data/raw/_waterbirds_report.txt 与 code/results/csv/group_stats.csv。",
], kind="warn")
K.h2(doc, "5.1 目录与完整性校验")
K.code_block(doc, CODE_DATASET_TREE, size=8.5)
K.p(doc, "解压后先做四件事，任一项不过就别往下走：① metadata 行数 = 图像数（本机实测 11,788 行 / 11,788 张 / "
         "0 缺失）；② 每个 split 的 2×2 四格都 > 0；③ 无 0 字节文件；④ 掩码数 = 图像数"
         "（本机实测 11,788 个，2026-11-25 已通过；见 5.4）。")
K.p(doc, "目录上还有一层：<项目根>/data/ 的四个子目录各管一件事——raw/ 放原始与解压数据，"
         "processed/ 放换景样本等派生产物，weights/ 放 CLIP 权重，cache/ 放 HF 与 open_clip 的下载缓存。"
         "实际路径以 code/configs/base.yaml 的 paths 段为准（换景样本目录由 swaps_dir 配置），代码里一律读配置、不写死盘符。")
K.h2(doc, "5.2 四组统计脚本（可直接运行）")
K.p(doc, "只用标准库，环境刚建好就能跑。输出 train/val/test 三张 2×2 交叉表、每行合计、最小组占比与"
         "缺失图像数；数字填进 5.3 的表，就是 02 号文档「四组样本统计表」的口径。")
K.code_block(doc, CODE_DATASET_STATS, size=7.8)
K.h2(doc, "5.3 结果填写")
K.p(doc, "把脚本输出的三行数字填成 2×2 交叉表（train/val/test 各一行，四组各一格 + 合计一列），即 02 号文档"
         "「四组样本统计表」的口径。本机已跑过一次，四组数已是实测值（见 code/results/csv/group_stats.csv）；"
         "正式写进 02 文档前再复算一遍，因为口径一错（把 place 数值当第三类、或 val/test 弄反），"
         "最差组准确率会虚高且单次运行看不出来。")
K.h2(doc, "5.4 掩码的获取与生成（已解决）")
K.p(doc, "Waterbirds 官方包只有 200 个 CUB 类别目录与 metadata.csv，**没有 segmentations/**；"
         "而换景合成（03_make_swaps.py）与「去前景背景图」都依赖逐像素前景掩码。"
         "注意 CUB 官方也把掩码单独发布：图像包（记录 65de6-vp158）不含掩码，"
         "掩码在**独立记录 w9d68-gec53** 的 segmentations.tgz 里，这是最容易踩的坑。")
K.p(doc, "做法：CUB 掩码与 Waterbirds 合成图同尺寸、同位置（官方 generate_waterbirds.py 的做法是 "
         "img_black = CUB 图 × CUB 掩码，再叠加背景），所以把 CUB 掩码按 metadata.csv 的 img_filename "
         "复制成 data/raw/waterbirds/segmentations/<同名>.png 即可，不需要几何配准。"
         "code/scripts/02_make_masks.py 就是做这件事；因合成图以 JPEG 保存，校验改用容差判据"
         "（前景 MAE 远小于背景 MAE），20 张抽样全部通过。")
K.p(doc, "当前状态（2026-11-25）：CUB_200_2011.tgz（1,150,585,339 B）与 segmentations.tgz（39,272,883 B）"
         "均已下载并校验；已生成 11,788 个掩码、缺失 0；覆盖率中位数约 0.13。"
         "备选方案（GrabCut / inpaint / 向导师要）不再需要，保留作记录。"
         "换景时仍须保证掩码覆盖率落在 5%~60%，且换景后前景像素不变。")
K.callout(doc, "别把「Waterbirds 自带掩码」这句话当真", [
    "网上不少教程写「Waterbirds 自带 segmentations」，那是把 CUB 的掩码包记混了。官方 Waterbirds 发布只有"
    "图像 + metadata.csv；用之前先 ls 一遍目录，别等到 W5 做换景时才发现掩码不存在。",
], kind="warn")

# --------------------------------------------------------------- 六、权重
K.h1(doc, "六、模型权重：CLIP ViT-B/16 的两条加载路径")
K.p(doc, "用 OpenAI 的 CLIP ViT-B/16，通过 open_clip 加载：create_model_and_transforms(\"ViT-B-16\", "
         "pretrained=\"openai\")。图像塔 86 M + 文本塔 63 M ≈ 149 M 参数，fp32 约 0.6 GB。"
         "主线选 open_clip 而非 transformers，是因为它模块层级清楚、抓激活与替换头输出更直接；"
         "transformers 留作交叉验证。权重当前**尚未下载**，落盘位置是 data/weights/（或让它下进 data/cache/）。")
K.table(doc,
        ["路径", "适用场景", "做法", "注意"],
        [
            ["一：在线", "首次跑、有网", "pretrained=\"openai\" 并指定 cache_dir；首次下载、之后走缓存",
             "约 0.6 GB，国内可能慢；设 HF_ENDPOINT 镜像"],
            ["二：离线", "服务器无外网或反复重装", "本机下好 .bin 拷到 data/weights/，pretrained 直接指文件路径",
             "文件名与缓存布局随版本变（请自行核对），核对大小与 MD5"],
        ],
        widths=[2.4, 3.8, 6.0, 4.0], font_size=8.5, first_col_bold=True, zebra=True)
K.caption(doc, "表 6-1  CLIP 权重的两条加载路径")
K.p(doc, "open_clip 的下载走 huggingface_hub，设两个环境变量就够、不需要配代理：HF_ENDPOINT 指国内镜像"
         "（hf-mirror.com 是第三方社区镜像，可用性随时间变化，请自行核对），HF_HOME 把缓存放在项目内 "
         "data/cache/huggingface，别写到 C 盘用户目录。把脚本里的 IMAGE 换成 data/raw/waterbirds/ 下任意一张图；"
         "W1 的验收标准就是打印出两个类别的相似度分数且大小关系合理。若报 unexpected keyword argument，"
         "去掉 cache_dir、改用 HF_HOME。")
K.code_block(doc, CODE_CLIP_LOAD, size=7.8)
K.h2(doc, "6.1 冻结模型的三条纪律")
K.p(doc, "① model.eval() 关 dropout、固定 BN；② p.requires_grad_(False) 彻底关梯度（留着会为每次前向建计算图，"
         "显存翻倍）；③ torch.no_grad() 包住前向——hook 在 no_grad 下仍能改输出，这正是干预模块能工作的原因。"
         "另有纪律：权重必须跨机器一致，把大小与 MD5 写进 results/logs/ 存档。")

# --------------------------------------------------------------- 七、仓库
K.h1(doc, "七、参考代码仓库与检索方式")
K.p(doc, "原则：论文为主、代码为辅；先原样跑通 demo 再改；不直接复制进自己仓库（先看 LICENSE，论文注明来源）。"
         "检索三个动作：① 用「论文标题 + 年份」搜，优先看论文首页脚注与作者主页；② GitHub 搜作者名 + 关键词，"
         "非作者本人维护的要注明「非官方实现」；③ 确实没有代码，就如实写「作者未公开代码，本文依据论文第 X 节"
         "公式复现」并交代差异——这句话不扣分，编造假链接才扣分。")
K.table(doc,
        ["名称", "在本课题中的用途", "获取方式", "确定性"],
        [
            ["open_clip", "加载 ViT-B/16、抓中间激活、替换注意力头输出（唯一模型依赖）",
             "pip install open_clip_torch；github.com/mlfoundations/open_clip", "地址确定"],
            ["openai/CLIP", "对照预处理与 prompt 写法；openai 权重来源", "github.com/openai/CLIP（只读代码）", "地址确定"],
            ["TextSpan", "方法论直接来源：按文本方向把图像表示分解到各组件",
             "论文《Interpreting CLIP's Image Representation via Text-Based Decomposition》；"
             "项目页在论文首页脚注，官方代码状态请自行核对", "需自行核对"],
            ["LTC", "直接对标方法：头级评分（Logit Lens / direct effect）+ 选头 + mean ablation 抑制；"
                     "本文要在相同干预头数 k 下与并集方案对比",
             "论文《Locate then Correct: Debiasing Attention Heads in CLIP》；是否开源请自行核对，"
             "未开源则按论文公式复现", "需自行核对"],
            ["GroupDRO / Waterbirds", "数据定义、四组划分、worst-group accuracy 口径",
             "检索 Sagawa GroupDRO（ICLR 2020）作者主页；数据见 WILDS 站点（地址请自行核对）", "需自行核对"],
        ],
        widths=[2.8, 5.0, 5.6, 2.6], font_size=8.5, first_col_bold=True, zebra=True)
K.caption(doc, "表 7-1  参考代码仓库（「需自行核对」= 本文不写死未核实地址，用标题检索确认）")

# --------------------------------------------------------------- 八、预算
K.h1(doc, "八、显存与耗时预算")
K.p(doc, "把 1.3 的推导落成可查的表，用途是「判断够不够、排期留多少余量」，正式数字用自检脚本实测值替换。")
K.h2(doc, "8.1 显存预算")
K.table(doc,
        ["项目", "估算公式", "batch = 32", "batch = 128"],
        [
            ["视觉塔权重（fp32）", "86 M × 4 B", "0.34 GB", "0.34 GB"],
            ["文本塔权重（fp32）", "63 M × 4 B", "0.25 GB", "0.25 GB"],
            ["输入激活", "batch × (3–5 MB/样本)", "0.10–0.16 GB", "0.4–0.6 GB"],
            ["CUDA context + cuDNN", "固定开销", "0.5–0.8 GB", "0.5–0.8 GB"],
            ["合计（估算）/ 8 GB 余量", "——", "1.2–1.6 GB / 4–5 倍", "1.5–2.0 GB / 3–4 倍"],
            ["若 hook 存全部 12 层激活", "batch × 12 × 0.58 MB", "+0.22 GB", "+0.9 GB"],
        ],
        widths=[4.4, 5.2, 3.3, 3.3], font_size=9, first_col_bold=True, zebra=True)
K.caption(doc, "表 8-1  显存预算（ViT-B/16 @224，fp32；fp16 权重减半、激活约减半）")
K.p(doc, "结论：8 GB 跑推理绰绰有余，甚至可同进程留两份模型做「抑制前/后」对比。本机短板是内存 15.6 GB："
         "DataLoader 每个 worker 都有进程开销，num_workers=6 时读图 + 解码缓存很容易吃掉 6–8 GB，"
         "故本机给 4、服务器给 8–12。干预侧不必担心显存：主操作 mean ablation 每个头只多一个 768 维均值向量"
         "（144 头合计约 0.4 MB），zero ablation 更是零额外开销；只有补充消融里存全量激活时才按表里最后一行估。")
K.h2(doc, "8.2 耗时预算")
K.p(doc, "估法：ViT-B/16 @224 单图前向约 17.6 GFLOPs（常用口径，随实现浮动）。本机实测的 fp32 稠密矩阵乘约 "
         "7.4 TFLOPS（与 00_check_env.py 第 6 项同口径），fp16 / Tensor Core 路径通常更快；"
         "真实图像吞吐还要扣 IO、batch 与 kernel 启动开销。下表是排期用量级，不是承诺值，正式数字以实测为准。")
K.table(doc,
        ["场景", "规模", "4060 估算", "3090 估算", "说明"],
        [
            ["验证集一次评测", "约 1.2 千张", "10–20 s", "3–6 s", "W4 基线、W10 选 k 都会反复用到"],
            ["测试集一次评测", "约 5.8 千张", "40–70 s", "10–25 s", "主结果每个数字都要它；只评一次"],
            ["k 选择（8 档，验证集）", "约 1 万张", "1.5–3 min", "30–60 s", "W10，六组共用同一个 k"],
            ["换景合成 / 评测", "每方向数百到数千张", "合成：CPU 为主，N 张约几分钟", "同量级（合成不吃 GPU）",
             "W5 合成、W12 复评；以实测为准"],
            ["144 头评分（含文本投影）", "2–3 遍全量前向", "5–10 min", "1.5–3 min", "W7–W9"],
            ["重复实验（6 组 × ≥3 seed）", "约 18–54 次评测", "30–90 min", "10–25 min", "W13；随机对照 ≥3 seed"],
        ],
        widths=[4.2, 3.4, 2.6, 2.6, 3.4], font_size=8.5, first_col_bold=True, zebra=True)
K.caption(doc, "表 8-2  耗时预算（量级估算，用于排期；正式数据以 00_check_env.py 的吞吐与 bench 实测为准）")
K.p(doc, "★ 排期结论：全部实验在本机 4060 上都能跑完，最重的一天也就是「晚上挂两小时」；服务器的意义是"
         "「多 seed 并行、当天出结果」，不是「没有它就跑不了」——W1 先打通本机，别为等服务器卡住进度。"
         "三条降耗手段：文本 embedding 只算一次并缓存；固定 batch 跑通全程（频繁改会让 cuDNN 反复选算法）；"
         "评测与绘图分离（评测只落盘 csv，改图样式不用重跑模型）。")

# --------------------------------------------------------------- 九、目录
K.h1(doc, "九、目录结构：代码 / 数据 / 结果 / 论文四分离")
K.p(doc, "做到第 18 周最容易出的问题不是模型不 work，而是「找不到当时跑出这个数的脚本」。四分离的目的很直接："
         "任何一张图、任何一个数字都能反查到生成它的代码与配置。")
K.code_block(doc, CODE_PROJECT_TREE, size=8.5)
K.p(doc, "code/scripts/ 的编号规划如下（与 code/README.md 一致）。**编号是规划，实际以 code/scripts 目录为准**："
         "目前真实存在的只有 00_check_env.py、01_stats_groups.py、02_make_masks.py，其余按周次逐步补齐——"
         "别以为编号写了脚本就有。")
K.table(doc,
        ["编号", "脚本", "职责", "周次"],
        [
            ["00", "00_check_env.py", "环境自检：torch / CUDA / GPU / 吞吐", "W1"],
            ["01", "01_stats_groups.py", "四组样本统计 + 缺失图校验", "W2"],
            ["02", "02_make_masks.py", "从 CUB segmentation 生成前景掩码（含逐像素校验）", "W5"],
            ["03", "03_make_swaps.py", "同前景换景样本（水→陆、陆→水两方向 + 质量检查）", "W5"],
            ["04", "04_baseline.py", "零样本基线 + 换景分数 + 背景识别基线", "W4–W5"],
            ["05", "05_head_scoring.py", "LTC 评分 + 水面/陆地双向选头 + LTC 合并集合", "W7–W9"],
            ["06", "06_intervene.py", "单独 / 并集 / LTC / 随机四条抑制链路", "W10"],
            ["07", "07_scan_k.py", "验证集选 k 与方案（六组共用同一个 k）", "W10"],
            ["08", "08_main_results.py", "测试集六组主实验 + 同头数对比", "W11–W14"],
            ["09", "09_background_probe.py", "背景识别三口径复评", "W12"],
            ["10", "10_make_tables.py", "由 results/csv 生成论文表格", "W14–W18"],
        ],
        widths=[1.4, 4.4, 8.2, 2.2], font_size=8.5, first_col_bold=True, zebra=True)
K.caption(doc, "表 9-1  code/scripts 编号规划（规划口径；实际状态以目录为准，已存在 00 / 01 / 02）")
K.p(doc, "四条规矩：① data/ 不进 Git、不放图片本体，只放来源说明与校验脚本（体积 GB 级、数据集不可再分发）；"
         "② results/logs/ 与 results/figures/ 进 .gitignore，results/csv/ 是论文所有数字的唯一来源、必须进 Git；"
         "③ paper/ 只放论文与图源，docs/ 放 00~07 号文档与翻译稿；④ 任何脚本不许写绝对路径。"
         "磁盘上本项目的数据约 1 GB + 权重约 0.6 GB，都落在项目内 data/，C 盘剩约 53 GB 足够；"
         "conda 环境在 F 盘（F:\\anaconda\\envs，8–12 GB），F 盘剩约 87 GB，可再放 pip/HF 缓存与备份。"
         "C 盘实在紧，就把 pip 缓存清掉（pip cache purge），或把 cache_dir 指到 F 盘。")

# --------------------------------------------------------------- 十、Git
K.h1(doc, "十、Git 与实验记录规范")
K.p(doc, "可复现性有两半：环境（第 2、3 节）和记录（本节）。Git 管代码版本，实验记录表管「哪个数字是哪次运行"
         "出来的」，缺一不可。一条 commit 只做一件事，格式 type(scope): 一句话，type 只用五种：chore（环境）、"
         "feat（新功能）、fix（修 bug）、exp（实验设置）、docs（文档）。跑出主结果那次的 commit 号要抄进"
         "实验记录表——这是「数字能反查到代码」的唯一保证。")
K.code_block(doc, CODE_GIT, size=8.5)
K.p(doc, "分支策略：main 永远保持「能跑出当前论文数字」；新想法开 exp/<日期>-<主题> 分支，跑通再合回；"
         "答辩前一晚不做任何合并。本课题不做训练，但「随机选头对照」必须可复现，所以随机源统一入口：")
K.code_block(doc, CODE_SEED, size=8.5)
K.h2(doc, "10.1 实验记录表（每次运行一行）")
K.table(doc,
        ["字段", "含义", "示例 / 填法"],
        [
            ["run_id", "日期_实验类型_参数_方式_种子", "20270112_k10_mean_union_seed42"],
            ["date / git_commit", "日期 + 当时 commit 前 7 位", "2027-01-12 / a3f9c21"],
            ["seed / setting / k / op", "随机种子 / 原模型·水面·陆地·并集·LTC·随机 / 抑制头数 / 干预方式",
             "42 / union / 10 / mean_ablation"],
            ["overall / worst", "总体与最差组准确率", "实跑后填，不预填"],
            ["swap / bg_acc", "两方向换景分数变化 + 背景识别三口径准确率", "实跑后填"],
            ["batch / device / sec", "batch、设备、本次耗时与显存峰值", "32 / RTX4060L / 实跑后填"],
        ],
        widths=[3.6, 7.0, 5.2], font_size=8.5, first_col_bold=True, zebra=True)
K.caption(doc, "表 10-1  实验记录表字段（一行 = 一次运行，禁止把多次运行合并成一行；数字一律实跑后填）")
K.p(doc, "run_id 全部小写、下划线分隔；禁止出现 final、new、test2、最终版 这类名字——三个月后你分不清哪个是哪个。")

# --------------------------------------------------------------- 十一、排查
K.h1(doc, "十一、常见问题排查表")
K.p(doc, "遇到问题三个动作：① 读完整报错，尤其最后三行；② 缩到最小可复现例子（去掉数据、只留十行）；"
         "③ 把 python / torch / CUDA / GPU 四项打印出来存档备查。")
K.table(doc,
        ["现象", "最可能的原因", "处理办法"],
        [
            ["torch.cuda.is_available() 为 False", "装了 CPU 版；或驱动异常",
             "看 torch.version.cuda 是否 None；是则按 3.2 从 cu126 源重装；再 nvidia-smi 确认驱动为 621.24"],
            ["CUDA out of memory", "batch 太大；激活未释放；同进程两份模型；别的进程占卡",
             "降 batch 先跑通；激活立即 detach().cpu()；查僵尸 python 进程"],
            ["pip 下载超时", "默认源境外、镜像未配或临时不可用",
             "确认 pip config list 是清华源；torch 必须走官方 cu126 源；加 --retries 5 --timeout 120"],
            ["conda activate 无反应", "在普通终端里敲（conda 不在 PATH）",
             "改用开始菜单的 Anaconda Prompt；不要为此把 conda 加进 PATH"],
            ["Windows 路径报错", "中文/空格路径；反斜杠被当转义", "字符串用 r\"..\\data\\raw\\waterbirds\"；统一 pathlib；数据别放桌面"],
            ["DataLoader 报错或卡住", "num_workers>0 但缺少 main guard 入口保护",
             "入口放进 if __name__ == \"__main__\"；先设 num_workers=0 排错，再升到 4"],
            ["operator torchvision::nms 不存在", "torch 与 torchvision 不配对", "整对卸载重装（见第 2 节）"],
            ["open_clip 加载卡住 / HTTP 错误", "HF 连接超时、镜像未生效", "设 HF_ENDPOINT 与 HF_HOME；或走离线 .bin 路径"],
            ["CUB 包下载失败 / 速度极慢", "官方链接不稳；断点续传文件不完整",
             "换镜像或从 Wayback 找回；确认 .tgz 大小完整再解压；实在拿不到就向导师要现成掩码，或走 GrabCut 备选（5.4）"],
            ["import cv2 失败 / OpenCV inpaint 报错", "opencv-python 与 numpy 2.x 的 ABI 冲突",
             "先装 numpy<2 再重装 opencv-python；仍失败换 opencv-python-headless；最后才考虑用 PIL + scipy 补洞"],
            ["换景图边缘有缝 / 出现彩色描边", "掩码硬切、羽化不足；或 donor 背景没去干净",
             "掩码先膨胀/羽化 1–2 px（configs 里 swap.blend_px）；检查前景像素是否被改；"
             "换景前后做逐像素 diff 定位"],
            ["数据对不上号或每次结果不一样", "解压不全/二手改版；随机对照与 shuffle 未固定种子",
             "官方包重解压 + 01_stats_groups.py 对数；seed_everything 统一入口并写进 run_id"],
        ],
        widths=[4.4, 5.6, 6.0], font_size=8.5, zebra=True)
K.caption(doc, "表 11-1  常见问题排查表（覆盖约 90% 的实际卡点）")
K.p(doc, "关于多卡：本课题用不到多卡（8 GB 单卡足够，3090 也是单卡），不需要学 DistributedDataParallel。"
         "但「batch 与卡数无关」这点常被搞混：换到 3090 只改 batch_size，不改任何模型代码。")

# --------------------------------------------------------------- 十二、周次
K.h1(doc, "十二、阶段一（W1–W3）执行清单（对齐 plan_spec）")
K.p(doc, "环境搭建属阶段一（W1–W3），按 plan_spec 压在 W1 完成，W2–W3 转精读、四组统计与开题。"
         "W1 的任务写得很明确：「新建 clipbg 环境，装 torch cu126 + open_clip，跑 00_check_env.py 到 "
         "SELF-CHECK PASS」；Anaconda 已装好，S02 的 Miniconda 安装跳过。")
_week_criteria = {
    1: ("确认 Anaconda Prompt 可用（S02 跳过）、新建 clipbg、装 torch cu126 与依赖、跑自检；"
        "下载 ViT-B/16 权重并跑通单图零样本推理",
        "conda activate clipbg 后 python -V 为 3.12.x；自检前 6 项正常；--with-clip 打出 [OK]；两个锁版本文件已生成",
        "2、3、4、6 节"),
    2: ("四组样本统计落 csv；ViT/CLIP 张量流与四组划分精读（PyTorch 基础已在预修完成）",
        "group_stats.csv 与 metadata 对数一致；能说清 197 token / 12 层 / 12 头 / 768 维", "5.2、5.3 节"),
    3: ("TextSpan/LTC 精读；写开题报告与技术路线图；完成英文翻译（M1）",
        "开题 + 翻译 + 路线图三件齐备；能画出 LTC 的「评分 → 选头 → mean ablation」流程", "1.3、6.1 节"),
}
_wk_rows = []
for _w, _pid, _theme, _tasks, _deliver in P.WEEKS[:3]:
    _c, _m, _sec = _week_criteria[_w]
    _wk_rows.append([f"第 {_w} 周\n{P.week_dates(_w)}", _c, _m, _sec])
K.table(doc,
        ["周次", "本周环境任务（主题取自 plan_spec）", "完成判据", "本文对应"],
        _wk_rows,
        widths=[2.2, 7.4, 4.6, 2.0], font_size=8.5, first_col_bold=True, zebra=True)
K.caption(doc, "表 12-1  阶段一（W1–W3）环境任务与完成判据（周次取自 plan_spec.WEEKS；环境集中在 W1）")
K.p(doc, "W3 后环境只剩维护。任何一周没按判据通过，宁可推迟一周，也不要带着不确定的环境进入阶段二"
         "——基线一旦建立在不稳定环境上，后面所有对比实验都要重跑。")

# --------------------------------------------------------------- 十三、工具软件
K.h1(doc, "十三、编程之外的配套软件（容易被漏掉的一半）")
K.p(doc, "「需要准备什么软件」不只是 Python 包。任务书要求文献调研、技术路线图、论文排版、答辩演示，"
         "这些都要各自的工具。下表按「什么时候真正用上」排序，不用一次装完——但 W1 至少要把前两项装好。")

K.table(doc,
        ["用途", "推荐软件", "必需性", "什么时候装", "为什么 / 注意"],
        [["代码编辑与调试", "VS Code（＋ Python、Jupyter 扩展）\n或 PyCharm Community", "必需", "W1",
          "要看变量、设断点、跑 notebook；VS Code 还能 Remote-SSH 连实验室服务器，一个工具两用"],
         ["文献管理与笔记", "Zotero（可选 Better BibTeX 插件）", "必需", "W1",
          "19 篇文献的题录、PDF、笔记集中管；写论文时能一键导出 GB/T 7714 格式，省掉手工排版"],
         ["文档写作", "Microsoft Word（用学院模板）", "必需", "W3 前",
          "开题报告就要用；公式用 Word 自带公式编辑器足够，不必上 MathType"],
         ["图表与流程图", "draw.io（网页版即可，免安装）", "必需", "W3 前",
          "画技术路线图、抑制位置示意图；导出矢量 PDF，插进论文不缺清晰度"],
         ["论文排查与备份", "OneDrive / 坚果云 ＋ Git 远端仓库", "必需", "W1",
          "论文和代码每天自动备份一次。硬盘坏一次足以毁掉整个毕设，这是最低成本的保险"],
         ["服务器连接", "VS Code Remote-SSH 或 MobaXterm", "需要 3090 时", "W13 前",
          "跑全量重复实验用 tmux/nohup 挂长任务，断网不中断"],
         ["截图与标注", "Snipaste / 系统自带截图", "推荐", "W6",
          "记录报错现场、给案例图加框标注，写诊断报告时省大量时间"],
         ["思维导图", "XMind", "可选", "W2",
          "梳理「三代研究脉络」「六个环节」这类结构；不是必需，喜欢用再用"],
         ["答辩演示", "PowerPoint 或 WPS", "必需", "W21",
          "PPT 结构见 02 号文档第七章；提前确认答辩教室的 Office 版本，避免字体错位"],
         ["论文查重", "学校指定系统（如知网）", "必需", "W19",
          "学院统一安排，提前问清免费次数与提交格式，别等到截止前一天"]],
        widths=[2.6, 4.4, 1.6, 2.6, 5.0], align="llccl", font_size=8.5, first_col_bold=True)

K.caption(doc, "表 13-1  配套工具软件清单（按使用时间排序；周次对齐 27 周计划）")

K.callout(doc, "三件「不要装」的东西",
          ["**不要装 CUDA Toolkit**：PyTorch 的 cu126 轮子自带运行时，装了反而可能污染 PATH（见 2.2 节）。",
           "**不要再装第二个 Python / 不要再装 Miniconda**：本机已有 Anaconda3 2026.07 与系统 Python 3.12.5，"
           "所有工作都在新建的 clipbg 里做；两套以上 Python 混用是最常见的「明明装了却 import 不到」的原因。",
           "**不要一开始就上 LaTeX**：学院给的是 Word 模板，本科论文用 LaTeX 排版公式的收益抵不上模板适配的成本。"
           "真要转，等论文内容定稿（W20）再考虑。"],
          kind="warn")

K.p(doc, "磁盘预算：Waterbirds 图像约 1 GB、掩码约 0.2 GB（生成后）、CLIP 权重约 0.6~1.2 GB（两种格式各一份就翻倍）、"
         "conda 环境约 6~8 GB（在 F 盘）、实验结果与图表约 1 GB、论文与文献约 1 GB。"
         "这轮实测 C 盘剩约 53 GB、F 盘剩约 87 GB，数据放项目内 data/、环境放 F 盘，两边都有余量；"
         "若日后数据量涨到几十 GB，再把 data_root 或 cache_dir 改到 F 盘即可，代码不用动。")

# --------------------------------------------------------------- 附录
K.h1(doc, "附录 A：本文标注「需自行核对」的条目")
K.p(doc, "规则：不确定的版本号、文件名、网址宁可不写也不编造。下面按类汇总全文的「需自行核对」条目，"
         "核对完把结果写进 docs/ 下的环境说明，论文附录「实验环境」用核对后的版本号而非本文建议区间：")
K.bullet(doc, [("版本号类：", {"bold": True}),
               ("torch/torchvision 配对（2.1、3.2，查 pytorch.org Get Started）；open_clip_torch / timm / "
                "transformers 的小版本（2.1，以能加载 ViT-B-16 为准，pip index versions）；"
                "驱动 621.24 支持的 CUDA 上限（2.2，查 NVIDIA 兼容表）。", {})])
K.bullet(doc, [("地址与数据类：", {"bold": True}),
               ("清华镜像地址（3.2）；Waterbirds 官方包下载页与包名（5，检索 Waterbirds dataset Sagawa GroupDRO "
                "WILDS）；CUB-200-2011 下载入口（5.4）；各 split 精确样本数（5.1、5.3，以 01_stats_groups.py "
                "输出为准）。", {})])
K.bullet(doc, [("第三方与开源状态：", {"bold": True}),
               ("hf-mirror.com 可用性（6）；TextSpan / LTC 的代码地址与开源状态（7，按标题检索论文首页脚注与"
                "作者主页）。", {})])

# --------------------------------------------------------------- 保存
K.save(doc, OUT)

# ===================================================================== 自检
from docx import Document                       # noqa: E402
from docx.oxml.ns import qn                     # noqa: E402
from docx.shared import Pt                      # noqa: E402


def _table_kind(t):
    """按单元格数 + 底纹判定构件类型：code / callout / table。"""
    try:
        cells = t.rows[0].cells
    except IndexError:
        return "other"
    ncell = len(cells)
    fill = None
    tcPr = cells[0]._tc.tcPr
    if tcPr is not None:
        shd = tcPr.find(qn("w:shd"))
        if shd is not None:
            fill = shd.get(qn("w:fill"))
    if ncell == 1 and fill == "F4F4F4":
        return "code"
    if ncell == 1 and fill in ("F2F5F9", "FDF0E6", "EAF4EC"):
        return "callout"
    return "table"


d2 = Document(str(OUT))
kinds = [_table_kind(t) for t in d2.tables]
n_table, n_code = kinds.count("table"), kinds.count("code")
n_callout = kinds.count("callout")

h1_list = []
for para in d2.paragraphs:
    txt = para.text.strip()
    if not txt:
        continue
    for run in para.runs:
        if run.font.size == Pt(17) and run.font.bold:
            h1_list.append(txt)
            break

n_chars = sum(len(pp.text) for pp in d2.paragraphs)
tbl_rows = sum(len(t.rows) for t in d2.tables)
code_lines = sum(len(c.paragraphs) for t, k in zip(d2.tables, kinds) if k == "code"
                 for c in t.rows[0].cells)

print("=" * 62)
print(f"OUT        : {OUT.name}")
print(f"paragraphs : {len(d2.paragraphs)}")
print(f"tables     : {len(d2.tables)} (normal={n_table} code={n_code} callout={n_callout})")
print(f"body chars : {n_chars} | table rows={tbl_rows} | code lines={code_lines}")
print(f"h1 count   : {len(h1_list)}")
print("-" * 62)
for i, h in enumerate(h1_list, 1):
    print(f"  {i:02d}. {h}")
print("=" * 62)
assert n_table >= 6, f"规范表格数不足：{n_table}"
assert n_code >= 3, f"代码块数不足：{n_code}"
assert len(h1_list) >= 11, f"一级标题数不足：{len(h1_list)}"
print("SELF-CHECK PASS: tables / code blocks / h1 all sufficient.")
