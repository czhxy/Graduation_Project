# -*- coding: utf-8 -*-
import sys
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "docs", "任务书_Transform背景依赖分析与抑制研究.docx")
doc = Document(path)

def iter_block_items(parent):
    from docx.oxml.ns import qn
    parent_elm = parent.element.body
    for child in parent_elm.iterchildren():
        if child.tag == qn('w:p'):
            yield Paragraph(child, parent)
        elif child.tag == qn('w:tbl'):
            yield Table(child, parent)

out = []
for block in iter_block_items(doc):
    if isinstance(block, Paragraph):
        t = block.text.strip()
        if t:
            out.append(f"[{block.style.name}] {t}")
    else:
        out.append("[TABLE]")
        for row in block.rows:
            cells = [c.text.strip().replace("\n", " / ") for c in row.cells]
            out.append(" | ".join(cells))
        out.append("[/TABLE]")

print("\n".join(out))

# also headers/footers? skip
