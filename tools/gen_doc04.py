# -*- coding: utf-8 -*-
"""gen_doc04.py —— 生成《04_软件与环境配置.docx》

严格复用 docx_kit 的排版函数；周次口径来自 plan_spec。
输出：<项目根>/docs/04_软件与环境配置.docx（路径由 __file__ 推导，不写死盘符）
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
# C:\Users\<用户名>\.condarc（没有就新建）：conda 走清华镜像
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
# 1) 建环境（Python 3.10）并激活；提示符前应出现 (clipbg)
conda create -n clipbg python=3.10 -y
conda activate clipbg
python -c "import sys; print(sys.executable)"   # 期望 ...\envs\clipbg\python.exe

# 2) pip 换清华源，然后装 PyTorch —— 必须指向 pytorch 官方 cu121 源，
#    因为 PyPI / 国内镜像上的 Windows 版 torch 是 CPU-only，装完 cuda 不可用
python -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
python -m pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn
python -m pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu121

# 3) 其余依赖（分两批，出错好定位）
python -m pip install open_clip_torch timm transformers
python -m pip install numpy==1.26.4 scipy pandas scikit-learn
python -m pip install matplotlib seaborn tqdm pyyaml Pillow jupyter

# 4) 最重要的一次检查：是不是 GPU 版（期望 2.5.1+cu121 True 12.1）
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.version.cuda)"

# 5) 留证据：论文附录与日后重装都靠这两个文件
python -m pip freeze > requirements-lock.txt
conda env export --no-builds > environment.yml
'''

CODE_SELFCHECK = r'''
# scripts/selfcheck.py
# 用法：python scripts/selfcheck.py              只查环境（第 1 周）
#       python scripts/selfcheck.py --with-clip  加 open_clip 加载与吞吐（第 3 周）
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


if __name__ == "__main__":
    main()
'''

CODE_DATASET_TREE = r'''
F:\datasets\waterbirds\
├── metadata.csv                        # 每张图的 y / place / split（核心表）
├── waterbird_complete95_forest2water2\ # 图像（子文件夹里是 jpg）
├── segmentations\                      # 前景/背景掩码（做背景替换对照用）
└── MD5.txt                             # 自己生成的校验值，归档用
'''

CODE_DATASET_STATS = r'''
# scripts/dataset_stats.py —— 只用标准库，环境刚建好就能跑
import csv
from collections import Counter
from pathlib import Path

ROOT = Path(r"F:\datasets\waterbirds")                   # 改成你的数据根目录
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

img_dir = ROOT / "waterbird_complete95_forest2water2"
missing = [r["img_filename"] for r in rows if not (img_dir / r["img_filename"]).exists()]
print(f"\n缺失图像: {len(missing)} 张" + (f" | 例 {missing[:3]}" if missing else " | 校验通过"))
'''

CODE_CLIP_LOAD = r'''
# scripts/check_clip.py —— 两条加载路径任选其一
import os
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")   # 权重走 HF 镜像
os.environ.setdefault("HF_HOME", r"F:\cache\huggingface")

import torch, open_clip
from PIL import Image
DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
CACHE = r"F:\cache\clip"

# 路径一：在线（首次自动下载，之后读缓存）
model, _, preprocess = open_clip.create_model_and_transforms(
    "ViT-B-16", pretrained="openai", cache_dir=CACHE)
# 路径二：离线（权重已下载成 .bin，直接指文件路径）
# model, _, preprocess = open_clip.create_model_and_transforms(
#     "ViT-B-16", pretrained=r"F:\cache\clip\open_clip_pytorch_model.bin")

tokenizer = open_clip.get_tokenizer("ViT-B-16")
model = model.to(DEV).eval()
for p in model.parameters():          # 冻结：本课题不做任何训练
    p.requires_grad_(False)

PROMPTS = ["a photo of a waterbird.", "a photo of a landbird."]
IMAGE = r"F:\datasets\waterbirds\waterbird_complete95_forest2water2\<子目录>\<文件名>.jpg"

with torch.no_grad():
    txt = model.encode_text(tokenizer(PROMPTS).to(DEV))
    txt = txt / txt.norm(dim=-1, keepdim=True)
    feat = model.encode_image(preprocess(Image.open(IMAGE)).unsqueeze(0).to(DEV))
    feat = feat / feat.norm(dim=-1, keepdim=True)
print("相似度(×100):", {p: round(s, 3) for p, s in zip(PROMPTS, (feat @ txt.T * 100)[0].tolist())})
'''

CODE_PROJECT_TREE = r'''
Graduation_Project\           # 项目根：只放 README.md / CLAUDE.md / 进度.md / .gitignore
├── docs\                      # 指引文档（只读，由 tools\ 重生成）
├── code\                      # ★ 代码工作区（下面这一整块都在它里面）
│   ├── configs\               # base.yaml（4060）/ server3090.yaml
│   ├── src\                   # data\ models\ scoring\ intervene\ eval\
│   ├── scripts\               # selfcheck / check_clip / run_* / bench
│   ├── results\               # raw\ (gitignore) tables\ figures\ env\
│   ├── notebooks\  tests\
│   ├── requirements.txt
│   └── README.md
├── data\                      # 数据集与权重本体：raw\waterbirds\ weights\ cache\
├── paper\                     # 论文：00_开题\ 01_文献翻译\ 02_正文\ 03_图表\ 04_答辩\
|
└── .gitignore                 # 已排除 data\ ~$* results\logs\ 等
'''

CODE_GIT = r'''
git init
git config user.name "你的名字"
git config user.email "你的邮箱"
# ★ 先建 .gitignore 再 add，否则数据进了历史很难清。内容建议：
#   data/  results/raw/  results/env/  __pycache__/  *.pyc
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
        ("目标数据", "Waterbirds 二分类（水鸟 / 陆鸟），四组样本统计"),
        ("目标机器", "本机 Windows x64 + RTX 4060 Laptop 8 GB；实验室 RTX 3090 24 GB"),
        ("排期归属", "阶段一（第 1–6 周），环境搭建集中在第 1–3 周完成"),
        ("文档版本", "v1.0 · 2026-11-09"),
    ],
    footer_note="凡标注「需自行核对」的版本号、文件名与网址，使用前请以官方页面为准；"
                "本文不写未经核实的绝对地址。",
)

# --------------------------------------------------------------- 导读
K.callout(doc, "先看结论", [
    "本机 8 GB 显存够用：全程冻结 CLIP ViT-B/16、只做前向推理，显存占用约 1.2–2 GB（推导见 1.3）。"
    "真正的瓶颈是 15.6 GB 内存与只剩 53.4 GB 的 C 盘——图像、权重、缓存一律放 F 盘（剩 86.7 GB），"
    "C 盘只放 conda 环境与代码。本文只管「环境能不能跑、跑得对不对」，命令按「复制粘贴就能用」写，"
    "并说明每一步为什么；方案、实验、文献、写作、答辩见 01–06 其余文档。",
], kind="ok")

# --------------------------------------------------------------- 一、硬件
K.h1(doc, "一、硬件方案：两套机器，一套代码")
K.p(doc, "本课题的实际需求是：加载约 1.5 亿参数的双塔模型、抓中间层激活、修改注意力头输出。"
         "这三件事都在推理阶段完成、不涉及反向传播，算力需求比「训练大模型」低一到两个数量级。")

K.h2(doc, "1.1 本机家底（实测）")
K.table(doc,
        ["部件", "实测规格", "对本课题的意义"],
        [
            ["GPU", "RTX 4060 Laptop，8188 MiB，驱动 566.07", "主力运算；8 GB 跑 fp32/fp16 推理都够"],
            ["CPU", "i9-13900H，14 核 20 线程", "图像解码；num_workers 给 4–6"],
            ["内存", "15.6 GB", "比显卡更紧：多进程读图 + 缓存很快吃满"],
            ["磁盘 C", "剩余 53.4 GB", "只放 conda 环境（8–12 GB）、代码"],
            ["磁盘 F", "剩余 86.7 GB", "数据集、权重、全部缓存"],
            ["已有 / 缺失", "Windows x64；Python 3.12.5（系统级）；git 2.49.0；"
                            "无 conda；无 CUDA Toolkit（nvcc 不在 PATH）", "系统 Python 不动（第 3 节）；"
                            "conda 必装；CUDA Toolkit 不装（2.2）"],
        ],
        widths=[2.4, 6.8, 6.8], font_size=9, first_col_bold=True, zebra=True)
K.caption(doc, "表 1-1  本机硬件与软件实测清单")

K.h2(doc, "1.2 两套方案的分工")
K.p(doc, "方案 A 本机、方案 B 服务器，不是二选一而是前后接力：调试要反复改代码、随时看报错，远程做效率极低；"
         "流水线一旦稳定，多 seed 重复实验就是纯算力问题。")
K.table(doc,
        ["维度", "方案 A：本机 4060 Laptop（8 GB）", "方案 B：实验室 3090（24 GB）"],
        [
            ["角色", "开发机：写代码、调流水线、看错误样本", "跑量机：全量重复、k 扫描、多 seed"],
            ["优势", "随时可用、改一行立刻能试", "显存 3 倍、全量实验快 3–4 倍"],
            ["限制", "显存 8 GB、内存 15.6 GB，不适合长跑", "要 SSH、排队、环境迁移、数据同步"],
            ["batch", "fp16 64（保守 32）；fp32 32；调试先 8", "fp16 256（保守 128）；fp32 128"],
            ["承担", "基线单次评测、k 扫描冒烟、可视化", "k 扫描全档、消融、最终数字"],
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
K.callout(doc, "抓激活的三条纪律（第 3 周就养成）", [
    "① 只抓需要的层：12 层全存 32 个样本仅 0.22 GB，但存成全库就是几十 GB 文件。"
    "② 抓到就 .detach().cpu()：留在 GPU 上是「越跑越慢最后 OOM」最常见的原因。"
    "③ forward hook 的返回值会替换该层输出——这是修改注意力头的入口，且在 torch.no_grad() 下仍生效，"
    "所以「冻结 + 干预」不需要反向传播。",
], kind="info")

K.h2(doc, "1.4 本地开发 → 服务器跑全量：代码一行不改")
K.p(doc, "前提守住三条：① 路径全从 config 读，代码里不出现 C:\\ 或 /home/，统一 pathlib；② 设备用 "
         "torch.device(\"cuda\" if torch.cuda.is_available() else \"cpu\") 自动判断；③ 结果按 run_id 落盘。"
         "这样迁移只改 4 个值：batch_size（64→256）、num_workers（4→8）、data_root"
         "（F:\\datasets\\waterbirds → /data/waterbirds）、cache_dir（F:\\cache\\clip → /data/cache/clip）。")
K.p(doc, "迁移五步：本机 commit 推送 → 服务器 clone 并按第 3 节重建环境 → 改 server3090.yaml → 服务器上先跑 "
         "selfcheck.py（不能省，两台机器环境不一定一样）→ nohup / tmux 起批处理，日志写进 results/raw。")

# --------------------------------------------------------------- 二、软件栈
K.h1(doc, "二、软件栈：把版本钉死")
K.p(doc, "不锁版本时，半年后重装一次 torch 可能已跳两级、numpy 到 2.x，当初跑出 78.4% 的脚本直接报错。"
         "原则是「装定住的版本」：① 大版本锁死、小版本给区间；② torch 与 torchvision 整对装（编译期绑定，"
         "配错报 nms 缺失）；③ numpy < 2.0（复现代码多用 1.x 接口，2.x 删了 np.float_ 等）。")
K.h2(doc, "2.1 版本锁定表")
K.table(doc,
        ["包 / 组件", "建议版本", "锁定理由", "装错的后果"],
        [
            ["Python", "3.10.x", "研究仓库多在 3.8–3.10 验证", "3.12+ 部分包无 wheel"],
            ["conda 环境", "clipbg", "与系统 Python 3.12.5 隔离", "污染系统 Python"],
            ["torch", "2.4/2.5（cu121）", "接口稳定；cu121 自带运行时", "装成 CPU 版 → 无 CUDA"],
            ["torchvision", "0.19 / 0.20", "与 torch 严格配对", "报错或 nms 算子缺失"],
            ["open_clip_torch / timm", "2.24–2.26（≥2.20）/ 0.9–1.0", "HF 加载与模型接口稳定；timm 决定 ViT 实现", "缺 ViT-B-16 映射；与 timm 冲突"],
            ["transformers", "4.40–4.46", "只做交叉验证，不需新特性", "与 torch 版本耦合报错"],
            ["numpy", "1.26.4", "1.x 最后一档稳定版", "2.x 让老代码 import 崩"],
            ["scipy / pandas", "1.11–1.14 / 2.0–2.2", "与 numpy 1.26 配套；读 metadata.csv", "新版要求 numpy≥2，互相打架"],
            ["scikit-learn", "1.3–1.6", "统计指标与简单分析（可选）", "新版对 numpy 有硬要求"],
            ["matplotlib / seaborn", "3.7–3.9 / 0.13", "柱状图、k 曲线、144 头热力图", "中文变方框；新旧不兼容"],
            ["tqdm / pyyaml", "4.66+ / 6.0+", "进度条、读写 config", "无"],
            ["jupyter / Pillow", "1.x（可选）/ 10–11", "交互看错误样本 / 读 jpg", "Pillow 过旧读不了 jpg"],
        ],
        widths=[2.9, 3.0, 6.3, 3.8], font_size=8.2, first_col_bold=True, zebra=True)
K.caption(doc, "表 2-1  软件栈版本锁定表（区间而非唯一答案；以 pip freeze 实际输出为准）")
K.p(doc, "若真踩到坑：torchvision 与 torch 不配 → 整对卸载、按 pytorch.org 官方命令重装；装成 CPU 版 → "
         "见第 3 节；numpy 被别的包升到 2.x → 装 numpy<2 后立刻重新 freeze，把上限写进 requirements。")

K.h2(doc, "2.2 为什么不需要装 CUDA Toolkit")
K.p(doc, "PyTorch 的 cu121 轮子已内含所需 CUDA 运行时，只要驱动够新就能用；nvcc 只有自己编译 CUDA 算子时才需要，"
         "本课题不做。所以「nvcc 不在 PATH」不是问题，装 Toolkit 反而容易污染环境。本机驱动 566.07 支持 CUDA 12.x "
         "（对应关系以 NVIDIA 官方兼容性表为准，请自行核对），装 cu121 轮子是安全选择。")

# --------------------------------------------------------------- 三、安装
K.h1(doc, "三、安装步骤（Windows，按顺序复制粘贴）")
K.p(doc, "命令在 PowerShell 和 cmd 里都能用（全部单行，不必关心换行差异）。本机已有系统 Python 3.12.5 与 "
         "git 2.49.0，缺 conda、缺 CUDA Toolkit：系统 Python 保持不动（混用是事故源头），git 跳过，Toolkit 不装。")
K.h2(doc, "3.1 安装 Miniconda")
K.num(doc, 1, "下载：清华镜像目录 https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/ 里找最新的 "
              "Miniconda3-latest-Windows-x86_64.exe（文件名随版本变化，请自行核对）；或走 Anaconda 官网。")
K.num(doc, 2, "向导选「Just Me」，路径用纯英文无空格（如 C:\\miniconda3，conda 对中文/空格路径兼容差）；"
              "最后一步「Add to my PATH」不勾（会抢 PATH），用开始菜单的 Anaconda Prompt 进入。")
K.num(doc, 3, "验证：conda --version 与 where.exe conda 都有输出即成功。")
K.h2(doc, "3.2 配置镜像并建环境")
K.p(doc, "为什么配镜像：默认源都在境外，装 torch 这种 2 GB 以上轮子常在 90% 处超时，"
         "conda 解析几十个包依赖一次卡住就是二十分钟。镜像只加速下载，包内容由哈希保证不变。")
K.code_block(doc, CODE_CONDA_RC, size=8.5)
K.p(doc, "为什么用 3.10 而不是系统那个 3.12：要复现的 TextSpan / LTC 一类研究代码基本在 3.8–3.10 上验证过。")
K.code_block(doc, CODE_INSTALL, size=8)
K.p(doc, "关键点：Windows 上 PyPI 与国内镜像是 CPU-only 版 torch，装完 torch.cuda.is_available() 会是 False，"
         "必须从官方 CUDA 索引装 cu121 轮子——「镜像不等于万能」的典型例子。官方源超时就挂代理，或加 "
         "-f https://download.pytorch.org/whl/cu121/torch_stable.html 只从官方源找大文件，别退回镜像装 CPU 版。"
         "第 4 步打印 True 与 12.1 就算打通。")

# --------------------------------------------------------------- 四、自检
K.h1(doc, "四、环境自检：一条命令确认「能用」")
K.p(doc, "环境问题必须在第 1 周暴露。等第 7 周下完 1.5 GB 数据才发现 torch 是 CPU 版，损失的是整周。"
         "下面这份脚本三十秒跑完，输出存进 results/env/ 作为两台机器的一致性证据。")
K.h2(doc, "4.1 脚本全文")
K.code_block(doc, CODE_SELFCHECK, size=7.6)
K.p(doc, "第 1 周跑 python scripts/selfcheck.py；第 3 周再跑 python scripts/selfcheck.py --with-clip。"
         "存档写法（两个终端都支持）：python scripts\\selfcheck.py > results\\env\\selfcheck_4060.txt 2>&1。")
K.h2(doc, "4.2 判读与通过判据")
K.bullet(doc, [("第 1–4 项：", {"bold": True}),
               ("Python 显示 3.12.5 → conda activate 没生效；PyTorch 编译 CUDA 为 None → 装成 CPU 版（回 3.2 重装）；"
                "CUDA 为 False → 先查 nvidia-smi 与驱动；GPU 名/显存不符 → 可能用了核显或远程会话。", {})])
K.bullet(doc, [("第 5–7 项：", {"bold": True}),
               ("随机张量前向报 CUDA error → 驱动与运行时版本不匹配；open_clip 报 HTTP 错误/卡住 → 设 HF_ENDPOINT "
                "或走离线路径。", {})])
K.p(doc, "五条通过判据：① 七项全正常且第 3 项为 True；② 记下 TFLOPS 与真实 img/s，替换第 8 节估算；"
         "③ 两台机器各跑一遍存档；④ 两个锁版本文件已提交；⑤ 用 Dataset + DataLoader 在 GPU 上跑一次 100 张图"
         "真实前向（随机张量只验证算子，不验证数据管线）。")

# --------------------------------------------------------------- 五、数据
K.h1(doc, "五、数据准备：Waterbirds")
K.p(doc, "Waterbirds 由 Sagawa 等在 GroupDRO（ICLR 2020）中提出：图像源自 CUB 鸟类数据，合成为水鸟/陆鸟两类，"
         "每张图另有背景标注（水面/陆地），样本于是切成 2×2 四组，其中「水鸟+陆地」「陆鸟+水面」极少，"
         "是标准组偏移设定。它自带前景/背景分割掩码，可做出「只留前景」「只留背景」「背景替换」三组对照输入，"
         "第 7–9 周诊断会直接用到。")
K.callout(doc, "数据来源与一条底线", [
    "来源：Waterbirds 随 GroupDRO 论文与 WILDS 数据集系列公开提供，入口见论文作者主页与 WILDS 站点"
    "（地址请自行核对；检索：Waterbirds dataset Sagawa GroupDRO WILDS）。官方发布含图像压缩包（文件名含 "
    "waterbird_complete95_forest2water2，约 1.1 GB 量级）、掩码包（segmentations，约 200 MB 量级）与 "
    "metadata.csv，文件名与体积以官方页面为准（请自行核对）。",
    "底线：别从网盘拿数据。metadata.csv 被改过（排序、删行）四组统计就对不上，而你后面所有准确率与最差组"
    "结论都建立在这张表上。解压后算一次 MD5，服务器上用同一 MD5 校验。",
], kind="warn")
K.h2(doc, "5.1 目录与完整性校验")
K.code_block(doc, CODE_DATASET_TREE, size=8.5)
K.p(doc, "解压后先做四件事，任一项不过就别往下走：① metadata 行数 = 图像数（Waterbirds 总量在 1.18 万张量级，"
         "以官方包为准、请自行核对）；② 每个 split 的 2×2 四格都 > 0；③ 无 0 字节文件；④ mask 数与图像数一致。")
K.h2(doc, "5.2 四组统计脚本（可直接运行）")
K.p(doc, "只用标准库，环境刚建好就能跑。输出 train/val/test 三张 2×2 交叉表、每行合计、最小组占比与"
         "缺失图像数；数字填进 5.3 的表，就是 02 号文档「四组样本统计表」的口径。")
K.code_block(doc, CODE_DATASET_STATS, size=7.8)
K.h2(doc, "5.3 结果填写")
K.p(doc, "把脚本输出的三行数字填成 2×2 交叉表（train/val/test 各一行，四组各一格 + 合计一列），即 02 号文档"
         "「四组样本统计表」的口径。为什么先统计再跑实验：少数群体常只有几十到几百张，口径一错（把 place 数值"
         "当第三类、或 val/test 弄反），最差组准确率会虚高且单次运行看不出来。")

# --------------------------------------------------------------- 六、权重
K.h1(doc, "六、模型权重：CLIP ViT-B/16 的两条加载路径")
K.p(doc, "用 OpenAI 的 CLIP ViT-B/16，通过 open_clip 加载：create_model_and_transforms(\"ViT-B-16\", "
         "pretrained=\"openai\")。图像塔 86 M + 文本塔 63 M ≈ 149 M 参数，fp32 约 0.6 GB。"
         "主线选 open_clip 而非 transformers，是因为它模块层级清楚、抓激活与替换头输出更直接；"
         "transformers 留作交叉验证。")
K.table(doc,
        ["路径", "适用场景", "做法", "注意"],
        [
            ["一：在线", "首次跑、有网", "pretrained=\"openai\" 并指定 cache_dir；首次下载、之后走缓存",
             "约 0.6 GB，国内可能慢；设 HF_ENDPOINT 镜像"],
            ["二：离线", "服务器无外网或反复重装", "本机下好 .bin 拷过去，pretrained 直接指文件路径",
             "文件名与缓存布局随版本变（请自行核对），核对大小与 MD5"],
        ],
        widths=[2.4, 3.8, 6.0, 4.0], font_size=8.5, first_col_bold=True, zebra=True)
K.caption(doc, "表 6-1  CLIP 权重的两条加载路径")
K.p(doc, "open_clip 的下载走 huggingface_hub，设两个环境变量就够、不需要配代理：HF_ENDPOINT 指国内镜像"
         "（hf-mirror.com 是第三方社区镜像，可用性随时间变化，请自行核对），HF_HOME 把缓存挪到 F 盘。"
         "把脚本里的 IMAGE 换成数据集里任意一张图；第 3 周的验收标准就是打印出两个类别的相似度分数且大小"
         "关系合理。若报 unexpected keyword argument，去掉 cache_dir、改用 HF_HOME。")
K.code_block(doc, CODE_CLIP_LOAD, size=7.8)
K.h2(doc, "6.1 冻结模型的三条纪律")
K.p(doc, "① model.eval() 关 dropout、固定 BN；② p.requires_grad_(False) 彻底关梯度（留着会为每次前向建计算图，"
         "显存翻倍）；③ torch.no_grad() 包住前向——hook 在 no_grad 下仍能改输出，这正是干预模块能工作的原因。"
         "另有纪律：权重必须跨机器一致，把大小与 MD5 写进 results/env/ 存档。")

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
            ["LTC", "直接对标方法：头级评分 + 选头 + 定向校正与对照",
             "论文《Locate then Correct: Debiasing Attention Heads in CLIP》；是否开源请自行核对，"
             "未开源则按第 3 节公式复现", "需自行核对"],
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
         "故本机给 4、服务器给 8–12。")
K.h2(doc, "8.2 耗时预算")
K.p(doc, "估法：ViT-B/16 @224 单图前向约 17.6 GFLOPs（常用口径，随实现浮动）。4060 Laptop fp16 有效算力按 "
         "20–40 TFLOPS 估，理论 1000–2000 img/s，实测受 IO、batch 与 kernel 启动开销影响往往只有 100–200 img/s；"
         "3090 约为其 3–4 倍。下表是排期用数字，不是承诺值。")
K.table(doc,
        ["场景", "规模", "4060 估算", "3090 估算", "说明"],
        [
            ["验证集一次评测", "约 1.1 千张", "10–20 s", "3–6 s", "第 8 周要做几十次"],
            ["测试集一次评测", "约 5.8 千张", "40–70 s", "10–25 s", "主结果每个数字都要它"],
            ["k 扫描一轮（8 档，验证集）", "约 9 千张", "1.5–3 min", "30–60 s", "第 14 周主线"],
            ["144 头评分（含文本投影）", "2–3 遍全量前向", "5–10 min", "1.5–3 min", "第 11 周"],
            ["全量重复（8 档 × 3 设置 × 3 seed）", "约 72 次评测", "50–90 min", "15–25 min", "第 15 周，4060 一晚跑完"],
        ],
        widths=[4.2, 3.4, 2.6, 2.6, 3.4], font_size=8.5, first_col_bold=True, zebra=True)
K.caption(doc, "表 8-2  耗时预算（量级估算，用于排期；正式数据以 bench.py / selfcheck 实测为准）")
K.p(doc, "★ 排期结论：全部实验在本机 4060 上都能跑完，最重的一天也就是「晚上挂两小时」；服务器的意义是"
         "「多 seed 并行、当天出结果」，不是「没有它就跑不了」——第 1 周先打通本机，别为等服务器卡住进度。"
         "三条降耗手段：文本 embedding 只算一次并缓存；固定 batch 跑通全程（频繁改会让 cuDNN 反复选算法）；"
         "评测与绘图分离（评测只落盘 json/csv，改图样式不用重跑模型）。")

# --------------------------------------------------------------- 九、目录
K.h1(doc, "九、目录结构：代码 / 数据 / 结果 / 论文四分离")
K.p(doc, "做到第 20 周最容易出的问题不是模型不 work，而是「找不到当时跑出这个数的脚本」。四分离的目的很直接："
         "任何一张图、任何一个数字都能反查到生成它的代码与配置。四条规矩：① data/ 不进 Git、不放图片本体，"
         "只放来源说明与校验脚本；② results/raw/ 进 .gitignore，tables/ 与 figures/ 必须进 Git；"
         "③ paper/ 只放论文与图源，docs/ 放 00~07 号文档与翻译稿；④ 任何脚本不许写绝对路径。")
K.code_block(doc, CODE_PROJECT_TREE, size=8.5)
K.p(doc, "四条规矩：① data/ 不进 Git、不放图片本体，只放来源说明与校验脚本（体积 GB 级、数据集不可再分发）；"
         "② results/raw/ 进 .gitignore，tables/ 与 figures/ 是论文成品、必须进 Git；③ paper/ 只放论文与图源，"
         "docs/ 放 00~07 号文档与翻译稿；④ 任何脚本不许写绝对路径。磁盘上 C 盘只需 15 GB 以上空闲"
         "（conda 环境 8–12 GB 是最大一头，pip 缓存可 pip cache purge）；数据 1.3–1.6 GB、权重与 HF 缓存 1–2 GB "
         "都在 F 盘。C 盘实在紧就用 conda create -p F:\\envs\\clipbg 把环境建到 F 盘。")

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
        ["字段", "含义", "示例"],
        [
            ["run_id", "日期_实验类型_参数_方式_种子", "20261118_k10_zero_seed42"],
            ["date / git_commit", "日期 + 当时 commit 前 7 位", "2026-11-18 / a3f9c21"],
            ["seed / setting / k / op", "随机种子 / 原始·定向·随机 / 抑制头数 / 干预方式", "42 / targeted / 10 / zero"],
            ["overall / worst", "总体与最差组准确率", "0.812 / 0.734"],
            ["batch / device / sec", "batch、设备、本次耗时与显存峰值", "64 / RTX4060L / 68 s / 1.7 GB"],
        ],
        widths=[3.6, 7.0, 5.2], font_size=8.5, first_col_bold=True, zebra=True)
K.caption(doc, "表 10-1  实验记录表字段（一行 = 一次运行，禁止把多次运行合并成一行）")
K.p(doc, "run_id 全部小写、下划线分隔；禁止出现 final、new、test2、最终版 这类名字——三个月后你分不清哪个是哪个。")

# --------------------------------------------------------------- 十一、排查
K.h1(doc, "十一、常见问题排查表")
K.p(doc, "遇到问题三个动作：① 读完整报错，尤其最后三行；② 缩到最小可复现例子（去掉数据、只留十行）；"
         "③ 把 python / torch / CUDA / GPU 四项打印出来存档备查。")
K.table(doc,
        ["现象", "最可能的原因", "处理办法"],
        [
            ["torch.cuda.is_available() 为 False", "装了 CPU 版；或驱动异常",
             "看 torch.version.cuda 是否 None；是则按 3.2 从 cu121 源重装；再查 nvidia-smi"],
            ["CUDA out of memory", "batch 太大；激活未释放；同进程两份模型；别的进程占卡",
             "降 batch 先跑通；激活立即 detach().cpu()；查僵尸 python 进程"],
            ["pip 下载超时", "默认源境外、镜像未配或临时不可用",
             "确认 pip config list 是清华源；torch 必须走官方 cu121 源；加 --retries 5 --timeout 120"],
            ["conda activate 无反应", "系统终端未 conda init；PATH 被污染",
             "改用 Anaconda Prompt；或 conda init powershell 后重开窗口"],
            ["Windows 路径报错", "中文/空格路径；反斜杠被当转义", "字符串用 r\"F:\\\\...\"；统一 pathlib；数据别放桌面"],
            ["DataLoader 报错或卡住", "num_workers>0 但缺少 main guard 入口保护",
             "入口放进 if __name__ == \"__main__\"；先设 num_workers=0 排错，再升到 4"],
            ["operator torchvision::nms 不存在", "torch 与 torchvision 不配对", "整对卸载重装（见第 2 节）"],
            ["open_clip 加载卡住 / HTTP 错误", "HF 连接超时、镜像未生效", "设 HF_ENDPOINT 与 HF_HOME；或走离线 .bin 路径"],
            ["数据对不上号或每次结果不一样", "解压不全/二手改版；随机对照与 shuffle 未固定种子",
             "官方包重解压 + dataset_stats.py 对数；seed_everything 统一入口并写进 run_id"],
        ],
        widths=[4.4, 5.6, 6.0], font_size=8.5, zebra=True)
K.caption(doc, "表 11-1  常见问题排查表（覆盖约 90% 的实际卡点）")
K.p(doc, "关于多卡：本课题用不到多卡（8 GB 单卡足够，3090 也是单卡），不需要学 DistributedDataParallel。"
         "但「batch 与卡数无关」这点常被搞混：换到 3090 只改 batch_size，不改任何模型代码。")

# --------------------------------------------------------------- 十二、周次
K.h1(doc, "十二、第 1–3 周执行清单（对齐 plan_spec）")
K.p(doc, "环境搭建属阶段一（第 1–6 周），按 plan_spec 压在前三周完成。第 1 周任务书写得很明确："
         "「装好 Miniconda，建好 conda 环境（本周只到这一步）」。")
_week_criteria = {
    1: ("装 Miniconda、建 clipbg 环境、装 torch 与基础依赖（同时开始 ML 概念扫盲）",
        "conda activate clipbg 成功；selfcheck 前 6 项正常；两个锁版本文件已生成", "2、3、4 节"),
    2: ("PyTorch 核心：Tensor、Dataset/DataLoader、nn.Module；★ 学会 register_forward_hook",
        "能独立写出「加载 CIFAR-10 子集 → 前向 → 抓某层输出」的 50 行脚本", "1.3、4.2 节"),
    3: ("装 open_clip、下载 ViT-B/16 权重、跑通一次 CLIP 推理并打印两个类别相似度",
        "selfcheck --with-clip 出现 [OK]；check_clip.py 相似度合理；权重 MD5 已记录", "5、6 节"),
}
_wk_rows = []
for _w, _pid, _theme, _tasks, _deliver in P.WEEKS[:3]:
    _c, _m, _sec = _week_criteria[_w]
    _wk_rows.append([f"第 {_w} 周\n{P.week_dates(_w)}", _c, _m, _sec])
K.table(doc,
        ["周次", "本周环境任务（主题取自 plan_spec）", "完成判据", "本文对应"],
        _wk_rows,
        widths=[2.2, 7.4, 4.6, 2.0], font_size=8.5, first_col_bold=True, zebra=True)
K.caption(doc, "表 12-1  第 1–3 周环境任务与完成判据（周次取自 plan_spec.WEEKS；第 1 周「只到建环境」）")
K.p(doc, "第 3 周后环境只剩维护。任何一周没按判据通过，宁可推迟一周，也不要带着不确定的环境进入阶段二"
         "——基线一旦建立在不稳定环境上，后面所有对比实验都要重跑。")

# --------------------------------------------------------------- 十三、工具软件
K.h1(doc, "十三、编程之外的配套软件（容易被漏掉的一半）")
K.p(doc, "「需要准备什么软件」不只是 Python 包。任务书要求文献调研、技术路线图、论文排版、答辩演示，"
         "这些都要各自的工具。下表按「什么时候真正用上」排序，不用一次装完——但第 1 周至少要把前两项装好。")

K.table(doc,
        ["用途", "推荐软件", "必需性", "什么时候装", "为什么 / 注意"],
        [["代码编辑与调试", "VS Code（＋ Python、Jupyter 扩展）\n或 PyCharm Community", "必需", "第 1 周",
          "要看变量、设断点、跑 notebook；VS Code 还能 Remote-SSH 连实验室服务器，一个工具两用"],
         ["文献管理与笔记", "Zotero（可选 Better BibTeX 插件）", "必需", "第 1 周",
          "16 篇文献的题录、PDF、笔记集中管；写论文时能一键导出 GB/T 7714 格式，省掉手工排版"],
         ["文档写作", "Microsoft Word（用学院模板）", "必需", "第 6 周前",
          "开题报告就要用；公式用 Word 自带公式编辑器足够，不必上 MathType"],
         ["图表与流程图", "draw.io（网页版即可，免安装）", "必需", "第 5 周",
          "画技术路线图、抑制位置示意图；导出矢量 PDF，插进论文不缺清晰度"],
         ["论文排查与备份", "OneDrive / 坚果云 ＋ Git 远端仓库", "必需", "第 1 周",
          "论文和代码每天自动备份一次。硬盘坏一次足以毁掉整个毕设，这是最低成本的保险"],
         ["服务器连接", "VS Code Remote-SSH 或 MobaXterm", "需要 3090 时", "第 13 周前",
          "跑全量重复实验用 tmux/nohup 挂长任务，断网不中断"],
         ["截图与标注", "Snipaste / 系统自带截图", "推荐", "第 9 周",
          "记录报错现场、给案例图加框标注，写诊断报告时省大量时间"],
         ["思维导图", "XMind", "可选", "第 3 周",
          "梳理「三代研究脉络」「六个环节」这类结构；不是必需，喜欢用再用"],
         ["答辩演示", "PowerPoint 或 WPS", "必需", "第 24 周",
          "PPT 结构见 02 号文档第七章；提前确认答辩教室的 Office 版本，避免字体错位"],
         ["论文查重", "学校指定系统（如知网）", "必需", "第 22 周",
          "学院统一安排，提前问清免费次数与提交格式，别等到截止前一天"]],
        widths=[2.6, 4.4, 1.6, 2.6, 5.0], align="llccl", font_size=8.5, first_col_bold=True)

K.caption(doc, "表 13-1  配套工具软件清单（按使用时间排序）")

K.callout(doc, "三件「不要装」的东西",
          ["**不要装 CUDA Toolkit**：PyTorch 的 cu121 轮子自带运行时，装了反而可能污染 PATH（见 2.2 节）。",
           "**不要再装第二个 Python**：系统已有的 3.12.5 保持不动，所有工作都在 conda 环境里做；"
           "两套 Python 混用是最常见的「明明装了却 import 不到」的原因。",
           "**不要一开始就上 LaTeX**：学院给的是 Word 模板，本科论文用 LaTeX 排版公式的收益抵不上模板适配的成本。"
           "真要转，等论文内容定稿（第 22 周）再考虑。"],
          kind="warn")

K.p(doc, "磁盘预算：Waterbirds 图像与分割掩码约 1~2 GB，CLIP 权重约 0.6~1.2 GB（两种格式各一份就翻倍），"
         "conda 环境约 6~8 GB，实验结果与图表约 1 GB，论文与文献约 1 GB。"
         "整机留出 **15 GB** 比较稳妥——本机 C 盘剩 53.4 GB、F 盘剩 86.7 GB，建议把数据与缓存都放 F 盘。")

# --------------------------------------------------------------- 附录
K.h1(doc, "附录 A：本文标注「需自行核对」的条目")
K.p(doc, "规则：不确定的版本号、文件名、网址宁可不写也不编造。全文共 9 处「需自行核对」，核对完把结果写进 "
         "docs/ 下的环境说明，论文附录「实验环境」用核对后的版本号而非本文建议区间：")
K.bullet(doc, [("版本号类 4 处：", {"bold": True}),
               ("Miniconda 包名（3.1）；torch/torchvision 配对（2.1、3.2，查 pytorch.org Get Started）；"
                "open_clip_torch 小版本（2.1，pip index versions）；驱动 566.07 的 CUDA 上限（2.2，查 NVIDIA 兼容表）。", {})])
K.bullet(doc, [("地址与数据类 3 处：", {"bold": True}),
               ("清华镜像地址（3.2）；Waterbirds 下载页与包名（5，检索 Waterbirds dataset Sagawa GroupDRO WILDS）；"
                "各 split 精确样本数（5.1、5.3，以 dataset_stats.py 输出为准）。", {})])
K.bullet(doc, [("第三方与开源状态 2 处：", {"bold": True}),
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
