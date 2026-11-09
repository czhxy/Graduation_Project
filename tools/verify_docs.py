# -*- coding: utf-8 -*-
import os, sys, glob
from docx import Document
from docx.oxml.ns import qn

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
files = sys.argv[1:] or sorted(
    f for f in glob.glob(os.path.join(ROOT, "*.docx"))
    if not os.path.basename(f).startswith("~$"))
for f in files:
    p = f if os.path.isabs(f) else os.path.join(ROOT, f)
    if not os.path.exists(p):
        print("MISSING", p); continue
    d = Document(p)
    paras = [x for x in d.paragraphs if x.text.strip()]
    chars = sum(len(x.text) for x in paras)
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                chars += len(c.text)
    bad_order = 0
    for tc in d.element.body.iter(qn('w:tcPr')):
        tags = [c.tag.split('}')[1] for c in tc]
        if 'shd' in tags and 'tcBorders' in tags and tags.index('shd') < tags.index('tcBorders'):
            bad_order += 1
    print(f"{os.path.basename(p):<34} 非空段={len(paras):>4}  表格={len(d.tables):>3}  字数≈{chars:>6}  tcPr顺序异常={bad_order}")
