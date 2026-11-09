# -*- coding: utf-8 -*-
"""生成《03_文献阅读清单.docx》。

数据源：plan_spec.LITERATURE（16 篇）/ WEEKS（26 周）/ PHASES（6 阶段）。
排版：全部复用 docx_kit 的函数，不在本文件里自定义样式。
篇幅控制：正文（含封面、图表）目标 8~12 页，因此每节只保留“可执行”的内容。
"""
import os
import re
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import docx_kit as K          # noqa: E402
import plan_spec as S         # noqa: E402

OUT = os.path.join(ROOT, "docs", "03_文献阅读清单.docx")

LIT = {l["no"]: l for l in S.LITERATURE}
CORE = [LIT[i] for i in range(1, 6)]
SUPPORT = [LIT[i] for i in range(6, 17)]          # 11 篇

# ------------------------------------------------------------------ 封面
doc = K.new_doc(header_text="03 文献阅读清单 · Transformer 大模型图像分类中的背景依赖分析与抑制研究")

K.cover(
    doc,
    kicker="深圳大学 · 电子与信息工程学院 · 电子信息工程",
    title="03 文献阅读清单",
    subtitle="Transformer 大模型图像分类中的背景依赖分析与抑制研究",
    metas=[
        ("文档定位", "开题阶段（P1，第 1~6 周）的文献阅读作战手册"),
        ("适用对象", "学过 Python、未学过机器学习与 PyTorch 的本科毕业设计"),
        ("课题一句话", "冻结 CLIP ViT-B/16，在 Waterbirds 上诊断背景依赖，定位并抑制背景相关注意力头"),
        ("数据源", "_build/plan_spec.py：LITERATURE 16 条 / WEEKS 26 周 / PHASES 6 阶段"),
        ("覆盖范围", "核心 5 篇精读指南 + 强相关 11 篇速查 + 检索、笔记、翻译、著录方法"),
        ("版本", "v1.0 · 2026-11-09"),
    ],
    footer_note="本清单文献全部来自 plan_spec.LITERATURE，未新增文献；页码、卷期等信息以数据库原文为准。",
)

# ------------------------------------------------------------------ 术语速查
K.h1(doc, "术语速查：开始读之前先记住这些词")
K.p(doc, "下面 12 个词在后面反复出现，第一次看不懂论文，多半不是公式问题，而是这些词没有白话版解释。"
         "建议先读两遍，读论文时放在旁边。")
K.caption(doc, "表 1  本课题高频术语白话对照", above=True)
K.table(
    doc,
    ["术语", "英文", "一句话白话解释", "为什么本课题离不开它"],
    [
        ["机器学习", "machine learning", "让程序从数据里自己找规律，而不是人把规则写死。",
         "先知道模型“学”什么，才能理解它为什么学歪。"],
        ["训练/验证/测试集", "train/val/test", "分别用来学规律、调参数、最后只考一次的三批数据，不能混用。",
         "调参只碰验证集，测试集只在最后用一次。"],
        ["过拟合 / 虚假相关", "overfitting / spurious correlation", "训练集上背答案，换新题就错；两样东西只是常一起出现，却被当成因果。",
         "背景依赖就是模型背下了“水面→水鸟”这条捷径。"],
        ["组 / 最差组准确率", "group / worst-group accuracy", "按“类别×背景”分成四组分别算准确率，取最低那组当成绩。",
         "总体 95% 而最差组 60%，说明模型靠背景；这是主指标。"],
        ["表征 / embedding", "representation / embedding", "把图或句子压成一串数字（向量），语义相近方向也相近。",
         "CLIP 分类就是在 embedding 空间比方向。"],
        ["余弦相似度", "cosine similarity", "两个向量夹角的余弦，越接近 1 越像。",
         "零样本分类的分数就是它。"],
        ["Transformer / 自注意力", "Transformer / self-attention", "一种靠“注意力”让每个位置去看其他所有位置、按相关程度加权求和的结构。",
         "CLIP 的视觉塔就是 Transformer 的变体 ViT。"],
        ["注意力头", "attention head", "注意力被切成若干份并行计算，每份叫一个头；本课题是 12 层×12 头=144 个。",
         "本课题的干预单位就是“头”。"],
        ["CLS token", "class token", "ViT 在 196 个图像块 token 前额外加的第 197 个 token，输出当作整张图的表示。",
         "hook、打分、干预都围着它转。"],
        ["残差流", "residual stream", "每层输出“加”回主干道的那条总线，注意力头把信息写进去。",
         "抑制一个头 = 让它少写一点某方向的信息。"],
        ["零样本分类", "zero-shot classification", "不训练新分类头，直接用“图片向量 vs 类别文字向量”的相似度分类。",
         "你的基线就是这么来的。"],
        ["前向钩子", "forward hook", "PyTorch 接口，能在某层算完时把输入/输出“截”出来看或改。",
         "抓头输出、做抑制全靠它（第 2 周必学）。"],
    ],
    widths=[2.7, 3.6, 5.7, 4.2],
    font_size=8.3,
    first_col_bold=True,
)

# ------------------------------------------------------------------ 一、总策略
K.h1(doc, "一、阅读总策略：三圈法")
K.p(doc, "16 篇全部精读一轮约 48 小时，而 P1 留给文献的时间只有 40 小时左右，还要同时补 ML/PyTorch 基础、"
         "写开题报告和翻译。所以必须分圈：内圈读到能讲出来，中圈读到能说清方法，外圈知道有什么用即可。"
         "唯一判断标准是——读完能在课题上做出一个具体动作（画图、写公式、跑结果、写进论文某段）。")
K.p(doc, "先读顺序（不能反）：第 3 周文献 6 → 第 4 周文献 1、2 → 第 5 周文献 3、4 → 第 6 周文献 5、7。"
         "文献 5 的评分依赖文献 4 的“文本方向分解”，文献 4 的投影依赖文献 2 的图文相似度；"
         "第 4 篇卡住回第 2 篇 3.1 节，第 5 篇卡住回第 4 篇公式。")
K.hint(doc, "三种读法：精读（逐段读、公式自己推、图自己画，产出 1 页笔记 + 1 张图）用于内圈；"
            "通读（摘要/引言/方法/结论 + 主结果表）用于中圈；跳读（摘要 + 方法图 + 结论）用于外圈。")

K.caption(doc, "表 2  三圈阅读策略", above=True)
K.table(
    doc,
    ["圈层", "包含文献", "读法", "时间", "验收"],
    [
        ["内圈·必读", "文献 1~5（core）", "逐段精读，公式自己推、图自己画，读完立刻写笔记",
         "25~30 h\nW4~W6", "合上论文能白板讲 3 分钟，答出第二章全部问题"],
        ["中圈·优先", "文献 6、7、11（prio=强烈建议）", "通读全文 + 精读方法节，抄下可复用公式",
         "7~9 h\nW3/W6/W18", "能说清对应流程哪一步，并写出 1 个可复用做法"],
        ["外圈·按需", "文献 8~10、12~16（8 篇）", "先读摘要+方法图+结论，用到哪节再读哪节",
         "每篇 ≤2 h", "30 秒内能定位“该翻哪一篇哪一节”"],
    ],
    widths=[2.3, 4.5, 5.0, 2.0, 4.9],
    font_size=8.8,
    first_col_bold=True,
)

K.h2(doc, "读到什么程度算够（三种读法的产出）")
K.bullet(doc, "内圈：能不看论文讲清“问题—方法—结论—与我的关系”，并答出第二章列出的问题。")
K.bullet(doc, "中圈：能说出它解决了流程里的哪一步，并写出 1 个可复用公式或 1 条实验设置。")
K.bullet(doc, "外圈：能 30 秒内定位到具体小节，不要求记住数字。")
K.bullet(doc, "通用：每篇都有笔记（模板见第七章），笔记里至少 3 条“对我的课题有什么用”。")
K.callout(
    doc,
    "一句话验收",
    ["合上论文，用 3 分钟向不懂机器学习的同学讲清楚：这篇解决什么问题、用了什么招、结论是什么、"
     "和你的水鸟-水面课题有什么关系。讲不清就是没读到位。"],
    kind="ok",
)

K.h2(doc, "止损规则（读不下去时怎么办）")
K.num(doc, 1, "时间止损：单篇超过预计工时 1.5 倍就先停，把问题记进笔记，去做实验，带着问题回读第二遍。")
K.num(doc, 2, "难度止损：公式卡住先跳过推导，只记“输入什么、输出什么、干什么用”，复现时再回来推。")
K.num(doc, 3, "真实性止损：要写进论文的文献必须能在数据库查到原文，查不到的不用；第 22 周统一核查。")

# ------------------------------------------------------------------ 二、核心 5 篇
K.h1(doc, "二、核心文献 5 篇：逐篇精读指南")
K.p(doc, "5 篇是任务书指定必读，也是论文“研究现状 + 方法”两章的主要来源。每篇按“为什么读 → 重点节 → "
         "必须能回答 → 验收动作 → 读不懂怎么办”展开；问题答不上来，不要开始下一篇。")

K.caption(doc, "表 3  核心文献总览（编号与 plan_spec.LITERATURE 一致）", above=True)
K.table(
    doc,
    ["编号", "简称", "读它对本课题有什么用", "重点读哪几节", "读完必须能回答", "工时/周次"],
    [[str(l["no"]), l["short"], l["why"], l["read"], l["must"], f"{l['hours']}\n{l['when']}"]
     for l in CORE],
    widths=[1.0, 2.0, 4.3, 3.7, 3.6, 1.6],
    font_size=8.0,
    first_col_bold=True,
    align=["c", "l", "l", "l", "l", "c"],
)

CORE_DETAIL = {
    1: dict(
        role="本课题的模型骨架：CLIP 的视觉编码器就是 ViT-B/16，要 hook、打分、抑制的 144 个头全部来自这篇的结构。"
             "读它不是学训练，而是写代码时知道每个张量是什么形状、在第几层、对应哪个头。",
        sections=[
            "第 3 节方法整节精读，边读边画：224×224×3 → 切 16×16 块 → 196 个 token → 加 CLS 变 197 → 12 层 → 取 CLS 的 768 维。",
            "patch embedding：为什么用 kernel=16、stride=16 的卷积实现“切块+线性投影”；位置编码为什么必须加、加在哪。",
            "多头自注意力：768 维怎么切成 12 个 64 维的头，Q/K/V 形状，多头的输出怎么拼回 768。",
            "表 1 找到 B/16 那一行，确认 12 层、12 头、768 维、patch=16 四个数。",
        ],
        questions=[
            "patch=16 时序列长度为什么是 196？加 CLS 后 197 里的“+1”是什么？768 维是 patch 展开的还是投影输出的？",
            "第 l 层第 h 个头的输入、输出各是什么形状？它输出的 64 维最后去了哪里？",
            "为什么说“12 层×12 头=144 个头”而不是“12 个模型”？层和头是什么关系？",
            "CLIP 的视觉塔与本篇 ViT-B/16 是同一结构吗？CLIP 改了哪里？",
            "在 PyTorch 里 hook 挂在哪个模块上能拿到“某层所有头拼接后的输出”？怎么拆成单个头？",
        ],
        verify="不看论文画出张量流并标出每步 shape，写出 144=12×12 的来源，贴进 Zotero 笔记——这张图就是第 5 周技术路线图“模型”栏的底稿。",
        fallback="先看李宏毅 Transformer 或《The Illustrated Transformer》建立直觉，再回读第 3 节；公式第一遍不懂没关系，先弄对形状和流程。",
    ),
    2: dict(
        role="模型来源，也是“零样本分类”的定义出处。你不训练、只做前向，但要能解释：没有分类头为什么能分类，"
             "以及为什么换个 prompt 模板结果就变——后者说明判断依赖图文共现，正是背景依赖的入口。",
        sections=[
            "第 2 节：双塔结构、对比学习目标（配对图文拉近、不配对推远）、温度系数 τ 的作用。",
            "第 3.1 节：图像与类别文本 embedding 算余弦相似度 → 乘温度 → softmax → 取最大。",
            "prompt 模板段：'a photo of a {class}.' 为什么比只写类名好；论文试了多少模板、结论是什么。",
            "第 2.3 节可跳读，但看清它和“冻结特征只做线性探针”的关系（第 11 篇 DFR 会用到）。",
        ],
        questions=[
            "CLIP 训练时优化什么？正样本对、负样本对怎么构造？",
            "零样本分类从一张图到两个类别概率，中间每一步在做什么？",
            "为什么套句子模板会提升准确率？模板不同结果不同，说明模型在利用什么信息？",
            "把 'a photo of a waterbird' 换成 'a photo of a bird on water'，预测会怎么变？这和背景依赖什么关系？",
            "图文相似度可以看成“图像表示在文本方向上的投影”吗？TextSpan 正从这里出发。",
        ],
        verify="用三套 prompt 模板在同一批样本上各跑一遍，记录准确率差异写成一页笔记——这就是第 18 周消融 3 的雏形。",
        fallback="对照 open_clip 官方 zero-shot 示例代码读 3.1 节，论文那一节在代码里只有二十几行；公式可跳过。",
    ),
    3: dict(
        role="Waterbirds 数据集就是这篇提出的，worst-group accuracy 也是这篇定义的。没有它，你的“四组准确率”和"
             "“最差组”就是没有出处的指标；开题的国内外研究现状里，它是去偏/组鲁棒性这条线的起点。",
        sections=[
            "第 3 节数据集：Waterbirds 怎么构造（CUB 鸟图贴到 COCO 背景）、组怎么由“鸟类别×背景类型”交叉得到、为什么是 group shift。",
            "worst-group accuracy 的定义与计算：先算每组准确率，再取最小值。",
            "第 4 节实验设置：训练/验证/测试的组分布为什么故意不平衡，验证集与测试集组比例怎么设。",
            "摘要与引言中“平均准确率掩盖少数失败”的论证，可直接改写成论文第 1 章动机段。",
        ],
        questions=[
            "四组分别是什么？训练集里哪组最少，为什么最少的那组最容易垮？",
            "worst-group accuracy 与普通 accuracy 公式差在哪？为什么总体 95% 仍可能是坏模型？",
            "group shift、spurious correlation、分布外泛化在这篇里是什么关系？",
            "验证集与测试集的组比例为什么不同？这对“用验证集选 k”意味着什么风险？",
            "为什么本课题必须报告四组而不是只报总体？对应任务书哪条要求？",
        ],
        verify="合上论文默写四组划分和 worst-group 计算步骤，再用一句话向同学解释“为什么总体准确率高不代表模型好”——这句话直接进开题报告。",
        fallback="数据集细节多，先看第 3 节图 1 和表 1；worst-group 不清楚就对照 02 号文档的四组统计表模板，用数字理解更快。",
    ),
    4: dict(
        role="本课题方法论的直接来源：它把 CLIP 的图像表示拆成“各组件（含注意力头）沿各文本方向的贡献之和”，"
             "这是给 144 个头打分的数学基础，也是英文翻译首选。这篇读不通，第 10~11 周的评分代码就写不出来。",
        sections=[
            "第 2 节：把 CLS 表示写成“各层各头输出+MLP+残差”的加和形式，注意 LayerNorm 的非线性怎么处理（全文最绕）。",
            "第 3 节：分解公式与“投影到文本方向”的定义；每个组件对某文本概念的贡献怎么算。",
            "第 4 节：如何由分解定位到具体头，以及“头—概念”对应案例。",
            "附录：CLS 的 bias 怎么处理、用哪些文本方向、归一化怎么做、样本量——复现按附录，不要自己猜。",
        ],
        questions=[
            "把 CLS 最终表示写成“若干项之和”的公式是什么？每项对应哪个组件？",
            "“投影到文本方向”是内积还是余弦？为什么这个值可以当作贡献？只看向量在某方向的分量为什么不丢信息？",
            "从分解结果到“第 l 层第 h 个头对背景概念的贡献”要经过哪几步？",
            "贡献值有正负号吗？负值什么意思？排序按绝对值还是原值？",
            "论文用什么指标验证分解可信？我至少要复用哪一条验证？只算“背景 vs 鸟”两个方向时最少要改哪些代码？",
        ],
        verify="写出分解公式并逐项标注含义；用本课题数据跑一次最小复现，输出 144 头 × “水面”方向的贡献值存 csv（第 11 周评分表雏形）。",
        fallback="先看第 4 节案例图建立“头—概念”直觉，再啃第 2~3 节；LayerNorm 段第一遍可跳过，照附录跑通后再回读。",
    ),
    5: dict(
        role="要复现的直接对标方法：定位背景相关头，再做定向校正。它是你的参照系——评分、选头、抑制流程应能逐条对上它的步骤；"
             "写论文时，你的差异（评分口径、抑制方式、对照设计）要说得清。",
        sections=[
            "方法整节：头级评分怎么定义（用什么量衡量“这个头与背景有关”）、按什么排序、k 怎么选。",
            "“校正”作用在哪：改残差流里的贡献项（表征贡献编辑），还是把头输出置零/缩放（中间激活消融）？任务书要求写清这个区别。",
            "实验设置：数据集、backbone、基线、指标、对照实验怎么设计；消融里哪些设计必要、哪些可简化。",
        ],
        questions=[
            "完整流水线能画成哪 5 个方框？每个方框的输入输出是什么？",
            "头级评分公式是什么？和“头输出在背景文本方向上的投影”是同一个东西吗？",
            "选头是全局 Top-k 还是每层取若干？k 在验证集上选吗？",
            "抑制/校正具体改哪个张量？改完是否要重新归一化？会不会影响后面的层？",
            "它和随机抑制怎么对照？几个随机种子、报告什么统计量？复现时哪些部分可以砍掉、论文里怎么说明？",
        ],
        verify="把流水线画成 5 个方框，右侧并排写“本课题对应环节”和“差异点”，这张对照表直接进技术路线页；再列出第 10~13 周的最小代码清单（评分/选头/抑制/对照四个脚本）。",
        fallback="先读摘要+方法开头+实验设置，把五步流程搞清；公式卡住就先读第 4 篇——LTC 的评分建立在 TextSpan 分解之上。",
    ),
}

for idx, item in enumerate(CORE, start=1):
    d = CORE_DETAIL[item["no"]]
    K.h2(doc, f"2.{idx} 文献 {item['no']} · {item['short']}（{item['when']}，{item['hours']}）")
    K.rich(doc, [
        ("题目：", {"b": True}), (item["title"], {}),
        ("；出处：", {"b": True}), (item["venue"], {}),
    ], indent=False, space_after=2)
    K.p(doc, d["role"])
    K.h3(doc, "读完必须能回答（答不上就是没读懂）")
    for qi, q in enumerate(d["questions"], start=1):
        K.num(doc, qi, q)
    K.p(doc, "验收动作：" + d["verify"])
# ------------------------------------------------------------------ 三、强相关 11 篇
K.h1(doc, "三、强相关文献 11 篇：分区快速消化")
K.p(doc, "plan_spec 中 kind=support 共 11 篇（任务书按 10 篇做的预算，数据源实为 11 篇）。本清单不删减："
         "prio=强烈建议 的 3 篇（文献 6、7、11）属第二圈必读，其余 8 篇第三圈按需。"
         "这 11 篇不要求推导，价值是给假设找依据、给方法找祖先、给实验找对照、给论文找“相关工作”的写法。")

K.caption(doc, "表 4  强相关文献速查（按编号排序，非阅读顺序）", above=True)
K.table(
    doc,
    ["编号", "简称", "本次阅读的作用", "重点读", "读完必须能回答", "工时/周次"],
    [[str(l["no"]), l["short"], l["why"], l["read"], l["must"], f"{l['hours']}\n{l['when']}"]
     for l in SUPPORT],
    widths=[1.0, 1.9, 4.1, 3.7, 3.8, 1.7],
    font_size=7.9,
    first_col_bold=True,
    align=["c", "l", "l", "l", "l", "c"],
)

K.h2(doc, "四组怎么串起来读")
K.bullet(doc, [("头与剪枝（6、7）：", {"b": True}),
               ("解决同一个前提——头能不能按重要性排序、能不能单独关掉。第 6 篇给可操作的头重要性打分与剪枝流程，是“抑制头”的方法祖先；"
                "第 7 篇证明头确实功能分化，为“存在背景相关头”提供依据。把它们的评分抄下来和 TextSpan、LTC 对照，差别只在“用什么量衡量重要性”。", {})])
K.bullet(doc, [("定位、编辑与回路（8、9、10）：", {"b": True}),
               ("第 8 篇帮你分清 activation editing（改激活）与 ablation（关掉），任务书要求界定的“本课题属于哪种”依据就在这里；"
                "第 9 篇让你有底气写“只做头级归因，不等同于完整回路发现”；第 10 篇提供“残差流+头写入”的语言，"
                "“抑制=把该头写入残差流的向量按系数缩小”最准确的出处就是它。", {})])
K.bullet(doc, [("基线与机制（11~16）：", {"b": True}),
               ("第 11 篇 DFR 只冻特征、重训最后一层，是最简单却很强的对照，算力极低，建议第 18 周补一组；第 12 篇 JTT 用来把“推理期干预”"
                "放进“训练期去偏”谱系。第 13 篇讲 CLIP 像“词袋”依赖共现，可把“水面→水鸟”提升到机制解释；第 14 篇拆视觉/文字子空间，"
                "和 TextSpan 同源；第 15 篇可借鉴给 144 个头各找一个中文概念；第 16 篇 Grad-CAM 是第 9 周做图最省事的工具。", {})])
K.hint(doc, "按需触发速查：画诊断图翻 16；写干预类型区别翻 8；写局限“不是完整回路”翻 9；解释“改残差流写入”翻 10；"
            "补简单基线翻 11；写方法谱系翻 12；给头打标签翻 15；解释 CLIP 依赖共现翻 13。")

# ------------------------------------------------------------------ 四、时间轴
K.h1(doc, "四、建议阅读顺序时间轴（第 1~26 周）")
K.p(doc, "阅读分三波：第一波 W3~W6 打地基（6 → 1 → 2 → 3 → 4 → 5 → 7，与补基础、开题并行，M1 前五篇核心读完）；"
         "第二波 W9~W13 边做边读（16 → 14 → 15 → 8/10 → 9，服务做图、分解、评分、干预）；"
         "第三波 W18~W19 对照与解释（11 → 12 → 13，服务论文第 4、5 章）。")

K.h2(doc, "逐周安排")
K.p(doc, "下表与 01 号文档 WEEKS 完全对齐。没有文献的周不是放假，而是把前面的笔记读薄、把时间投给实验；"
         "需要时按上文“按需触发速查”定向回读。")

WEEK_READ = {
    3: [6], 4: [1, 2], 5: [3, 4], 6: [5, 7],
    9: [16], 10: [14], 11: [15], 12: [8, 10], 13: [9],
    18: [11, 12], 19: [13],
}
WEEK_DEPTH = {
    1: "不读论文：过术语表，看基础视频，把“虚假相关”用自己的话写 3 句。",
    2: "不读论文：补 PyTorch，跑通 register_forward_hook（后面所有干预靠它）。",
    3: "通读全文（很短），抄下头重要性评分公式。",
    4: "精读：2 篇笔记 + ViT 张量流图 + 三套 prompt 对比。",
    5: "精读：默写四组划分；写出 TextSpan 分解公式。",
    6: "精读 LTC：画 5 步流水线；Voita 只读功能特化结论。",
    7: "不新增：搭数据管线；组划分疑问回读第 3 篇第 3 节。",
    8: "不新增：跑基线；对照 CLIP 3.1 节检查温度系数。",
    9: "精读 Grad-CAM 第 3 节（一页）；产出 ≥8 张诊断图。",
    10: "通读方法；写 200 字说明它与 TextSpan 的异同。",
    11: "跳读方法；列出“给 144 个头打概念标签”的步骤。",
    12: "ROME 只看定位+编辑思路；Circuits 读 1~2 节练“残差流”表达。",
    13: "读 IOI 引言与结论；写“头级干预≠完整回路”说明段。",
    14: "不新增：k 扫描（验证集）。",
    15: "不新增：测试集复评与重复实验。",
    16: "不新增：可视化与案例分析。",
    17: "不新增：阶段报告；定向回读第 4、5 篇。",
    18: "DFR 精读方法+结果，判断能否加对照；JTT 看两阶段流程。",
    19: "读 Bags-of-Words 失败模式，写进论文讨论节。",
    20: "写作周：只回查不新读；第 1 章引用每篇都要有笔记。",
    21: "写作周：引用与列表对齐，补页码/DOI。",
    22: "不新读：核对 16 篇真实性（每篇都能查到）。",
    23: "不新读：按学校模板统一格式。",
    24: "不新读：PPT 用文献图时标注出处。",
    25: "不新读：按评委问题回读补解释。",
    26: "不新读：归档笔记与 PDF。",
}

rows = []
for w, pid, theme, tasks, check in S.WEEKS:
    lits = WEEK_READ.get(w, [])
    read_txt = "\n".join(f"{n} {LIT[n]['short']}" for n in lits) if lits else "—"
    rows.append([f"W{w}", S.week_dates(w), pid, read_txt, WEEK_DEPTH[w]])

K.caption(doc, "表 5  逐周阅读安排（日期为计划日期，随实际进度顺延）", above=True)
K.table(
    doc,
    ["周", "日期", "阶段", "读什么（文献编号+简称）", "读到什么程度 / 与实验的衔接"],
    rows,
    widths=[1.1, 2.5, 1.2, 4.4, 7.0],
    font_size=7.9,
    first_col_bold=True,
    align=["c", "c", "c", "l", "l"],
)

K.p(doc, "里程碑对应：M1（W6）5 篇核心读完、6/7 至少通读；“研究现状”每段有出处。M2（W9）用 16 做 ≥8 张诊断图。"
         "M3（W13）4、5、8、9、10 已消化，能写出两种干预方式的区别。M5（W21）16 篇全部入笔记、列表与引用对应；"
         "M6（W25）能回答“为什么不用 DFR/JTT”。")

# ------------------------------------------------------------------ 五、英文翻译
K.h1(doc, "五、英文文献翻译")
K.p(doc, "英文翻译是任务书课程目标 1 的交付物，也是开题材料。它不是“找篇英文翻一下”，而是“把方法路上最难的一篇读懂并用自己的话重构一遍”。"
         "选文选错，后面全是白工。")

K.caption(doc, "表 6  翻译选文候选（均来自 LITERATURE）", above=True)
K.table(
    doc,
    ["优先级", "文献与建议章节", "为什么适合", "主要难点"],
    [
        ["首选", "文献 4 TextSpan\n第 2~3 节 + 第 4 节开头",
         "与课题方法一一对应：翻完等于把“分解公式、文本方向、头级贡献”整套术语表建好，方法章直接受益。",
         "LayerNorm 处理与“投影”叙述绕、长句多；公式要用公式编辑器逐项核对。"],
        ["备选一", "文献 6 Sixteen Heads\n第 2~4 节",
         "全文很短、概念清晰，头重要性评分可直接用于本课题；工作量可控，适合时间紧。",
         "实验数字多需核对；不能只译方法，篇幅会不足。"],
        ["备选二", "文献 5 LTC\n方法整节 + 实验设置",
         "与课题对标最直接，翻它的方法节相当于提前写自己方法章的框架。",
         "符号密集，τ、k、头索引易混；先确认能拿到官方全文。"],
    ],
    widths=[1.5, 4.2, 5.6, 4.9],
    font_size=8.5,
    first_col_bold=True,
    align=["c", "l", "l", "l"],
)
K.hint(doc, "不推荐 1（ViT）或 2（CLIP）：篇幅长、偏背景，翻完对方法章帮助不如上面三篇。若导师指定，以导师意见为准。"
            "下载优先官方来源：ICLR→OpenReview，ICML→PMLR，NeurIPS→Proceedings，CVPR/ICCV→CVF；不要用来路不明的转载 PDF。")

K.h2(doc, "选文标准（缺一不可）")
K.num(doc, 1, "与课题方法核心直接相关（评分/定位/抑制），不是泛泛的背景综述。")
K.num(doc, 2, "有公式或流程图，翻译后能沉淀成本课题的术语表和公式来源。")
K.num(doc, 3, "正文 4~8 页、结构清晰，总翻译量约 6000~9000 字，一个月内能完成。")
K.num(doc, 4, "能拿到含清晰公式与图表的官方 PDF，不能只有摘要页。")
K.num(doc, 5, "你至少能读懂 80%——读不懂只能机翻，语句必不通，必被扣分。")
K.num(doc, 6, "动笔前给导师确认选文与章节，避免翻完被否。")

K.h2(doc, "翻译质量要求")
K.bullet(doc, "先建术语表：attention head、residual stream、spurious correlation、worst-group accuracy、zero-shot 等定死译法，全文一致（表 1 可当底稿）。")
K.bullet(doc, "忠实优先：不漏句、不合并段落、不改因果与限定词；may / might / suggests 的语气要译出来。")
K.bullet(doc, "中文要像中文：长句拆短、被动改主动；但公式、变量名、缩写（CLIP、ViT、CLS）保留原文。")
K.bullet(doc, "公式与图表：用公式编辑器重排，编号与原文一致；图题、表题、表头、图注必须译，图内英文可在图注说明。")
K.bullet(doc, "数字照抄：百分比、±、p 值、数据集规模不要“顺手改成整数”；专有名词首次出现给中英对照。")
K.bullet(doc, "不得整段机翻后只改几个词：学院会看语句是否通顺、术语是否统一，这是最常见的扣分点。")

K.h2(doc, "排版格式")
K.p(doc, "封面写全：题目、作者、出处（会议/年份）、译者、学号、指导教师。正文用“原文段 + 译文段”上下对照，"
         "原文与译文各自从 [1]、【1】 开始编号并一一对应；若学院模板要求左右对照，改成两栏表格。"
         "中文宋体小四、英文 Times New Roman 小四、1.5 倍行距、页边距 2.5 cm、页脚居中页码；"
         "公式用公式编辑器重排，编号与原文一致；交付前打印模板逐项打勾。")

K.h2(doc, "常见扣分点（逐条自查）")
K.bullet(doc, "术语不一致：同一个 head 一会儿“头”一会儿“注意力头”——先做术语表，定稿前全文替换。")
K.bullet(doc, "漏译/跳段：漏掉限定条件和否定句——按段落编号逐段勾选，原文与译文段数必须相同。")
K.bullet(doc, "机翻痕迹：长定语套娃、语序生硬——译完朗读一遍，读不通就重写。")
K.bullet(doc, "公式错乱、图表题注未译：用公式编辑器重排并核对编号；图表单独列检查表逐张核对。")
K.bullet(doc, "出处标注缺失：只写篇名没写会议/年份/页码——封面与页脚都标全。")
K.bullet(doc, "篇幅不足（只译摘要和引言）或格式不符模板——选文时按“方法与实验”节选，交前打印模板逐项打勾。")

# ------------------------------------------------------------------ 六、检索方法
K.h1(doc, "六、文献检索方法")
K.p(doc, "本清单 16 篇是起点。开题要写“国内外研究现状”，你可能还要补 3~5 篇。补充时只检索真实文献，"
         "并把关键词、数据库、检索式记进笔记，方便复核。")

K.caption(doc, "表 7  检索关键词中英文对照", above=True)
K.table(
    doc,
    ["中文", "英文", "用途"],
    [
        ["虚假相关", "spurious correlation", "核心词，命中去偏理论"],
        ["捷径学习", "shortcut learning", "找“模型走捷径”的机制解释"],
        ["背景偏差/背景依赖", "background bias / background reliance", "直接命中题目"],
        ["组鲁棒性", "group robustness", "去偏方向总标签"],
        ["最差组准确率", "worst-group accuracy", "精确定位评价指标"],
        ["组偏移/分布偏移", "group shift / distribution shift", "找 Waterbirds 这类设置"],
        ["去偏", "debiasing", "方法类，结果多，按被引筛"],
        ["注意力头", "attention head", "干预对象"],
        ["注意力头剪枝", "attention head pruning", "文献 6 同类工作"],
        ["机制可解释性", "mechanistic interpretability", "“定位+编辑”范式"],
        ["表征编辑/激活编辑", "representation editing / activation editing", "文献 8 路线"],
        ["视觉-语言模型", "vision-language model (VLM)", "CLIP 所属大类"],
        ["文本分解", "text-based decomposition", "文献 4 精确词"],
        ["提示词/模板", "prompt / prompt template", "第 18 周消融 3"],
    ],
    widths=[3.8, 7.4, 5.0],
    font_size=8.1,
    first_col_bold=True,
)

K.h2(doc, "数据库与工具")
K.bullet(doc, [("找论文：", {"b": True}),
               ("Google Scholar（跨库、看被引）、DBLP（按会议/作者精确检索、确认真实性）、Semantic Scholar / Connected Papers（滚雪球）。", {})])
K.bullet(doc, [("拿全文：", {"b": True}),
               ("arXiv（最新预印本，未经评审要打折）、OpenReview（ICLR/NeurIPS 全文与审稿意见）、PMLR / NeurIPS Proceedings（ICML/NeurIPS 官方 PDF）、"
                "CVF Open Access（CVPR/ICCV）；IEEE Xplore / Web of Science 从学校图书馆入口进。", {})])
K.bullet(doc, [("写论文：", {"b": True}),
               ("Papers with Code 找官方代码（有代码的优先精读）；CNKI / 万方看中文术语与开题格式；Zotero 管文献与引用。", {})])

K.h2(doc, "检索式示例与初筛方法")
K.code_block(doc, """# Google Scholar / Semantic Scholar
("background bias" OR "spurious correlation" OR "shortcut learning")
  AND ("vision transformer" OR "CLIP" OR "vision-language model")
"attention head" AND ("pruning" OR "ablation" OR "importance" OR "editing")
"text-based decomposition" AND "CLIP"
"Waterbirds" AND "worst-group accuracy"

# arXiv：ti（标题）/ abs（摘要）字段
ti:"background" AND abs:"spurious correlation" AND abs:"CLIP"

# CNKI（主题）
主题 = 虚假相关 AND 主题 = 深度学习""", size=8.0)
K.p(doc, "搜到几十上百篇时不要从头读。用下面五项各花 30~60 秒初筛，四项通过就进入待读，两项以下直接放掉：")
K.num(doc, 1, "标题+摘要+方法图：30 秒内能否说清它解决什么问题、对应我流程哪一步；完全看不懂先放。")
K.num(doc, 2, "是否有官方代码：有 → 优先级提高（本课题要复现）。")
K.num(doc, 3, "被引与年份：近三年被引多或奠基性老文 → 值得读；孤立低被引新文 → 先放。")
K.num(doc, 4, "实验设置：数据集/backbone 与 CLIP ViT-B/16 + Waterbirds 越接近越值得读。")

# ------------------------------------------------------------------ 七、笔记模板
K.h1(doc, "七、阅读笔记模板与 Zotero 使用")
K.p(doc, "笔记不是抄论文，而是“把论文压缩成能直接用的东西”。统一模板的价值：写论文时按标题找，三分钟就能把某篇内容搬进正文。")

K.h2(doc, "阅读笔记模板（Markdown，直接复制）")
K.code_block(doc, """# 文献笔记 · {编号} {中文简称}
## 0 元信息
- 题目 / 作者 / 出处 / 年份：
- 类型：核心 / 强相关 / 按需
- 阅读日期 / 实际用时：
- 对应周次 / 里程碑：
## 1 它解决什么问题（3 句话以内）
## 2 方法（不看原文，用自己的话写）
- 输入：
- 核心操作：
- 输出：
- 关键公式（抄下来，逐个标注符号含义）：
## 3 实验与结论
- 数据集 / backbone：
- 指标：
- 主要数字（总体 / 最差组）：
- 作者声称的结论：
## 4 对我的课题有什么用（至少 3 条，必填）
- 可直接复用的：
- 需要改造的：
- 可以写进论文第几章第几节：
## 5 我没读懂的地方（列问题，不要留空）
## 6 下一步动作（可复现 / 可验证）
## 7 引用信息
- GB/T 7714：
- BibTeX key：""", size=8.2)

K.h2(doc, "目录命名与 Zotero 建议")
K.p(doc, "工作目录建议分四层：01_core / 02_support / 03_on_demand / 99_translation，另加一个“文献笔记汇总.md”做索引。"
         "文件名统一为“编号_简称_年份_读法.md”（如 04_TextSpan_2024_精读笔记.md）；译文用 v1/v2/final 版本号，旧版移到 _old/ 不覆盖；"
         "每周日压缩一份带日期（YYYYMMDD）的备份放网盘。")
K.num(doc, 1, "装 Zotero 7 + 浏览器插件，在 Google Scholar / arXiv 一键入库，PDF 拖进条目自动挂附件。")
K.num(doc, 2, "建 3 个 collection：core（5 篇）、support（11 篇）、reading-log（按周记录读了什么）。")
K.num(doc, 3, "装 Better BibTeX，citation key 设为“作者+年份+简称”（如 gandelsman2024textspan），导出 .bib 给论文用。")
K.num(doc, 4, "每篇加三类标签：kind（core/support）、topic（head/debias/vlm）、status（未读/在读/已精读）。")
K.num(doc, 5, "笔记写成 child note，标题直接套上面的 7 个一级标题；每周日导出 Markdown 备份并发给导师看。")
K.num(doc, 6, "写论文时用 Zotero 的 Word 插件插入引用，样式选 GB/T 7714-2015，避免手抄出错。")

# ------------------------------------------------------------------ 八、参考文献格式
K.h1(doc, "八、参考文献格式规范")
K.p(doc, "深圳大学毕业设计撰写规范要求参考文献按 GB/T 7714-2015 著录、中英文分列、全文统一。"
         "任务书未单独规定英文条目写法，最终以学院最新模板为准；下面给出两种常见写法，选定一种后全文统一，不要混用。")
K.p(doc, "常用类型标识：会议论文 [C]（作者. 题名[C]//会议名. 出版地: 出版者, 年: 页码.）；期刊 [J]；"
         "网络资源 [EB/OL]（作者. 题名[EB/OL]. (发布日期)[引用日期]. URL.，文献 10 属于此类）；"
         "学位论文 [D]；专著 [M]。")

K.caption(doc, "表 8  GB/T 7714 写法与英文自然语序写法对照", above=True)
K.table(
    doc,
    ["文献", "写法 A · GB/T 7714", "写法 B · 英文自然语序"],
    [
        ["文献 1\nViT",
         "DOSOVITSKIY A, BEYER L, KOLESNIKOV A, et al. An image is worth 16x16 words: transformers for image recognition at scale[C]//International Conference on Learning Representations. 2021.",
         "Dosovitskiy A, Beyer L, Kolesnikov A, et al. An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale. In: ICLR, 2021."],
        ["文献 2\nCLIP",
         "RADFORD A, KIM J W, HALLACY C, et al. Learning transferable visual models from natural language supervision[C]//Proceedings of the International Conference on Machine Learning. PMLR, 2021, 139: 8748-8763.",
         "Radford A, Kim J W, Hallacy C, et al. Learning Transferable Visual Models from Natural Language Supervision. In: ICML, PMLR 139, 2021: 8748-8763."],
        ["文献 5\nLTC",
         "YEO W J, MAO R, ABDAR M, et al. Locate then correct: debiasing attention heads in CLIP[C]//Proceedings of the International Conference on Machine Learning. PMLR, 2026, 306: 148640-148677.",
         "Yeo W J, Mao R, Abdar M, et al. Locate then Correct: Debiasing Attention Heads in CLIP. In: ICML, PMLR 306, 2026: 148640-148677."],
    ],
    widths=[1.9, 7.1, 7.2],
    font_size=7.7,
    first_col_bold=True,
)
K.hint(doc, "其余 13 篇按同样规则套用：作者姓全大写+名缩写，会议用全称，年份后接页码；文献 10 用 [EB/OL] 并补 URL 与引用日期。"
            "所有条目建议由 Zotero 导出后手工校一遍，不要手抄。")

K.h2(doc, "常见错误")
K.bullet(doc, "作者格式混用：GB/T 7714 要求姓全大写、名缩写且缩写后不加点，不要一半全名一半缩写。")
K.bullet(doc, "“et al.” 与“等”混用：英文用 et al.，中文用“等”；超过 3 位作者时列前 3 位。")
K.bullet(doc, "会议名只写缩写或前后不一致：用全称（括号附缩写），同一篇在正文与列表必须一致。")
K.bullet(doc, "页码缺失或把 arXiv 预印本当正式发表：会议论文写起止页码；已正式发表的必须引正式版本。")
K.bullet(doc, "正文引用与列表不对应：正文每条都要在列表里，列表每条都要在正文被引用；中英文分列、编号连续。")

K.h2(doc, "交付前五分钟检查")
K.num(doc, 1, "对照学院最新模板逐项检查：字体、字号、行距、页边距、页码、图表题注位置。")
K.num(doc, 2, "用 Zotero“查找重复条目”清一遍库，并随机抽 5 条在数据库搜标题，确认作者、年份、会议、页码全对得上。")
K.num(doc, 3, "导出 PDF 打印一份，纸质稿读一遍——屏幕上看不出的格式问题，纸上很明显。")

K.callout(
    doc,
    "最后一句",
    ["文献读得好不好，不看读了多少篇，看能不能在论文里指出“这句话出自哪一篇、哪一节、为什么支持我的做法”。"
     "每读完一篇就问自己这个问题；答不上来，回去补笔记。"],
    kind="warn",
)

# ------------------------------------------------------------------ 保存 + 自检
K.save(doc, OUT)

from docx import Document                      # noqa: E402

chk = Document(OUT)
n_par = len(chk.paragraphs)
n_tab = len(chk.tables)
h1s = []
for para in chk.paragraphs:
    if para.runs and para.runs[0].font.size is not None and para.runs[0].font.size.pt >= 17:
        if para.text.strip():
            h1s.append(para.text.strip())

empty_tables = [i for i, t in enumerate(chk.tables)
                if len(t.rows) == 0 or all(not c.text.strip() for r in t.rows for c in r.cells)]

print("=" * 60)
print("输出文件：", OUT)
print("文件大小：", os.path.getsize(OUT), "bytes")
print("段落总数：", n_par)
print("表格总数：", n_tab)
print("空表数量：", len(empty_tables))
print("一级标题（共 %d 个）：" % len(h1s))
for h in h1s:
    print("  -", h)

assert n_par > 80, f"段落数不足：{n_par}"
assert n_tab >= 4, f"表格数不足：{n_tab}"
assert not empty_tables, f"存在空表：{empty_tables}"
print("自检通过：段落数 > 80，表格数 >= 4，无空表。")
