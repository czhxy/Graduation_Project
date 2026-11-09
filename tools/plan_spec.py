# -*- coding: utf-8 -*-
"""plan_spec.py —— 全部文档的唯一数据源（single source of truth）。

任何一处改动（周次、阶段、里程碑、文献、任务）只需要改这里，
01~06 号文档全部从这里读取，保证口径一致。
"""
from datetime import date, timedelta

# ---------------------------------------------------------------- 时间锚点
# W1 的周一。用户选择“从今天起重新排”，故取系统当前日期。
ANCHOR = date(2026, 11, 9)
TOTAL_WEEKS = 26


def week_range(w):
    """第 w 周（1-based）的 (周一, 周日)"""
    mon = ANCHOR + timedelta(days=7 * (w - 1))
    return mon, mon + timedelta(days=6)


def week_dates(w):
    mon, sun = week_range(w)
    return f"{mon.month:02d}/{mon.day:02d}–{sun.month:02d}/{sun.day:02d}"


def week_iso(w):
    mon, _ = week_range(w)
    return f"{mon.year}-{mon.month:02d}-{mon.day:02d}"


# ---------------------------------------------------------------- 六个阶段
# 与任务书“进度安排”六段一一对应；基础补课压在阶段一的前三周。
PHASES = [
    dict(
        pid="P1",
        name="阶段一",
        weeks=(1, 6),
        title="补基础 · 搭环境 · 文献调研与开题",
        taskbook="任务书进度（1）：2025.11.01–12.15",
        goal="从「没学过机器学习」到「能读懂 CLIP 代码并跑通一次推理」，"
             "同时完成文献调研、英文翻译和开题报告。这是全流程最关键的阶段，"
             "基础不牢后面每一步都会卡。",
        focus="3 周补齐 ML/PyTorch 基础 + 3 周文献与开题，两条线并行推进",
        deliverables=[
            "可运行的 Python/PyTorch 环境（本机 4060 或实验室 3090 二选一打通）",
            "《开题报告》（含研究现状、技术路线、进度安排）",
            "《英文文献翻译》（1 篇，中文译文 + 原文对照）",
            "技术路线图（1 页，含 5 个环节）",
            "文献笔记 ≥6 篇（Zotero 或 Markdown 均可）",
        ],
        milestone="M1 — 开题",
    ),
    dict(
        pid="P2",
        name="阶段二",
        weeks=(7, 9),
        title="基线复现与背景依赖诊断",
        taskbook="任务书进度（2）：2025.12.15–12.31",
        goal="把 CLIP ViT-B/16 在 Waterbirds 上的零样本分类跑通，"
             "用四组准确率和错误样本把「背景依赖」这个现象量化出来、看得见。",
        focus="数据管线 → 基线 → 诊断，三步必须按顺序做完",
        deliverables=[
            "四组样本统计表（训练/验证/测试，含多数组与少数组）",
            "基线准确率总表：总体 / 四组 / 最差组",
            "背景依赖诊断报告（含 ≥8 个典型错误样本的可视化）",
            "可复现脚本：数据整理 + 基线评测",
        ],
        milestone="M2 — 基线冻结",
    ),
    dict(
        pid="P3",
        name="阶段三",
        weeks=(10, 13),
        title="背景相关头评分复现与定向抑制",
        taskbook="任务书进度（3）：2026.01.01–01.31",
        goal="复现头级评分与选择方法，定位「背景相关注意力头」，"
             "并对选中头的输出贡献做定向抑制，同时搭好随机抑制对照。",
        focus="评分 → 排序 → 选头 → 抑制 → 对照，五个动作逐个打通",
        deliverables=[
            "12 层 × 12 头 = 144 个头的评分表（含排序）",
            "背景相关头 Top-k 名单与层/头分布图",
            "定向抑制模块（支持 head 置零 / 缩放两种方式）",
            "随机抑制对照模块（同头数、同操作）",
            "干预正确性核查记录（干预位置、张量形状、前后数值）",
        ],
        milestone="M3 — 干预流水线打通",
    ),
    dict(
        pid="P4",
        name="阶段四",
        weeks=(14, 17),
        title="抑制头数参数分析与重复实验",
        taskbook="任务书进度（4）：2026.02.01–02.28",
        goal="把「抑制多少个头」这条主曲线做出来：验证集选参、测试集评测，"
             "定向抑制与随机抑制在相同头数下正面对比，报告均值与标准差。",
        focus="参数扫描是主线，重复实验保证结论可信，可视化负责把结论讲清楚",
        deliverables=[
            "k 扫描曲线（验证集）：总体 / 最差组 / 四组",
            "主结果表（测试集）：原始 vs 定向抑制 vs 随机抑制",
            "随机对照 ≥3 次重复的均值±标准差",
            "改善/退化案例图与人物-背景分离可视化",
            "阶段性报告（可直接用于中期检查）",
        ],
        milestone="M4 — 主结果冻结",
    ),
    dict(
        pid="P5",
        name="阶段五",
        weeks=(18, 21),
        title="补充消融 · 局限分析 · 论文撰写",
        taskbook="任务书进度（5）：2026.03.01–03.31",
        goal="补足审稿人会追问的实验（抑制方式、层分布、提示词敏感性），"
             "把方法的有效性边界和局限写清楚，并完成论文初稿。",
        focus="实验收口 + 论文成稿，这是工作量最重的一个月",
        deliverables=[
            "补充消融实验表（≥3 组）",
            "方法局限与适用范围分析（对应任务书第 (2)C 与 (3) 条）",
            "可复现代码仓库（README + requirements + 一键复现脚本）",
            "论文初稿（全文，含图表）",
        ],
        milestone="M5 — 论文初稿",
    ),
    dict(
        pid="P6",
        name="阶段六",
        weeks=(22, 26),
        title="定稿 · 查重 · 答辩 · 归档",
        taskbook="任务书进度（6）：2026.04.01–05月",
        goal="按深圳大学撰写规范完成定稿，通过查重与导师审阅，完成答辩并归档全部材料。",
        focus="格式与内容是两条独立战线，不要混在一起改",
        deliverables=[
            "毕业论文终稿（含中英文摘要、参考文献、致谢、附录）",
            "查重报告（重复率达标）",
            "答辩 PPT + 现场演示脚本",
            "成果归档包（论文 / 代码 / 数据 / 环境说明 / 结果记录 / 翻译）",
        ],
        milestone="M6 — 答辩",
    ),
]

# ---------------------------------------------------------------- 周计划
# (周次, 阶段id, 本周主题, [具体任务...], 本周交付/检查点)
WEEKS = [
    (1, "P1", "机器学习与深度学习概念扫盲",
     ["搞清 训练/验证/测试 三分、过拟合与欠拟合、损失函数、准确率等指标的含义",
      "理解「虚假相关 / 背景依赖」到底指什么：用本课题的水鸟-水面例子画一遍因果图",
      "复习 numpy 数组操作与 matplotlib 画图（后面天天用）",
      "装好 Miniconda，建好 conda 环境（见 04 号文档，本周只到这一步）"],
     "能用自己的话解释「为什么模型会靠背景猜类别」；conda 环境建好"),

    (2, "P1", "PyTorch 核心 + forward hook",
     ["张量与自动求导：requires_grad / backward / no_grad 的含义与区别",
      "nn.Module、Dataset、DataLoader、transforms 的标准写法",
      "用一个小数据集（如 CIFAR-10 子集）跑通一次「加载-前向-算指标」",
      "★ 学会 register_forward_hook：把中间层输出抓出来（本课题的技术地基）"],
     "能独立写出「加载数据 → 前向 → 抓中间层输出」的 50 行脚本"),

    (3, "P1", "Transformer / ViT / CLIP 原理 + 环境打通",
     ["自注意力、多头注意力、残差流、LayerNorm 的直觉理解（不求推导，求能讲清）",
      "ViT：patch embedding、位置编码、CLS token、12 层 12 头从哪来",
      "CLIP：图文对比学习、零样本分类 = 图像 embedding 与文本 embedding 的余弦相似度",
      "装 PyTorch + open_clip，下载 ViT-B/16 权重，跑通一次推理并打印四组之一的结果"],
     "★ 能跑通一次 CLIP 推理：输入一张鸟图，输出两个类别的相似度分数"),

    (4, "P1", "核心文献精读（上）+ 翻译选文",
     ["精读 ViT（文献 1）：只看结构与参数量，弄清 144 个头的来源",
      "精读 CLIP（文献 2）：重点看零样本分类与 prompt 模板那一节",
      "确定英文翻译选文（建议 TextSpan 或 head-pruning 那篇，见 03 号文档）",
      "把两篇文献的笔记写成固定模板：问题 / 方法 / 结论 / 与本课题的关系"],
     "2 篇精读笔记；翻译选文定稿并经导师确认"),

    (5, "P1", "核心文献精读（下）+ 技术路线图",
     ["精读 GroupDRO（文献 3）：搞清 Waterbirds 的定义、四组划分、worst-group accuracy",
      "精读 TextSpan（文献 4）：重点理解「文本分解」如何把表示拆到各个头上",
      "画技术路线图（1 页）：数据 → 基线 → 评分 → 抑制 → 对照 → 结论",
      "英文翻译完成初稿（≥60%）"],
     "★ 技术路线图定稿；四组划分能默写出来"),

    (6, "P1", "LTC 精读 + 开题报告",
     ["精读 LTC（文献 5）：头级评分公式、选头策略、抑制操作的具体做法",
      "完成开题报告：研究背景 / 现状 / 内容 / 技术路线 / 可行性 / 进度",
      "英文翻译定稿并排版（原文+译文对照）",
      "★ 开题答辩（M1）"],
     "★ M1：开题报告 + 翻译稿 + 路线图三件齐备"),

    (7, "P2", "Waterbirds 数据管线",
     ["下载 Waterbirds（含 segmentation mask），校验文件完整性",
      "写 Dataset：返回 图像 / 类别标签 / 背景标签 / 组别(0-3)",
      "★ 统计四组样本数（训练 / 验证 / 测试），填进 02 号文档的表格模板",
      "固定预处理与文本提示（如 'a photo of a {class}.'），写进 config"],
     "四组统计表出结果；数据能稳定迭代"),

    (8, "P2", "CLIP 零样本基线",
     ["实现零样本分类：图像 embedding 与两个类别的文本 embedding 算相似度",
      "在验证集上测总体 / 四组 / 最差组准确率",
      "在测试集上复测一遍，确认两次一致（排除数据泄漏/顺序错误）",
      "记录耗时、显存占用，写进结果记录"],
     "★ 基线数字冻结：总体、四组、最差组四项全部有数"),

    (9, "P2", "背景依赖诊断与典型样本",
     ["挑出「高置信度但判错」的样本，看它们的背景是什么",
      "做 ≥8 个典型案例的拼图：原图 + 真实类别 + 预测类别 + 置信度",
      "可选：Grad-CAM 或注意力图，看模型是否盯着水面/草地",
      "写诊断报告：背景依赖的现象、程度、四组之间的差异"],
     "★ M2：诊断报告 + 基线数字，交给导师确认后再进入 P3"),

    (10, "P3", "跑通 TextSpan 文本分解",
     ["拿到 TextSpan 官方代码，先原样跑通一个 demo",
      "搞懂「把图像表示投影到文本方向上」的数学含义（对照文献 4 第 3 节）",
      "在本课题数据上跑一次分解，得到每个头对若干文本概念的贡献",
      "记录：用的样本数、标签、文本提示（任务书明确要求记录这三项）"],
     "文本分解能对本课题数据输出每个头的贡献值"),

    (11, "P3", "头级评分与排序",
     ["定义「背景相关头」的评分：头对背景类文本方向的贡献强度",
      "对 12×12=144 个头全部打分并排序，输出评分表（csv）",
      "画评分热力图（层 × 头）与 Top-k 条形图",
      "检查评分稳定性：换一批样本重算，看排序是否大体一致"],
     "★ 144 头评分表 + 热力图；Top-k 名单初步确定"),

    (12, "P3", "定向抑制实现",
     ["★ 分清两种操作：表征贡献编辑（改残差流里的贡献项）vs 中间激活消融（直接把头输出置零）——任务书要求必须写清区别",
      "实现 head 输出置零；再实现按系数缩放（scale=0.5/0）",
      "先在 1~2 个头上做单点验证：抑制后输出应该变化，不抑制应该完全复现基线",
      "写数值体检：抑制前后 logits / 准确率变化是否在合理范围"],
     "单头抑制可复现、可回退；两种操作的区别写成一段文字"),

    (13, "P3", "随机抑制对照 + 小规模扫描",
     ["实现随机对照组：随机抽同样数量的头、做同样的操作",
      "随机对照至少跑 3 个不同随机种子",
      "小规模 k 扫描（如 k=1,5,10）：确认定向 vs 随机在趋势上有差异",
      "★ M3：干预流水线自检清单逐项打勾"],
     "★ M3：定向/随机两条链路都能端到端跑完，结果方向合理"),

    (14, "P4", "k 扫描（验证集）",
     ["系统扫描 k（如 1,2,5,10,20,30,50），每档记录总体/四组/最差组",
      "只允许用验证集选 k，把「选参流程」写成脚本，避免手动挑",
      "画 dose-response 曲线：横轴 k，纵轴准确率（多条线）",
      "初步判断：最差组何时改善、总体何时开始明显掉"],
     "k 扫描曲线（验证集）完成；最优 k 的选取规则定下来"),

    (15, "P4", "测试集复评与重复实验",
     ["用验证集选出的 k，在独立测试集上评测（★ 不能再用测试集调参）",
      "随机对照重复 3~5 次，报告均值 ± 标准差",
      "整理主结果表：原始 / 定向抑制 / 随机抑制 × 总体/四组/最差组",
      "记录每组实验的种子、显存、耗时"],
     "★ 主结果表（测试集）完成，均值±标准差齐全"),

    (16, "P4", "可视化与案例分析",
     ["改善案例：抑制后由错变对的样本；退化案例：由对变错的样本",
      "四组准确率对比柱状图、最差组-总体权衡散点图",
      "头评分与背景依赖程度的关系图（本课题的「分析」落点）",
      "所有图统一字号/配色/导出 300dpi PNG + 矢量 PDF"],
     "全套图表（≥8 张）可直接放进论文"),

    (17, "P4", "阶段报告与中期沟通",
     ["把 P2~P4 的结果整理成 15 页阶段报告",
      "向导师汇报：现象是否成立、方法是否有效、卡点在哪",
      "★ M4：主结果冻结，后续不再改主实验设置",
      "根据导师意见调整 P5 的补充实验清单"],
     "★ M4：阶段报告 + 导师确认，主结果定稿"),

    (18, "P5", "补充消融实验",
     ["消融 1：抑制方式（置零 vs 缩放 vs 负向放大）",
      "消融 2：选头策略（Top-k vs 随机 vs 按层均匀）",
      "消融 3：提示词敏感性（3 套不同 prompt 模板）",
      "消融 4（可选）：单层抑制 vs 跨层抑制"],
     "≥3 组补充消融表，能回答「结论对设置是否敏感」"),

    (19, "P5", "有效性边界、局限分析与代码整理",
     ["写清方法在什么条件下有效、什么条件下失效（对应任务书要求）",
      "★ 明确声明：头级干预 ≠ 完整回路发现；本文只做头级归因与抑制",
      "整理代码仓库：README、requirements、config、一键复现脚本",
      "提交前跑一次「干净环境复现」自检"],
     "代码仓库可交付；局限分析成文"),

    (20, "P5", "论文撰写（上）",
     ["第 1 章 绪论：背景、意义、国内外研究现状、本文工作",
      "第 2 章 相关理论与技术：ViT、CLIP、注意力头、虚假相关",
      "第 3 章 方法：评分、选头、抑制、对照实验设计",
      "每章写完立刻让导师看，不要攒到最后"],
     "论文第 1~3 章初稿"),

    (21, "P5", "论文撰写（下）",
     ["第 4 章 实验：设置、基线、主结果、消融、可视化",
      "第 5 章 结论与展望；摘要（中英文）；参考文献格式统一",
      "★ M5：全文初稿完成，图表编号与正文引用对齐",
      "自查：任务书 8 条课程目标是否都有对应章节"],
     "★ M5：论文全文初稿"),

    (22, "P6", "修改润色与查重",
     ["按导师意见逐条修改并留修改记录",
      "统一术语（全文统一用 Transformer / 注意力头 / 虚假相关）",
      "查重并降重；核对参考文献真实性（★ 每条都要能查到）",
      "格式合规：页边距、字体、图表题注、页码、目录"],
     "查重报告达标；修改稿完成"),

    (23, "P6", "定稿送审",
     ["按深圳大学撰写规范逐项核对（可打印检查表打勾）",
      "英文摘要请人帮忙润色一遍",
      "附录：代码清单、超参表、完整结果表",
      "★ 提交定稿给导师审阅"],
     "定稿提交；导师审阅意见返回"),

    (24, "P6", "答辩准备",
     ["PPT 结构：背景 2 页 / 问题 2 页 / 方法 4 页 / 结果 6 页 / 结论 2 页",
      "准备 3 分钟版和 10 分钟版两个讲法",
      "★ 现场演示脚本：一条命令跑出「抑制前 vs 抑制后」对比",
      "预答辩：找同学当评委，练问答"],
     "★ M6 前置：PPT + 演示 + 问答清单"),
    (25, "P6", "答辩与修改",
     ["★ 正式答辩",
      "记录评委问题与建议，当天整理成修改清单",
      "按意见修改论文并请导师确认"],
     "★ M6：答辩通过；论文按意见修改完成"),
    (26, "P6", "成果归档",
     ["提交论文终稿（纸质 + 电子）",
      "归档：代码仓库、数据集说明、环境说明、结果记录、翻译稿、任务书",
      "把可发表的部分整理成投稿草案（如导师推荐）",
      "复盘：写下这套流程里最耗时的三件事"],
     "全部材料归档完成"),
]

# ---------------------------------------------------------------- 里程碑
MILESTONES = [
    ("M1", "开题", 6, "开题报告通过、技术路线定稿、翻译稿完成"),
    ("M2", "基线冻结", 9, "四组统计 + 基线四项数字 + 诊断报告"),
    ("M3", "干预打通", 13, "评分表 + 定向抑制 + 随机对照 端到端可跑"),
    ("M4", "主结果冻结", 17, "k 曲线 + 测试集主表 + 重复实验 + 阶段报告"),
    ("M5", "论文初稿", 21, "全文初稿 + 图表齐全"),
    ("M6", "答辩", 25, "答辩通过 + 材料归档"),
]

# ---------------------------------------------------------------- 文献
# kind: core=任务书指定必读；support=强相关必读；extra=按需选读
LITERATURE = [
    dict(no=1, kind="core", short="ViT",
         title="An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale",
         authors="Dosovitskiy A, Beyer L, Kolesnikov A, et al.",
         venue="ICLR 2021",
         why="本课题的模型骨架。CLIP 的视觉编码器就是一个 ViT-B/16。",
         read="第 3 节（方法）：patch embedding、位置编码、CLS token、"
              "多头自注意力的形状变换；表 1 看 B/16 的层数与头数。",
         must="能画出 ViT-B/16 的张量流：224×224×3 → 196+1 个 token → 12 层 → 768 维，"
              "并说清「12 层 × 12 头 = 144 个头」是怎么来的。",
         hours="3–4 h", when="第 4 周", prio="必读"),
    dict(no=2, kind="core", short="CLIP",
         title="Learning Transferable Visual Models from Natural Language Supervision",
         authors="Radford A, Kim J W, Hallacy C, et al.",
         venue="ICML 2021, PMLR 139: 8748-8763",
         why="定义了什么是对比学习、什么是零样本分类，是本课题的模型来源。",
         read="第 2 节（方法）与第 3.1 节（zero-shot 分类与 prompt 模板）；"
              "重点看「图像 embedding 与文本 embedding 做余弦相似度」那一段。",
         must="能解释：为什么 CLIP 没有分类头也能分类？prompt 模板为什么会影响结果？",
         hours="4–5 h", when="第 4 周", prio="必读"),
    dict(no=3, kind="core", short="GroupDRO / Waterbirds",
         title="Distributionally Robust Neural Networks for Group Shifts: "
               "On the Importance of Regularization for Worst-Case Generalization",
         authors="Sagawa S, Koh P W, Hashimoto T B, et al.",
         venue="ICLR 2020",
         why="Waterbirds 数据集就是这篇提出的；worst-group accuracy 也是这篇定义的。",
         read="第 3 节数据集部分：四组（组别）如何划分、为什么这是 group shift 问题；"
              "以及 worst-group accuracy 的定义。",
         must="能默写 Waterbirds 的四组划分，并说清「多数组 / 少数组」分别是什么、"
              "为什么总体准确率高不代表模型好。",
         hours="3 h", when="第 5 周", prio="必读"),
    dict(no=4, kind="core", short="TextSpan",
         title="Interpreting CLIP's Image Representation via Text-Based Decomposition",
         authors="Gandelsman Y, Efros A A, Steinhardt J",
         venue="ICLR 2024",
         why="本课题方法论的直接来源：把 CLIP 的图像表示按「文本方向」分解到各个组件。",
         read="第 3 节：分解公式（如何把表示写成各组件贡献之和）、第 4 节："
              "如何用分解定位到注意力头；附录里的实现细节。",
         must="能写出分解公式并解释每一项的物理含义；"
              "能说清「为什么可以按文本方向量化某个头对背景的贡献」。",
         hours="6–8 h", when="第 5 周", prio="必读（也是英文翻译首选）"),
    dict(no=5, kind="core", short="LTC",
         title="Locate then Correct: Debiasing Attention Heads in CLIP",
         authors="Yeo W J, Mao R, Abdar M, et al.",
         venue="ICML 2026, PMLR 306: 148640-148677",
         why="本课题要复现的直接对标方法：定位背景相关头并对其做定向校正。",
         read="方法全部：头级评分怎么算、按什么排序选头、"
              "「校正」具体作用在哪个位置（残差流贡献还是注意力输出），实验设置与对照。",
         must="能把 LTC 的流水线画成 5 个方框，并逐条对照本课题需要复现的部分。",
         hours="8–10 h", when="第 6 周", prio="必读（核心对标）"),

    dict(no=6, kind="support", short="Sixteen Heads",
         title="Are Sixteen Heads Really Better than One?",
         authors="Michel P, Levy O, Neubig G",
         venue="NeurIPS 2019",
         why="「剪掉注意力头」这件事的经典起点，教你怎么定义头的重要性并做消融。",
         read="全部（很短）：头重要性的打分方式、逐层/逐头剪枝实验。",
         must="能解释「头冗余」与「头重要性可排序」这两个前提，"
              "并说清它和本课题「抑制背景相关头」的异同。",
         hours="2–3 h", when="第 3 周", prio="强烈建议"),
    dict(no=7, kind="support", short="Voita",
         title="Analyzing Multi-Head Self-Attention: Specialized Heads Do the Heavy Lifting, "
               "the Rest Can Be Pruned",
         authors="Voita E, Talbot D, Moiseev F, et al.",
         venue="ACL 2019",
         why="证明注意力头存在功能分化（有的管句法、有的管位置），"
             "是本课题「背景相关头」假设的理论支撑。",
         read="第 3~4 节：头的功能分类与剪枝顺序。",
         must="能说清「功能特化」是什么意思，为什么它支持「背景依赖可以归因到特定头」。",
         hours="2–3 h", when="第 6 周", prio="强烈建议"),
    dict(no=8, kind="support", short="ROME",
         title="Locating and Editing Factual Associations in GPT",
         authors="Meng K, Bau D, Andonian A, et al.",
         venue="NeurIPS 2022",
         why="「定位后编辑」这一研究范式的代表作，帮助理解"
             "表征贡献编辑与中间激活干预的区别。",
         read="第 2~3 节：怎么定位关键层、怎么写入编辑；只看思路不看细节。",
         must="能说清 activation editing 与 ablation 的区别，"
              "并在论文里用一段话界定本课题属于哪一种。",
         hours="2 h", when="第 12 周", prio="选读（写方法章时看）"),
    dict(no=9, kind="support", short="IOI Circuit",
         title="Interpretability in the Wild: a Circuit for Indirect Object Identification in GPT-2 small",
         authors="Wang K, Variengien A, Conmy A, et al.",
         venue="ICLR 2023",
         why="「回路（circuit）」概念的标杆工作。任务书要求你明确"
             "「不将头级干预等同于完整回路发现」，读它是为了把这句话讲清楚。",
         read="第 1 节与第 4 节结论；重点是「一个完整回路包含哪些组件与连接」。",
         must="能解释为什么「找到几个重要的头」离「找到一条完整回路」还差很远。",
         hours="2–3 h", when="第 13 周", prio="选读（写局限时看）"),
    dict(no=10, kind="support", short="Transformer Circuits",
         title="A Mathematical Framework for Transformer Circuits",
         authors="Elhage N, Nanda N, Olsson C, et al. (Anthropic)",
         venue="Transformer Circuits Thread, 2021",
         why="残差流、头输出、QK/OV 分解的数学框架，是理解「头在做加法」的最佳材料。",
         read="第 1~2 节：残差流是「信息高速公路」、头往里面写向量。",
         must="能用「残差流 + 头写入」的语言描述你要抑制的那一步操作。",
         hours="3–4 h", when="第 12 周", prio="选读（但对写方法章帮助很大）"),
    dict(no=11, kind="support", short="DFR",
         title="Last Layer Re-Training is Sufficient for Robustness to Spurious Correlations",
         authors="Kirichenko P, Izmailov P, Wilson A G",
         venue="ICLR 2023",
         why="最强的「简单基线」。如果你的方法打不过它，审稿人一定会问。"
             "而且它只需冻住特征、重训最后一层，算力极低，适合本科做对照。",
         read="第 3 节方法（DFR）与实验结果。",
         must="能说清 DFR 做了什么、为什么这么简单却很强；"
              "能解释你的方法与它的定位差异（推理期干预 vs 重训）。",
         hours="2–3 h", when="第 18 周", prio="强烈建议（做对照实验用）"),
    dict(no=12, kind="support", short="JTT",
         title="Just Train Twice: Improving Group Robustness without Training Group Information",
         authors="Liu E Z, Haghgoo B, Chen A S, et al.",
         venue="ICML 2021",
         why="另一种经典去偏基线（两阶段重加权），帮助你把「推理期抑制」放进整个去偏方法谱系里。",
         read="第 3 节方法。",
         must="能画出 JTT 的两阶段流程，说出它和本课题方法的成本差异。",
         hours="1.5–2 h", when="第 18 周", prio="选读"),
    dict(no=13, kind="support", short="Bags-of-Words",
         title="When and Why Vision-Language Models Behave like Bags-of-Words, and What to Do About It",
         authors="Yuksekgonul M, Bianchi F, Kalluri P, et al.",
         venue="ICLR 2023",
         why="CLIP 会「看图里的词」而不是「理解关系」，这正是背景依赖的一种表现，"
             "能帮你把现象提升到机制层面的解释。",
         read="第 2~4 节：属性/关系任务上的失败模式。",
         must="能举一个 CLIP 依赖共现而非语义的例子，并联系到本课题的水鸟-水面。",
         hours="2 h", when="第 19 周", prio="选读"),
    dict(no=14, kind="support", short="CLIP 图文分离",
         title="Disentangling Visual and Written Concepts in CLIP",
         authors="Materzynska J, Torralba A, Bau D",
         venue="CVPR 2022",
         why="直接研究「CLIP 的表示里视觉概念和文字概念怎么纠缠」，"
             "跟「背景 vs 物体」的分解是同一类问题。",
         read="方法部分：如何把表示拆成视觉/文字两个子空间。",
         must="能说出它和 TextSpan 分解思路的异同。",
         hours="2 h", when="第 10 周", prio="选读"),
    dict(no=15, kind="support", short="CLIP-Dissect",
         title="CLIP-Dissect: Automatic Description of Neuron Representations in Deep Neural Networks",
         authors="Oikarinen T, Weng W, Weng W",
         venue="ICLR 2023",
         why="用 CLIP 给神经元自动打标签的思路，可借鉴来给「头」打标签（如「水面头」「鸟头」）。",
         read="第 3 节方法。",
         must="能想到把它的思路迁移到本课题：给 144 个头各自找最相关的中文概念。",
         hours="2 h", when="第 11 周", prio="选读（想加创新点时看）"),
    dict(no=16, kind="support", short="Grad-CAM",
         title="Grad-CAM: Visual Explanations from Deep Networks via Gradient-based Localization",
         authors="Selvaraju R R, Cogswell M, Das A, et al.",
         venue="ICCV 2017",
         why="做背景依赖可视化的最省事工具，第 9 周的诊断图可以直接用它。",
         read="第 3 节方法（很短）。",
         must="能生成一张热力图并解释颜色对应模型的关注区域。",
         hours="1–1.5 h", when="第 9 周", prio="选读（做图必备）"),
]

# ---------------------------------------------------------------- 基础补课模块（用户没学过 ML/PyTorch）
FOUNDATION = [
    dict(mod="A", name="机器学习基本概念", weeks="第 1 周",
         points=["训练集/验证集/测试集的分工，为什么不能拿测试集调参",
                 "过拟合、欠拟合、泛化",
                 "分类任务与准确率；总体准确率为什么会掩盖少数群体的失败",
                 "★ 虚假相关（spurious correlation）：模型靠「捷径特征」而不是真特征做判断",
                 "★ 组鲁棒性 / worst-group accuracy：本课题的核心评价指标"],
         resource="吴恩达《Machine Learning Specialization》第 1 门的前 2 周；"
                  "或李宏毅机器学习 2023 前 4 讲（B 站有）"),
    dict(mod="B", name="深度学习与反向传播", weeks="第 1–2 周",
         points=["神经网络 = 线性层 + 非线性激活的堆叠",
                 "损失函数、梯度下降、反向传播的直觉（会算简单链式法则即可）",
                 "embedding 是什么：为什么一个向量能表示语义",
                 "余弦相似度：CLIP 分类的数学基础"],
         resource="3Blue1Brown 神经网络系列（4 集，可视化极好）；"
                  "李宏毅 2023 第 5–7 讲"),
    dict(mod="C", name="PyTorch 实操", weeks="第 2 周",
         points=["Tensor 的 shape 思维（本课题 90% 的 bug 都是 shape 不对）",
                 "requires_grad / .backward() / torch.no_grad()（冻结模型只需要推理，所以全程 no_grad）",
                 "nn.Module 的 forward 写法",
                 "Dataset / DataLoader 的标准模板",
                 "★★ register_forward_hook：抓取中间层输出（本课题最关键的一个 API）"],
         resource="PyTorch 官方 60 分钟入门 + 官方教程 «Understanding hooks»"),
    dict(mod="D", name="Transformer 与 ViT", weeks="第 3 周",
         points=["自注意力：Q、K、V 各是什么，为什么能建模长程依赖",
                 "多头：把 768 维切成 12 份，每份 64 维，各算各的再拼回来",
                 "残差流：每层输出「加」回主线上，这是能「编辑贡献」的结构基础",
                 "ViT 结构：patch → token → 12 层 → CLS token 作为图像表示",
                 "★ 144 个头 = 12 层 × 12 头，每个头输出 768 维向量"],
         resource="李宏毅 Transformer 系列；ViT 论文第 3 节；"
                  "Jay Alammar «The Illustrated Transformer»"),
    dict(mod="E", name="CLIP 与零样本分类", weeks="第 3 周",
         points=["双塔结构：图像编码器 + 文本编码器",
                 "对比学习：配对样本拉近、非配对推远",
                 "零样本分类：对每个类别构造文本提示，算相似度取最大",
                 "prompt 模板的影响：'a photo of a {class}.' 为什么比单写类别好",
                 "★ 本课题全程冻结参数，不做任何训练，只做前向与干预"],
         resource="CLIP 论文第 2~3 节 + open_clip 官方示例代码"),
]
