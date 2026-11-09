# -*- coding: utf-8 -*-
"""audit.py —— 交付前一致性审计"""
import os, re, sys
from docx import Document
from openpyxl import load_workbook

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
DOCS = ["00_总览_先看这个.docx", "01_研究方向与技术路线.docx", "02_最终成果清单与验收标准.docx",
        "03_文献阅读清单.docx", "04_软件与环境配置.docx", "05_时间节点与任务计划.docx"]

CN = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8,
      "九": 9, "十": 10, "十一": 11, "十二": 12, "十三": 13}


def doc_text(path):
    d = Document(path)
    chunks = []
    for p in d.paragraphs:
        if p.text.strip():
            chunks.append(p.text)
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                if c.text.strip():
                    chunks.append(c.text)
    return "\n".join(chunks)


texts = {f: doc_text(os.path.join(ROOT, f)) for f in DOCS}

print("=" * 78)
print("① 残留标记扫描（Markdown / 占位符 / 编造数字）")
print("=" * 78)
patterns = {
    r"\*\*": "Markdown 加粗残留",
    r"```": "代码围栏残留",
    r"^\s*#{1,6}\s": "Markdown 标题残留",
    r"\|\s*---": "Markdown 表格分隔行",
    r"\]\(http": "Markdown 链接残留",
    r"TODO|TBD|待补充|待补|XXX|xxx占位|placeholder": "占位符残留",
    r"（待填）|待填写": "占位标记（可接受，确认是否有意）",
    r"准确率\s*(为|达|是)\s*\d+(\.\d+)?%": "★ 可疑的具体准确率数字（应为空模板）",
    r"（\d+\.\d+%）：|：\d+\.\d+%": "★ 可疑百分比",
}
hit_any = False
for f, txt in texts.items():
    for pat, desc in patterns.items():
        ms = re.findall(pat, txt, flags=re.M)
        if ms:
            hit_any = True
            print(f"  [{f}] {desc} × {len(ms)}: {str(ms[:3])[:110]}")
if not hit_any:
    print("  未发现残留标记")

print()
print("=" * 78)
print("② 各文档一级章节清单（用于校验跨文档引用）")
print("=" * 78)
chapter_map = {}
for f, txt in texts.items():
    # 一级标题以 “一、/二、…十二、” 开头且整行不超过 40 字
    found = []
    for line in txt.split("\n"):
        s = line.strip()
        m = re.match(r"^([一二三四五六七八九十]{1,2})、(.{2,38})$", s)
        if m and "\n" not in m.group(2):
            found.append(m.group(2))
    chapter_map[f[:2]] = found
    print(f"\n  {f[:2]} 号（共 {len(found)} 章）:")
    for i, t in enumerate(found, 1):
        print(f"     {i:>2}. {t}")

print()
print("=" * 78)
print("③ 跨文档引用校验：0X 号文档第Y章 是否真实存在")
print("=" * 78)
ref_pat = re.compile(r"(0[0-6])\s*号文档第([一二三四五六七八九十]{1,2})章")
bad = []
total = 0
for f, txt in texts.items():
    for m in ref_pat.finditer(txt):
        total += 1
        tgt, cn = m.group(1), m.group(2)
        idx = CN.get(cn)
        lst = chapter_map.get(tgt, [])
        ok = idx is not None and 1 <= idx <= len(lst)
        status = "OK" if ok else "★ 失效"
        if not ok:
            bad.append((f, tgt, cn, idx, len(lst)))
        print(f"  {f[:2]} 号 -> {tgt} 号 第{cn}章: {status}"
              + (f"  (目标仅 {len(lst)} 章)" if not ok else f"  => {lst[idx-1] if ok else ''}"))
print(f"\n  引用总数 {total}，失效 {len(bad)}")

print()
print("=" * 78)
print("④ 关键数字口径一致性")
print("=" * 78)
checks = [
    ("总周数 26", lambda t: "26 周" in t or "26周" in t),
    ("里程碑 M1~M6", lambda t: "M6" in t),
    ("144 个头", lambda t: "144" in t),
]
for f in ["00_总览_先看这个.docx", "01_研究方向与技术路线.docx", "05_时间节点与任务计划.docx"]:
    print(f"  {f[:2]} 号: " + ", ".join(f"{n}={'✓' if fn(texts[f]) else '✗'}" for n, fn in checks))

for label, pat in [
    ("'九张图' 说法", r"九张图"),
    ("'十张图' 说法", r"十张图"),
    ("'7 项必交' 说法", r"7 项必交"),
    ("'前四项是硬性' 说法", r"前四项是硬性"),
    ("'前五项是硬性' 说法", r"前五项是硬性"),
    ("小时数 500~550", r"500~550"),
    ("小时数 520~650", r"520~650"),
    ("每周 20~25 小时", r"20~25 小时"),
]:
    owners = [f[:2] for f, t in texts.items() if re.search(pat, t)]
    print(f"  {label:<22} 出现在: {owners if owners else '无'}")

print()
print("=" * 78)
print("⑤ Excel 结构复核")
print("=" * 78)
wb = load_workbook(os.path.join(ROOT, "06_进度追踪表.xlsx"))
print("  sheets:", wb.sheetnames)
ws = wb["① 看板"]
print("  B3 说明:", str(ws["B3"].value)[:60])
print("  B5 标签:", ws["B5"].value, "| C5 值:", ws["C5"].value, "| D5:", ws["D5"].value)
ws2 = wb["② 任务清单"]
n = sum(1 for r in range(2, ws2.max_row + 1) if ws2.cell(row=r, column=1).value)
print("  任务行数:", n, "| 最后一行:", ws2.cell(row=ws2.max_row, column=1).value)
print("  状态列下拉:", [dv.formula1 for dv in ws2.data_validations.dataValidation])
