# -*- coding: utf-8 -*-
"""plan_spec.py —— 全部文档的唯一数据源（single source of truth）。

任何一处改动（周次、阶段、里程碑、文献、任务）只需要改这里，
00~06 号文档全部从这里读取，保证口径一致。

2026-11-24 重大改版：按新版任务书（双向背景捷径 + 换景对照 + 并集抑制 +
同头数对比 LTC）重排；正式起算日改为 2026-11-24 所在周。
"""
from datetime import date, timedelta

# ---------------------------------------------------------------- 时间锚点
# 新版任务书进度（1）写明 2026-11-24 起算，故 W1 = 2026-11-23（周一）所在周。
# 2026-11-09~11-22 的 ML/PyTorch 基础补课与数据下载视为“预修”，不计入正式 27 周。
ANCHOR = date(2026, 11, 23)
TOTAL_WEEKS = 27


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
# 与新版任务书“进度安排”六段一一对应；边界按整周取整，末尾留 1~3 天缓冲。
PHASES = [
    dict(
        pid="P1",
        name="阶段一",
        weeks=(1, 3),
        title="环境打通 · CLIP 跑通 · 文献与开题",
        taskbook="任务书进度（1）：2026.11.24–12.15",
        goal="从「已补完 ML/PyTorch 基础」到「能跑通 CLIP 零样本推理、读懂 LTC 与"
             "背景捷径评测文献、完成开题与英文翻译」。基础补课已在 2026-11-09~11-23 预修完成，"
             "本阶段不再重复，只补 Transformer/ViT/CLIP 与研究设计。",
        focus="环境、推理、文献、开题四条线并行；W3 末必须完成 M1",
        deliverables=[
            "可运行的 clipbg 环境（S07 自检 PASS）",
            "CLIP ViT-B/16 单图零样本推理跑通，四组标签核对完成",
            "Waterbirds 四组样本统计表",
            "开题报告 + 技术路线图（含水面/陆地两条捷径、换景对照、并集抑制）",
            "《英文文献翻译》（1 篇，中文译文 + 原文对照）",
            "文献笔记 ≥7 篇（任务书 7 篇优先）",
        ],
        milestone="M1 — 开题",
    ),
    dict(
        pid="P2",
        name="阶段二",
        weeks=(4, 6),
        title="基线冻结 · 换景对照 · 背景诊断",
        taskbook="任务书进度（2）：2026.12.16–12.31",
        goal="把 CLIP 在 Waterbirds 上的零样本基线跑准，并构建「同前景换景」对照样本，"
             "用四组准确率、换景分数和背景识别探针把「水面捷径」与「陆地捷径」分别量化出来。",
        focus="基线 → 掩码 → 换景样本 → 换景分数 → 背景识别 → 诊断报告，顺序不能乱",
        deliverables=[
            "四组基线准确率表（总体 / 四组 / 最差组，val + test）",
            "Waterbirds 前景掩码（来自 CUB segmentation）与质量检查记录",
            "同前景换景样本库（水→陆、陆→水两个方向）",
            "换景分数表（两方向：正确类别 margin 变化 + 翻转率）",
            "背景识别探针基线（原图 / 去前景背景图 / 独立场景）",
            "诊断报告（两类误判分别统计 + ≥8 个典型案例）",
        ],
        milestone="M2 — 基线/换景冻结",
    ),
    dict(
        pid="P3",
        name="阶段三",
        weeks=(7, 10),
        title="LTC 复现 · 双向头定位 · 单独/并集抑制",
        taskbook="任务书进度（3）：2027.01.01–01.31",
        goal="复现 LTC 的头级定位与 mean ablation；分别定位水面捷径与陆地捷径的候选头，"
             "记录两组头的重合情况，实现单独抑制、并集联合抑制、LTC 原方案与随机对照，"
             "并在验证集上确定 k 与干预方案。",
        focus="评分 → 分方向选头 → 重合分析 → 抑制实现 → 验证集选方案，五个动作逐个打通",
        deliverables=[
            "LTC 评分/选头复现记录（144 头 direct-effect 表）",
            "水面捷径候选头集合 P_S^water 与陆地捷径候选头集合 P_S^land",
            "LTC 原方案（合并负组）候选头集合 P_S^LTC",
            "两组头重合分析（交集/并集/Jaccard/排序相关）",
            "单独抑制、并集抑制、LTC 原方案、随机抑制四个模块 + 开关自检",
            "验证集选 k 规则与最终干预方案（M3）",
        ],
        milestone="M3 — 干预流水线打通",
    ),
    dict(
        pid="P4",
        name="阶段四",
        weeks=(11, 14),
        title="测试集主实验 · 同头数对比 · 重复实验",
        taskbook="任务书进度（4）：2027.02.01–02.28",
        goal="在独立测试集上比较原模型、水面单独抑制、陆地单独抑制、并集抑制、LTC 原方案、"
             "随机抑制；在相同干预头数下比较并集与 LTC，并报告总体、四组、最差组、"
             "换景分数变化与背景识别结果。",
        focus="六组主实验是主线，换景/背景识别是代价侧，重复实验保证结论可信",
        deliverables=[
            "测试集主结果表（6 组 × 总体/四组/最差组）",
            "同头数对比表（并集 vs LTC 原方案，k 完全一致）",
            "换景分数变化表（两方向，干预前后）",
            "背景识别结果表（原图 / 去前景 / 独立场景）",
            "随机对照 ≥3 seeds 的均值±标准差",
            "阶段性报告（可直接用于中期检查）",
        ],
        milestone="M4 — 主结果冻结",
    ),
    dict(
        pid="P5",
        name="阶段五",
        weeks=(15, 18),
        title="补充消融 · 错配组分析 · 论文初稿",
        taskbook="任务书进度（5）：2027.03.01–03.31",
        goal="补做审稿人会追问的对照（抑制方式、选头策略、提示词），逐个复核两类错配组的"
             "改善与退化，整理图表、失败案例和实验记录，完成论文初稿。",
        focus="实验收口 + 论文成稿；这一阶段的重心是「解释收益与代价」而不是再调参",
        deliverables=[
            "补充消融表（≥3 组：抑制方式 / 选头策略 / 提示词）",
            "两类错配组（landbird-on-water、waterbird-on-land）改善/退化分析",
            "全套图表与失败案例",
            "可复现代码仓库（README + requirements + 一键复现脚本）",
            "论文初稿（全文，含图表）",
        ],
        milestone="M5 — 论文初稿",
    ),
    dict(
        pid="P6",
        name="阶段六",
        weeks=(19, 27),
        title="定稿 · 查重 · 答辩 · 归档",
        taskbook="任务书进度（6）：2027.04.01–05.31",
        goal="按深圳大学撰写规范完成定稿，通过查重与导师审阅，完成答辩并归档全部材料。",
        focus="格式与内容是两条独立战线，不要混在一起改；留足返修与归档时间",
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
    (1, "P1", "环境打通与 CLIP 冒烟测试",
     ["预修复盘：训练/验证/测试、过拟合、虚假相关、最差组准确率（11.09–11.23 已完成）",
      "预修复盘：numpy 数组 / matplotlib 画图（已预修）",
      "预修复盘：nn.Module / Dataset / DataLoader / 加载-前向-算指标（已预修）",
      "预修复盘：autograd / requires_grad / no_grad 原理（已预修）",
      "确认 Anaconda/conda 可用（已预修）",
      "写 .condarc 配清华镜像；新建 clipbg 环境，装 torch cu126 + open_clip，跑 00_check_env.py 到 SELF-CHECK PASS",
      "复习 register_forward_hook：抓 ViT 某层输出并拆成 12 个头",
      "下载 CLIP ViT-B/16 权重，跑通单图零样本推理，打印两类相似度",
      "下载 Waterbirds 官方包并校验 11,788 张图（已预修）",
      "核对 metadata：类别、背景标签、place 列、四组划分"],
     "环境自检 PASS；单图推理输出合理；四组标签核对表"),

    (2, "P1", "ViT/CLIP 精读 + 四组统计",
     ["精读 ViT 第 3 节，画出 224→196+1 token→12 层→768 维的张量流",
      "精读 CLIP 第 2~3.1 节：双塔、余弦相似度、prompt 模板",
      "精读 GroupDRO/Waterbirds：四组划分与 worst-group accuracy",
      "统计 train/val/test 四组样本数并落 csv；核对两方向错配组样本量",
      "确定英文翻译选文并报导师确认"],
     "张量流图；四组统计表；翻译选文确认"),

    (3, "P1", "TextSpan/LTC 精读 + 开题 + M1",
     ["精读 TextSpan：线性分解公式与文本方向投影",
      "精读 LTC：Logit Lens、对比评分、γ 阈值、mean ablation 与 knowledge injection",
      "精读背景捷径评测文献（Wang 2024）：hard/easy 子集与评测逻辑",
      "写开题报告：含两条捷径、换景对照、单独/并集抑制、同头数对比",
      "完成英文翻译与排版；画技术路线图；开题答辩（M1）"],
     "★ M1：开题报告 + 翻译稿 + 路线图三件齐备"),

    (4, "P2", "零样本基线冻结",
     ["写 Dataset：返回图像、类别标签、背景标签、组别（0~3）",
      "实现零样本分类：图像 embedding × 两个类别文本 embedding 的余弦相似度",
      "验证集评测：总体 / 四组 / 最差组",
      "测试集复测，并用独立脚本复算总体准确率（必须一致）"],
     "★ 基线四组 + 最差组数字冻结（val + test）"),

    (5, "P2", "前景掩码与换景样本",
     ["从 CUB-200-2011 segmentation 生成 Waterbirds 前景掩码（与合成图逐像素对齐）",
      "构建「同前景换景」样本：landbird→水面、waterbird→陆地两个方向",
      "换景质量检查：前景像素不变、掩码覆盖率、边缘融合、≥30 张人工目检",
      "计算换景分数：正确类别 margin 变化 + 预测翻转率（分方向）",
      "背景识别探针基线：原图 / 去前景背景图 / 独立场景"],
     "换景样本库 + 两方向换景分数表 + 背景识别基线"),

    (6, "P2", "两类捷径诊断 + M2",
     ["分方向统计误判：landbird-on-water（水面捷径）与 waterbird-on-land（陆地捷径）",
      "做 ≥8 个典型案例拼图：原图 + 真实/预测 + 两类分数",
      "可选：Grad-CAM/注意力图，看模型是否盯着水面/陆地",
      "写诊断报告：两方向差异、换景分数、背景识别基线、数据缺口",
      "向导师汇报 M2，确认 P3 的头定位与并集规则"],
     "★ M2：基线 + 换景 + 背景识别 + 诊断报告"),

    (7, "P3", "LTC 评分复现",
     ["跑通 TextSpan/LTC 的分解与 Logit Lens（先原样 demo，再改本数据）",
      "手推 LTC 式 (5)~(10)：direct effect、正负子组、对比评分、γ 掩码",
      "在本课题数据上算 144 头 direct-effect 表（先合并负组，复现 LTC 口径）",
      "记录样本数、标签、文本提示、γ 取值（任务书要求可追溯）"],
     "144 头评分表（LTC 合并负组口径）+ 复现记录"),

    (8, "P3", "水面捷径头定位",
     ["取 landbird-on-water 负组，按对/错分 NW/NC 子集",
      "计算 spurious 对比分数 σ(V_NW − V_NC)，按 γ 阈值与 top-k 选 P_S^water",
      "画层×头热力图与 Top-k 条形图；换样本重算排序稳定性（Spearman）",
      "与 LTC 论文报告的 Waterbirds 头（如 L10H10）对照，记录异同"],
     "水面捷径候选头集合 + 热力图 + 稳定性记录"),

    (9, "P3", "陆地捷径头定位 + 重合分析",
     ["取 waterbird-on-land 负组，同样流程得 P_S^land",
      "计算 P_S^water 与 P_S^land 的交集、并集、Jaccard、排序相关",
      "画两组头的层/头分布与重叠图；统计「只属于水面」「只属于陆地」「共有」三类",
      "对照 LTC 合并负组集合 P_S^LTC，看拆分是否带来新头"],
     "两组头 + 重合分析表/图 + 与 LTC 集合的差异表"),

    (10, "P3", "抑制实现 + 验证集选方案 + M3",
     ["实现 mean ablation（主）/ 置零 / 缩放；写开关一致性检查",
      "实现单独抑制、并集抑制（去重、按分数截到同 k）、LTC 原方案、随机抑制",
      "验证集扫 k，定规则：并集 vs LTC 用完全相同的 k；单独组也取 top-k",
      "单头/小组体检：抑制前后 logits、准确率、换景分数变化是否合理",
      "★ M3 自检：位置、形状、关闭==基线、只改目标头、no_grad、记录完整"],
     "★ M3：四条抑制链路端到端可跑；验证集方案冻结"),

    (11, "P4", "测试集主实验",
     ["固定验证集选出的 k 与方案，测试集只评测一次",
      "跑 6 组：原模型 / 水面单独 / 陆地单独 / 并集 / LTC 原方案 / 随机",
      "记录总体、四组、最差组；核对并集与 LTC 实际抑制头数完全一致",
      "落 csv：每行含 run_id、k、头集合哈希、种子、耗时"],
     "main_test.csv：6 组 × 四组/最差组齐全"),

    (12, "P4", "换景分数与背景识别复评",
     ["对 6 组干预分别重算两方向换景分数（margin 变化 + 翻转率）",
      "重算背景识别：原图 / 去前景背景图 / 独立场景三个口径",
      "分析收益：哪组最差组提升最大；代价：总体、换景、背景识别各掉多少",
      "把「并集是否同时缓解两类误判」单独列一张分方向表"],
     "换景分数变化表 + 背景识别表 + 分方向收益/代价表"),

    (13, "P4", "随机对照重复实验",
     ["随机抑制重复 ≥3 seeds（同 k、同操作、只换选哪几个头）",
      "报告均值±标准差；与并集、LTC 原方案、两个单独组比较",
      "检查随机组内部波动，判断定向增益是否超过随机波动",
      "记录每个种子的头集合与结果路径"],
     "random_control.csv（≥3 seeds，均值±sd）"),

    (14, "P4", "主结果表 + 可视化 + M4",
     ["填 docs/02 的表 C/D/E（主结果 / 同头数对比 / 分方向）",
      "出主图：6 组柱状、k 曲线、换景分数、头集合重叠、背景识别",
      "写 15 页阶段报告：现象、方法、主结果、收益与代价、卡点",
      "向导师汇报并冻结主实验设置（M4）"],
     "★ M4：主结果冻结，后续不再改数据划分/评分/选参规则"),

    (15, "P5", "补充消融",
     ["消融 1：抑制方式（mean ablation / zero / scale=0.5）",
      "消融 2：选头策略（水面 / 陆地 / 并集 / LTC / 随机 / 按层均匀）",
      "消融 3：提示词敏感性（3 套 prompt 模板）",
      "每组都报告总体/最差组 + 换景分数，回答「结论对设置是否敏感」"],
     "≥3 组消融表"),

    (16, "P5", "两类错配组改善/退化分析",
     ["分别统计 landbird-on-water 与 waterbird-on-land 的改善/退化样本数",
      "检查并集是否同时缓解两类误判，还是只对一类有效",
      "挑失败案例：抑制后由对变错、或两类都变差",
      "把「两类错配组的非对称性」写成分析段落"],
     "分方向改善/退化表 + 失败案例图"),

    (17, "P5", "局限分析 + 代码整理 + 干净复现",
     ["写局限：头级≠回路、单模型/单数据集、换景合成伪影、背景识别口径",
      "整理代码仓库：README、requirements.lock、config、一键复现脚本",
      "新建干净 conda 环境按 README 复现主结果",
      "提交前跑一次数据/结果溯源检查"],
     "可复现代码仓库 + 干净环境复现记录"),

    (18, "P5", "论文初稿 + M5",
     ["第 1~3 章：绪论 / 相关理论 / 方法（含两条捷径与并集设计）",
      "第 4~6 章：实验 / 讨论 / 总结（含换景与背景识别）",
      "图表编号与正文引用对齐；任务书 8 条课程目标逐条找落点",
      "★ M5：全文初稿完成，交导师审阅"],
     "★ M5：论文全文初稿"),

    (19, "P6", "修改润色与查重",
     ["按导师意见逐条修改并留修改记录",
      "统一术语（Transformer / 注意力头 / 虚假相关 / 换景分数）",
      "查重并降重；核对每条参考文献真实可查",
      "格式合规：页边距、字体、图表题注、页码、目录"],
     "修改稿 + 查重报告达标"),

    (20, "P6", "定稿送审",
     ["按深圳大学撰写规范逐项核对（打印检查表打勾）",
      "英文摘要请人润色；附录补代码清单、超参表、完整结果表",
      "核对引文、图表、复现说明三处一致性",
      "★ 提交定稿给导师审阅"],
     "定稿提交；导师审阅意见返回"),

    (21, "P6", "答辩 PPT 与演示脚本",
     ["PPT 结构：背景 2 / 问题 2 / 方法 4 / 结果 6 / 结论 2",
      "准备 3 分钟版和 10 分钟版两个讲法",
      "★ 现场演示脚本：一条命令跑出「原模型 vs 并集抑制」对比",
      "把换景分数、头集合重叠、背景识别三张图放进结果页"],
     "答辩 PPT + 演示脚本"),

    (22, "P6", "预答辩",
     ["找同学当评委，按 12 个预案问题练问答",
      "重点练：为什么拆分两条捷径、并集为什么可能更好、同头数怎么保证公平",
      "按预答辩反馈修 PPT 与讲稿",
      "检查演示在答辩电脑/断网环境下可跑"],
     "预答辩通过；PPT 定稿"),

    (23, "P6", "正式答辩（M6）",
     ["★ 正式答辩",
      "记录评委问题与建议，当天整理成修改清单",
      "确认论文修改范围与截止时间"],
     "★ M6：答辩通过；修改清单成文"),

    (24, "P6", "按意见修改",
     ["按答辩意见逐条修改论文并标注修改位置",
      "补做评委要求的必要对照（若时间允许）",
      "请导师确认修改是否到位"],
     "修改稿 + 导师确认"),

    (25, "P6", "终稿与格式合规",
     ["论文终稿（含中英文摘要、参考文献、致谢、附录）",
      "按学院模板逐项核对格式；打印纸质稿通读一遍",
      "生成提交版 PDF，检查图表清晰度与页码"],
     "论文终稿 + 提交版 PDF"),

    (26, "P6", "成果归档",
     ["按 docs/02 第 9 章清单归档：论文/任务书/开题/翻译/代码/环境/结果/PPT/查重",
      "代码仓库打 tag，导出压缩包；数据与权重单独说明来源",
      "填写学院归档登记表"],
     "归档材料十项齐全"),

    (27, "P6", "复盘、缓冲与投稿草案",
     ["复盘：写下这套流程里最耗时的三件事与三个教训",
      "检查归档是否有遗漏；补交学院要求的额外材料",
      "若导师推荐，整理投稿草案（不占用主线时间）"],
     "复盘记录；全部材料归档完成"),
]

# ---------------------------------------------------------------- 里程碑
MILESTONES = [
    ("M1", "开题", 3, "开题报告通过、技术路线定稿、翻译稿完成"),
    ("M2", "基线/换景冻结", 6, "四组基线 + 换景样本/分数 + 背景识别基线 + 诊断报告"),
    ("M3", "干预打通", 10, "双向头集合 + 重合分析 + 四条抑制链路 + 验证集方案"),
    ("M4", "主结果冻结", 14, "测试集 6 组 + 同头数对比 + 换景/背景识别复评 + 重复实验"),
    ("M5", "论文初稿", 18, "全文初稿 + 图表齐全"),
    ("M6", "答辩", 23, "答辩通过 + 材料归档"),
]

# ---------------------------------------------------------------- 文献
# kind: core=任务书指定/模型骨架必读；support=强相关必读；extra=按需选读
# 1~16 为原清单（编号保持不变，便于旧笔记/进度引用）；17~19 为 2026-11-24 新版任务书新增。
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
         hours="3–4 h", when="第 2 周", prio="必读（模型骨架）"),
    dict(no=2, kind="core", short="CLIP",
         title="Learning Transferable Visual Models from Natural Language Supervision",
         authors="Radford A, Kim J W, Hallacy C, et al.",
         venue="ICML 2021, PMLR 139: 8748-8763",
         why="定义了什么是对比学习、什么是零样本分类，是本课题的模型来源。",
         read="第 2 节（方法）与第 3.1 节（zero-shot 分类与 prompt 模板）；"
              "重点看「图像 embedding 与文本 embedding 做余弦相似度」那一段。",
         must="能解释：为什么 CLIP 没有分类头也能分类？prompt 模板为什么会影响结果？",
         hours="4–5 h", when="第 2 周", prio="必读（任务书）"),
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
         hours="3 h", when="第 2 周", prio="必读（任务书）"),
    dict(no=4, kind="core", short="TextSpan",
         title="Interpreting CLIP's Image Representation via Text-Based Decomposition",
         authors="Gandelsman Y, Efros A A, Steinhardt J",
         venue="ICLR 2024",
         why="本课题方法论的直接来源：把 CLIP 的图像表示按「文本方向」分解到各个组件。",
         read="第 3 节：分解公式（如何把表示写成各组件贡献之和）、第 4 节："
              "如何用分解定位到注意力头；附录里的实现细节。",
         must="能写出分解公式并解释每一项的物理含义；"
              "能说清「为什么可以按文本方向量化某个头对背景的贡献」。",
         hours="6–8 h", when="第 3 周", prio="必读（任务书；翻译首选）"),
    dict(no=5, kind="core", short="LTC",
         title="Locate then Correct: Debiasing Attention Heads in CLIP",
         authors="Yeo W J, Mao R, Abdar M, et al.",
         venue="ICML 2026, PMLR 306: 148640-148677",
         why="本课题要复现的直接对标方法：定位背景相关头并对其做定向校正。",
         read="方法全部：Logit Lens/direct effect、正负子组对比、γ 掩码、"
              "mean ablation 与 knowledge injection；实验设置与消融（尤其 LTC (R)）。",
         must="能把 LTC 的流水线画成 5 个方框，并逐条对照本课题需要复现/改造的部分；"
              "能写出式 (5)~(10) 的评分与选头流程。",
         hours="8–10 h", when="第 3 周", prio="必读（核心对标）"),

    dict(no=6, kind="support", short="Sixteen Heads",
         title="Are Sixteen Heads Really Better than One?",
         authors="Michel P, Levy O, Neubig G",
         venue="NeurIPS 2019",
         why="「剪掉注意力头」这件事的经典起点，教你怎么定义头的重要性并做消融。",
         read="全部（很短）：头重要性的打分方式、逐层/逐头剪枝实验。",
         must="能解释「头冗余」与「头重要性可排序」这两个前提，"
              "并说清它和本课题「抑制背景相关头」的异同。",
         hours="2–3 h", when="第 2 周", prio="强烈建议"),
    dict(no=7, kind="support", short="Voita",
         title="Analyzing Multi-Head Self-Attention: Specialized Heads Do the Heavy Lifting, "
               "the Rest Can Be Pruned",
         authors="Voita E, Talbot D, Moiseev F, et al.",
         venue="ACL 2019",
         why="证明注意力头存在功能分化（有的管句法、有的管位置），"
             "是本课题「背景相关头」假设的理论支撑。",
         read="第 3~4 节：头的功能分类与剪枝顺序。",
         must="能说清「功能特化」是什么意思，为什么它支持「背景依赖可以归因到特定头」。",
         hours="2–3 h", when="第 3 周", prio="强烈建议"),
    dict(no=8, kind="support", short="ROME",
         title="Locating and Editing Factual Associations in GPT",
         authors="Meng K, Bau D, Andonian A, et al.",
         venue="NeurIPS 2022",
         why="「定位后编辑」这一研究范式的代表作，帮助理解"
             "表征贡献编辑与中间激活干预的区别。",
         read="第 2~3 节：怎么定位关键层、怎么写入编辑；只看思路不看细节。",
         must="能说清 activation editing 与 ablation 的区别，"
              "并在论文里用一段话界定本课题属于哪一种。",
         hours="2 h", when="第 10 周", prio="选读（写方法章时看）"),
    dict(no=9, kind="support", short="IOI Circuit",
         title="Interpretability in the Wild: a Circuit for Indirect Object Identification in GPT-2 small",
         authors="Wang K, Variengien A, Conmy A, et al.",
         venue="ICLR 2023",
         why="「回路（circuit）」概念的标杆工作。任务书要求你明确"
             "「不将头级干预等同于完整回路发现」，读它是为了把这句话讲清楚。",
         read="第 1 节与第 4 节结论；重点是「一个完整回路包含哪些组件与连接」。",
         must="能解释为什么「找到几个重要的头」离「找到一条完整回路」还差很远。",
         hours="2–3 h", when="第 10 周", prio="选读（写局限时看）"),
    dict(no=10, kind="support", short="Transformer Circuits",
         title="A Mathematical Framework for Transformer Circuits",
         authors="Elhage N, Nanda N, Olsson C, et al. (Anthropic)",
         venue="Transformer Circuits Thread, 2021",
         why="残差流、头输出、QK/OV 分解的数学框架，是理解「头在做加法」的最佳材料。",
         read="第 1~2 节：残差流是「信息高速公路」、头往里面写向量。",
         must="能用「残差流 + 头写入」的语言描述你要抑制的那一步操作。",
         hours="3–4 h", when="第 9 周", prio="选读（但对写方法章帮助很大）"),
    dict(no=11, kind="support", short="DFR",
         title="Last Layer Re-Training is Sufficient for Robustness to Spurious Correlations",
         authors="Kirichenko P, Izmailov P, Wilson A G",
         venue="ICLR 2023",
         why="最强的「简单基线」。如果你的方法打不过它，审稿人一定会问。"
             "而且它只需冻住特征、重训最后一层，算力极低，适合本科做对照。",
         read="第 3 节方法（DFR）与实验结果。",
         must="能说清 DFR 做了什么、为什么这么简单却很强；"
              "能解释你的方法与它的定位差异（推理期干预 vs 重训）。",
         hours="2–3 h", when="第 15 周", prio="强烈建议（做对照实验用）"),
    dict(no=12, kind="support", short="JTT",
         title="Just Train Twice: Improving Group Robustness without Training Group Information",
         authors="Liu E Z, Haghgoo B, Chen A S, et al.",
         venue="ICML 2021",
         why="另一种经典去偏基线（两阶段重加权），帮助你把「推理期抑制」放进整个去偏方法谱系里。",
         read="第 3 节方法。",
         must="能画出 JTT 的两阶段流程，说出它和本课题方法的成本差异。",
         hours="1.5–2 h", when="第 15 周", prio="选读"),
    dict(no=13, kind="support", short="Bags-of-Words",
         title="When and Why Vision-Language Models Behave like Bags-of-Words, and What to Do About It",
         authors="Yuksekgonul M, Bianchi F, Kalluri P, et al.",
         venue="ICLR 2023",
         why="CLIP 会「看图里的词」而不是「理解关系」，这正是背景依赖的一种表现，"
             "能帮你把现象提升到机制层面的解释。",
         read="第 2~4 节：属性/关系任务上的失败模式。",
         must="能举一个 CLIP 依赖共现而非语义的例子，并联系到本课题的水鸟-水面。",
         hours="2 h", when="第 16 周", prio="选读"),
    dict(no=14, kind="support", short="CLIP 图文分离",
         title="Disentangling Visual and Written Concepts in CLIP",
         authors="Materzynska J, Torralba A, Bau D",
         venue="CVPR 2022",
         why="直接研究「CLIP 的表示里视觉概念和文字概念怎么纠缠」，"
             "跟「背景 vs 物体」的分解是同一类问题。",
         read="方法部分：如何把表示拆成视觉/文字两个子空间。",
         must="能说出它和 TextSpan 分解思路的异同。",
         hours="2 h", when="第 7 周", prio="选读"),
    dict(no=15, kind="support", short="CLIP-Dissect",
         title="CLIP-Dissect: Automatic Description of Neuron Representations in Deep Neural Networks",
         authors="Oikarinen T, Weng W, Weng W",
         venue="ICLR 2023",
         why="用 CLIP 给神经元自动打标签的思路，可借鉴来给「头」打标签（如「水面头」「鸟头」）。",
         read="第 3 节方法。",
         must="能想到把它的思路迁移到本课题：给 144 个头各自找最相关的中文概念。",
         hours="2 h", when="第 8 周", prio="选读（想加创新点时看）"),
    dict(no=16, kind="support", short="Grad-CAM",
         title="Grad-CAM: Visual Explanations from Deep Networks via Gradient-based Localization",
         authors="Selvaraju R R, Cogswell M, Das A, et al.",
         venue="ICCV 2017",
         why="做背景依赖可视化的最省事工具，第 6 周的诊断图可以直接用它。",
         read="第 3 节方法（很短）。",
         must="能生成一张热力图并解释颜色对应模型的关注区域。",
         hours="1–1.5 h", when="第 6 周", prio="选读（做图必备）"),

    dict(no=17, kind="core", short="CLIP 捷径鲁棒性（SoL）",
         title="A Sober Look at the Robustness of CLIPs to Spurious Features",
         authors="Wang Q, Lin Y, Chen Y, et al.",
         venue="NeurIPS 2024, 37. DOI: 10.52202/079017-3893",
         why="任务书新增的背景捷径评测文献；CounterAnimal 的 easy/hard 划分说明"
             "「换一个背景」本身就是检验捷径的核心手段。",
         read="先读摘要、数据集构造（easy/hard 子集）与评测协议；再读结论部分。"
              "重点看它如何区分「背景共现」与「真实类别特征」。",
         must="能说清 hard/easy 子集的含义，并解释为什么本课题需要「同前景换景」对照，"
              "而不是只看四组准确率。",
         hours="3–4 h", when="第 3 周", prio="必读（任务书新增）"),
    dict(no=18, kind="support", short="视觉表征去偏",
         title="Refining Skewed Perceptions in Vision-Language Contrastive Models "
               "through Visual Representations",
         authors="Dai H, Joshi S.",
         venue="ICCV Workshops 2025: 4130–4139",
         why="任务书新增：从视觉表征侧修正 CLIP 偏斜的工作，可作为「表征级干预」对照，"
             "帮助界定本课题「头级干预」的定位。",
         read="摘要、方法图与实验设置；只看它改哪一层表征、用什么监督/标签。",
         must="能说清它与头级 mean ablation 的差异（改整体表征 vs 改局部头），"
              "并说明为什么本课题不采用整体表征编辑。",
         hours="2 h", when="第 15 周", prio="选读（任务书新增）"),
    dict(no=19, kind="support", short="概念区域重要性",
         title="Concept Regions Matter: Benchmarking CLIP with a New Cluster-Importance Approach",
         authors="Agarwal A, Karanam S, Gandhi V.",
         venue="CVPR 2026: 2864–2874",
         why="任务书新增：从「概念区域」角度评测 CLIP 对背景/前景的依赖，"
             "可作为换景与背景识别实验的外部参照。",
         read="摘要、cluster-importance 的定义与评测指标；不必复现其全部实验。",
         must="能说清「区域级重要性」与「头级贡献」是两种粒度，"
              "并解释为什么本课题只声称头级结论。",
         hours="2 h", when="第 16 周", prio="选读（任务书新增）"),
]

# ---------------------------------------------------------------- 基础补课模块（用户没学过 ML/PyTorch）
# 2026-11-09~11-23 已预修完成（LeNet/AlexNet/VGG16 + FashionMNIST、numpy/matplotlib、
# autograd/nn.Module/DataLoader、forward hook 入门）。正式 27 周内只做查漏补缺。
FOUNDATION = [
    dict(mod="A", name="机器学习基本概念", weeks="预修（11.09–11.23）",
         points=["训练集/验证集/测试集的分工，为什么不能拿测试集调参",
                 "过拟合、欠拟合、泛化",
                 "分类任务与准确率；总体准确率为什么会掩盖少数群体的失败",
                 "★ 虚假相关（spurious correlation）：模型靠「捷径特征」而不是真特征做判断",
                 "★ 组鲁棒性 / worst-group accuracy：本课题的核心评价指标"],
         resource="吴恩达《Machine Learning Specialization》第 1 门的前 2 周；"
                  "或李宏毅机器学习 2023 前 4 讲（B 站有）"),
    dict(mod="B", name="深度学习与反向传播", weeks="预修（11.09–11.23）",
         points=["神经网络 = 线性层 + 非线性激活的堆叠",
                 "损失函数、梯度下降、反向传播的直觉（会算简单链式法则即可）",
                 "embedding 是什么：为什么一个向量能表示语义",
                 "余弦相似度：CLIP 分类的数学基础"],
         resource="3Blue1Brown 神经网络系列（4 集，可视化极好）；"
                  "李宏毅 2023 第 5–7 讲"),
    dict(mod="C", name="PyTorch 实操", weeks="预修（11.09–11.23）",
         points=["Tensor 的 shape 思维（本课题 90% 的 bug 都是 shape 不对）",
                 "requires_grad / .backward() / torch.no_grad()（冻结模型只需要推理，所以全程 no_grad）",
                 "nn.Module 的 forward 写法",
                 "Dataset / DataLoader 的标准模板",
                 "★★ register_forward_hook：抓取中间层输出（本课题最关键的一个 API）"],
         resource="PyTorch 官方 60 分钟入门 + 官方教程 «Understanding hooks»"),
    dict(mod="D", name="Transformer 与 ViT", weeks="第 2 周（补）",
         points=["自注意力：Q、K、V 各是什么，为什么能建模长程依赖",
                 "多头：把 768 维切成 12 份，每份 64 维，各算各的再拼回来",
                 "残差流：每层输出「加」回主线上，这是能「编辑贡献」的结构基础",
                 "ViT 结构：patch → token → 12 层 → CLS token 作为图像表示",
                 "★ 144 个头 = 12 层 × 12 头，每个头输出 768 维向量"],
         resource="李宏毅 Transformer 系列；ViT 论文第 3 节；"
                  "Jay Alammar «The Illustrated Transformer»"),
    dict(mod="E", name="CLIP 与零样本分类", weeks="第 2 周（补）",
         points=["双塔结构：图像编码器 + 文本编码器",
                 "对比学习：配对样本拉近、非配对推远",
                 "零样本分类：对每个类别构造文本提示，算相似度取最大",
                 "prompt 模板的影响：'a photo of a {class}.' 为什么比单写类别好",
                 "★ 本课题全程冻结参数，不做任何训练，只做前向与干预"],
         resource="CLIP 论文第 2~3 节 + open_clip 官方示例代码"),
]
