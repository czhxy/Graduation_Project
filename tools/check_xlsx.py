# -*- coding: utf-8 -*-
import sys
from openpyxl import load_workbook

p = sys.argv[1]
wf = load_workbook(p, data_only=False)
wv = load_workbook(p, data_only=True)

print("sheets:", wf.sheetnames)

ws_f, ws_v = wf["① 看板"], wv["① 看板"]
print("\n--- 看板 KPI（公式 -> 缓存值）---")
for r in range(5, 19):
    b = ws_f.cell(row=r, column=2).value
    cf_ = ws_f.cell(row=r, column=3).value
    cv = ws_v.cell(row=r, column=3).value
    if b is None and cf_ is None:
        continue
    print(f"  r{r:<3} {str(b)[:22]:<24} | {str(cf_)[:46]:<48} => {cv}")

print("\n--- 各阶段完成情况 ---")
for r in range(21, 29):
    name = ws_v.cell(row=r, column=2).value
    if name is None:
        continue
    print(f"  {str(name)[:24]:<26} 任务数={ws_v.cell(row=r,column=4).value} 完成={ws_v.cell(row=r,column=5).value} 率={ws_v.cell(row=r,column=6).value}")

print("\n--- 周视图抽查（前 6 周 + 里程碑周）---")
ws3 = wv["③ 周视图"]
for r in range(2, 28):
    wk = ws3.cell(row=r, column=1).value
    if wk in (1, 2, 3, 6, 9, 13, 17, 21, 26):
        print(f"  W{wk}: 任务数={ws3.cell(row=r,column=6).value} 已完成={ws3.cell(row=r,column=7).value} 率={ws3.cell(row=r,column=8).value}")

print("\n--- 扫描全部单元格的错误值 ---")
errs = []
for ws in wv.worksheets:
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and c.value.startswith("#"):
                errs.append((ws.title, c.coordinate, c.value))
print("  错误单元格:", errs if errs else "无")

# 公式保留检查
n_formula = 0
for ws in wf.worksheets:
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and c.value.startswith("="):
                n_formula += 1
print("\n公式总数:", n_formula)
