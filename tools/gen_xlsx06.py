# -*- coding: utf-8 -*-
"""生成 06_进度追踪表.xlsx"""
import sys, os
from datetime import date, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan_spec as S

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.utils import get_column_letter

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "docs", "06_进度追踪表.xlsx")

# ------------------------------------------------------------------ 样式常量
C_HEAD = "1F3B63"
C_HEAD2 = "DCE6F1"
C_BAND = "F7F9FC"
C_TODAY = "FFF2CC"
C_DONE = "C6EFCE"
C_WIP = "FFEB9C"
C_BLOCK = "FFC7CE"
C_TODO = "F2F2F2"

PHASE_COLORS = ["B4C7E7", "9DC3A7", "F4C7AB", "D9B3D3", "A9C4E8", "C9C9C9"]

THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

F_HEAD = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
F_BODY = Font(name="微软雅黑", size=9.5)
F_BOLD = Font(name="微软雅黑", size=9.5, bold=True)
F_TITLE = Font(name="微软雅黑", size=16, bold=True, color=C_HEAD)
F_SUB = Font(name="微软雅黑", size=9, color="595959")

AL_C = Alignment(horizontal="center", vertical="center", wrap_text=True)
AL_L = Alignment(horizontal="left", vertical="center", wrap_text=True)
AL_LT = Alignment(horizontal="left", vertical="top", wrap_text=True)


def head_row(ws, row, headers, widths=None, height=30):
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=row, column=i, value=h)
        c.font = F_HEAD
        c.fill = PatternFill("solid", fgColor=C_HEAD)
        c.alignment = AL_C
        c.border = BORDER
    ws.row_dimensions[row].height = height
    if widths:
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w


def fill_row(ws, row, values, aligns=None, band=False, bold_first=False):
    for i, v in enumerate(values, 1):
        c = ws.cell(row=row, column=i, value=v)
        c.font = F_BOLD if (bold_first and i == 1) else F_BODY
        c.border = BORDER
        if aligns and i <= len(aligns):
            c.alignment = {"c": AL_C, "l": AL_L}[aligns[i - 1]]
        else:
            c.alignment = AL_L
        if band:
            c.fill = PatternFill("solid", fgColor=C_BAND)


wb = Workbook()

# ================================================================== 1. 看板
ws = wb.active
ws.title = "① 看板"
ws.sheet_properties.tabColor = C_HEAD
ws.column_dimensions["A"].width = 3
ws.column_dimensions["B"].width = 26
ws.column_dimensions["C"].width = 20
ws.column_dimensions["D"].width = 20
ws.column_dimensions["E"].width = 20
ws.column_dimensions["F"].width = 34

ws.merge_cells("B2:F2")
c = ws["B2"]
c.value = "毕业设计进度看板 · Transformer 大模型图像分类中的背景依赖分析与抑制研究"
c.font = F_TITLE
c.alignment = Alignment(horizontal="left", vertical="center")
ws.row_dimensions[2].height = 34

ws.merge_cells("B3:F3")
c = ws["B3"]
c.value = ("用法：只需在 C5 填起始日期（第 1 周的周一），其余全部自动计算。"
          "每周更新「② 任务清单」的 I 列状态即可。")
c.font = F_SUB
c.alignment = Alignment(horizontal="left", vertical="center")

ws["B5"] = "起始日期（第1周周一）"
ws["B5"].font = F_BOLD
ws["B5"].alignment = AL_L
ws["B5"].fill = PatternFill("solid", fgColor=C_HEAD2)
ws["B5"].border = BORDER
ws["C5"] = S.ANCHOR
ws["C5"].number_format = "yyyy-mm-dd"
ws["C5"].font = Font(name="微软雅黑", size=11, bold=True, color="C00000")
ws["C5"].alignment = AL_C
ws["C5"].border = BORDER
ws["C5"].fill = PatternFill("solid", fgColor=C_TODAY)
ws["D5"] = "← 只改这个单元格"
ws["D5"].font = F_SUB
ws["D5"].alignment = AL_L

ws["B6"] = "结束日期（第26周周日）"
ws["B6"].font = F_BOLD
ws["B6"].alignment = AL_L
ws["B6"].border = BORDER
ws["C6"] = "=C5+7*26-1"
ws["C6"].number_format = "yyyy-mm-dd"
ws["C6"].font = F_BODY
ws["C6"].alignment = AL_C
ws["C6"].border = BORDER

rows_kpi = [
    ("今天", "=TODAY()", "yyyy-mm-dd"),
    ("当前所处周次", "=IF(TODAY()<C5,0,MIN(27,INT((TODAY()-C5)/7)+1))", "0"),
    ("距结束还有（天）", "=MAX(0,C6-TODAY())", "0"),
    ("总任务数", "=COUNTA('② 任务清单'!G2:G400)", "0"),
    ("已完成任务数", '=COUNTIF(\'② 任务清单\'!I:I,"已完成")', "0"),
    ("进行中任务数", '=COUNTIF(\'② 任务清单\'!I:I,"进行中")', "0"),
    ("受阻任务数", '=COUNTIF(\'② 任务清单\'!I:I,"受阻")', "0"),
    ("总完成率", "=IFERROR(C12/C11,0)", "0.0%"),
    ("应完成（截至上周）", "=COUNTIF('② 任务清单'!B:B,\"<\"&C10)", "0"),
    ("进度健康度", '=IF(C15=0,"—",IF(C12/C15>=0.9,"正常",IF(C12/C15>=0.7,"略滞后","严重滞后")))', "@"),
]
r = 9
for label, val, fmt in rows_kpi:
    ws.cell(row=r, column=2, value=label).font = F_BOLD
    ws.cell(row=r, column=2).alignment = AL_L
    ws.cell(row=r, column=2).border = BORDER
    cc = ws.cell(row=r, column=3, value=val)
    cc.number_format = fmt
    cc.font = F_BODY
    cc.alignment = AL_C
    cc.border = BORDER
    r += 1

# 修正 KPI 里的行号引用（总任务数在第 12 行、完成在第13行 → 完成率引用）
ws["C16"] = "=IFERROR(C13/C12,0)"
ws["C16"].number_format = "0.0%"
ws["C17"] = "=COUNTIF('② 任务清单'!B:B,\"<\"&C10)"
ws["C17"].number_format = "0"
ws["C18"] = '=IF(C17=0,"—",IF(C13/C17>=0.9,"正常",IF(C13/C17>=0.7,"略滞后","严重滞后")))'

wr = 21
ws.cell(row=wr, column=2, value="各阶段完成情况").font = Font(name="微软雅黑", size=12, bold=True, color=C_HEAD)
head_row(ws, wr + 1, ["", "阶段", "周次", "任务数", "已完成", "完成率"],
         widths=[3, 26, 20, 20, 20, 34], height=24)
# 左上角空表头去掉深色填充，避免出现一块孤立色块
ws.cell(row=wr + 1, column=1).fill = PatternFill(fill_type=None)
ws.cell(row=wr + 1, column=1).border = Border()
# 重新设置列宽（head_row 会覆盖，这里修正）
ws.column_dimensions["A"].width = 3
ws.column_dimensions["B"].width = 26
ws.column_dimensions["C"].width = 20
ws.column_dimensions["D"].width = 20
ws.column_dimensions["E"].width = 20
ws.column_dimensions["F"].width = 34

r = wr + 2
for ph in S.PHASES:
    w0, w1 = ph["weeks"]
    name = f'{ph["name"]} {ph["title"]}'
    ws.cell(row=r, column=2, value=name).font = F_BODY
    ws.cell(row=r, column=2).alignment = AL_L
    ws.cell(row=r, column=2).border = BORDER
    ws.cell(row=r, column=3, value=f"W{w0}–W{w1}").alignment = AL_C
    ws.cell(row=r, column=4, value=f'=COUNTIF(\'② 任务清单\'!B:B,">="&{w0})-COUNTIF(\'② 任务清单\'!B:B,">"&{w1})')
    ws.cell(row=r, column=5, value=f'=COUNTIFS(\'② 任务清单\'!B:B,">="&{w0},\'② 任务清单\'!B:B,"<="&{w1},\'② 任务清单\'!I:I,"已完成")')
    ws.cell(row=r, column=6, value=f"=IFERROR(E{r}/D{r},0)")
    ws.cell(row=r, column=6).number_format = "0.0%"
    for cc in range(3, 7):
        ws.cell(row=r, column=cc).border = BORDER
        ws.cell(row=r, column=cc).alignment = AL_C
        ws.cell(row=r, column=cc).font = F_BODY
    ws.cell(row=r, column=2).fill = PatternFill("solid", fgColor=PHASE_COLORS[S.PHASES.index(ph)])
    r += 1

ws.cell(row=r + 1, column=2,
        value="提示：任务清单里每一行是一周里的一个具体动作，共 %d 条。" % sum(len(w[3]) for w in S.WEEKS)).font = F_SUB

ws.sheet_view.showGridLines = False

# ================================================================== 2. 任务清单
ws2 = wb.create_sheet("② 任务清单")
ws2.sheet_properties.tabColor = "2E75B6"
headers2 = ["编号", "周次", "阶段", "开始日期", "截止日期", "本周主题",
            "具体任务", "本周交付 / 检查点", "状态", "完成日期", "备注"]
head_row(ws2, 1, headers2,
         widths=[9, 6, 8, 12, 12, 24, 46, 30, 10, 12, 24], height=30)

r = 2
for w, pid, theme, tasks, deliver in S.WEEKS:
    phase_name = next(p["name"] for p in S.PHASES if p["pid"] == pid)
    mon, sun = S.week_range(w)
    for ti, task in enumerate(tasks, 1):
        vals = [f"W{w:02d}-{ti}", w, phase_name, mon, sun, theme, task, deliver, "未开始", None, None]
        fill_row(ws2, r, vals, aligns="cclllllcccl", band=(r % 2 == 0))
        ws2.cell(row=r, column=4).number_format = "mm-dd"
        ws2.cell(row=r, column=5).number_format = "mm-dd"
        ws2.cell(row=r, column=10).number_format = "mm-dd"
        ws2.cell(row=r, column=2).font = F_BOLD
        ws2.row_dimensions[r].height = 34
        r += 1
last2 = r - 1

# 数据验证：状态下拉
dv = DataValidation(type="list",
                    formula1='"未开始,进行中,已完成,受阻,已取消"',
                    allow_blank=True, showDropDown=False)
dv.error = "请从下拉列表中选择"
dv.errorTitle = "输入无效"
ws2.add_data_validation(dv)
dv.add(f"I2:I{last2}")

# 条件格式：状态配色
for val, color in [("已完成", C_DONE), ("进行中", C_WIP), ("受阻", C_BLOCK),
                   ("未开始", C_TODO), ("已取消", "D9D9D9")]:
    ws2.conditional_formatting.add(
        f"I2:I{last2}",
        CellIsRule(operator="equal", formula=[f'"{val}"'],
                   fill=PatternFill("solid", fgColor=color)))

# 里程碑周高亮
ms_weeks = [m[2] for m in S.MILESTONES]
for wk in ms_weeks:
    ws2.conditional_formatting.add(
        f"A2:K{last2}",
        FormulaRule(formula=[f"$B2={wk}"],
                    fill=PatternFill("solid", fgColor="FDECE0")))

ws2.freeze_panes = "A2"
ws2.auto_filter.ref = f"A1:K{last2}"
ws2.sheet_view.zoomScale = 90

# ================================================================== 3. 周视图
ws3 = wb.create_sheet("③ 周视图")
ws3.sheet_properties.tabColor = "548235"
headers3 = ["周次", "开始", "截止", "阶段", "本周主题", "任务数", "已完成", "完成率", "本周交付 / 检查点"]
head_row(ws3, 1, headers3, widths=[6, 10, 10, 8, 28, 8, 8, 10, 40], height=30)
r = 2
for w, pid, theme, tasks, deliver in S.WEEKS:
    phase_name = next(p["name"] for p in S.PHASES if p["pid"] == pid)
    mon, sun = S.week_range(w)
    vals = [w, mon, sun, phase_name, theme, len(tasks),
            f'=COUNTIFS(\'② 任务清单\'!B:B,A{r},\'② 任务清单\'!I:I,"已完成")',
            f"=IFERROR(G{r}/F{r},0)", deliver]
    fill_row(ws3, r, vals, aligns="cccllcccl", band=(r % 2 == 0))
    ws3.cell(row=r, column=2).number_format = "mm-dd"
    ws3.cell(row=r, column=3).number_format = "mm-dd"
    ws3.cell(row=r, column=8).number_format = "0%"
    ws3.row_dimensions[r].height = 30
    r += 1

ws3.conditional_formatting.add(
    f"H2:H{r-1}",
    CellIsRule(operator="equal", formula=["1"],
               fill=PatternFill("solid", fgColor=C_DONE)))
ws3.freeze_panes = "A2"
ws3.sheet_view.zoomScale = 90

# ================================================================== 4. 甘特图
ws4 = wb.create_sheet("④ 甘特图")
ws4.sheet_properties.tabColor = "BF8F00"
ws4["A1"] = "26 周甘特图（阶段色带 + 里程碑）"
ws4["A1"].font = Font(name="微软雅黑", size=14, bold=True, color=C_HEAD)
ws4.column_dimensions["A"].width = 4
ws4.column_dimensions["B"].width = 30
ws4.column_dimensions["C"].width = 10

START_COL = 4  # D 列 = W1
for i in range(S.TOTAL_WEEKS):
    col = START_COL + i
    ws4.column_dimensions[get_column_letter(col)].width = 3.6
    c = ws4.cell(row=3, column=col, value=f"W{i+1}")
    c.font = Font(name="微软雅黑", size=7.5, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=C_HEAD)
    c.alignment = AL_C
    c.border = BORDER
    # 周起始日期（旋转）
    d = S.week_range(i + 1)[0]
    c2 = ws4.cell(row=2, column=col, value=d)
    c2.number_format = "m/d"
    c2.font = Font(name="微软雅黑", size=7, color="595959")
    c2.alignment = Alignment(horizontal="center", textRotation=90)
ws4["B3"] = "阶段"
ws4["B3"].font = F_HEAD
ws4["B3"].fill = PatternFill("solid", fgColor=C_HEAD)
ws4["B3"].alignment = AL_C
ws4["B3"].border = BORDER
ws4["C3"] = "周数"
ws4["C3"].font = F_HEAD
ws4["C3"].fill = PatternFill("solid", fgColor=C_HEAD)
ws4["C3"].alignment = AL_C
ws4["C3"].border = BORDER

r = 4
for idx, ph in enumerate(S.PHASES):
    w0, w1 = ph["weeks"]
    ws4.cell(row=r, column=2, value=f'{ph["name"]} {ph["title"]}').font = F_BOLD
    ws4.cell(row=r, column=2).alignment = AL_L
    ws4.cell(row=r, column=2).border = BORDER
    ws4.cell(row=r, column=3, value=f"{w1-w0+1}周").font = F_BODY
    ws4.cell(row=r, column=3).alignment = AL_C
    ws4.cell(row=r, column=3).border = BORDER
    for w in range(w0, w1 + 1):
        col = START_COL + w - 1
        c = ws4.cell(row=r, column=col)
        c.fill = PatternFill("solid", fgColor=PHASE_COLORS[idx])
        c.border = BORDER
    ws4.row_dimensions[r].height = 24
    r += 1

# 里程碑行
r_ms = r + 1
ws4.cell(row=r_ms, column=2, value="里程碑").font = F_BOLD
ws4.cell(row=r_ms, column=2).alignment = AL_L
ws4.cell(row=r_ms, column=2).border = BORDER
for m in S.MILESTONES:
    col = START_COL + m[2] - 1
    c = ws4.cell(row=r_ms, column=col, value=m[0])
    c.font = Font(name="微软雅黑", size=9, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor="C00000")
    c.alignment = AL_C
    c.border = BORDER

# 里程碑说明
r = r_ms + 2
ws4.cell(row=r, column=2, value="里程碑说明").font = Font(name="微软雅黑", size=11, bold=True, color=C_HEAD)
r += 1
for m in S.MILESTONES:
    ws4.cell(row=r, column=2, value=f"{m[0]}（W{m[2]}）{m[1]}").font = F_BODY
    ws4.cell(row=r, column=2).alignment = AL_L
    ws4.merge_cells(start_row=r, start_column=2, end_row=r, end_column=9)
    ws4.cell(row=r, column=10, value=m[3]).font = F_BODY
    ws4.cell(row=r, column=10).alignment = AL_L
    ws4.merge_cells(start_row=r, start_column=10, end_row=r, end_column=22)
    r += 1

ws4.sheet_view.showGridLines = False
ws4.freeze_panes = "D4"

# ================================================================== 5. 里程碑
ws5 = wb.create_sheet("⑤ 里程碑")
ws5.sheet_properties.tabColor = "C00000"
head_row(ws5, 1, ["编号", "名称", "周次", "计划周起始", "达成标准", "状态", "实际完成日", "差距分析"],
         widths=[8, 16, 8, 14, 52, 10, 14, 26], height=30)
r = 2
for m in S.MILESTONES:
    mon, _ = S.week_range(m[2])
    fill_row(ws5, r, [m[0], m[1], f"W{m[2]}", mon, m[3], "未开始", None, None],
             aligns="cclclcll", band=(r % 2 == 0))
    ws5.cell(row=r, column=4).number_format = "yyyy-mm-dd"
    ws5.cell(row=r, column=7).number_format = "yyyy-mm-dd"
    ws5.row_dimensions[r].height = 32
    r += 1
dv5 = DataValidation(type="list", formula1='"未开始,进行中,已达成,已延期"', allow_blank=True)
ws5.add_data_validation(dv5)
dv5.add(f"F2:F{r-1}")
for val, color in [("已达成", C_DONE), ("进行中", C_WIP), ("已延期", C_BLOCK)]:
    ws5.conditional_formatting.add(f"F2:F{r-1}",
                                   CellIsRule(operator="equal", formula=[f'"{val}"'],
                                              fill=PatternFill("solid", fgColor=color)))
ws5.freeze_panes = "A2"

# ================================================================== 6. 文献阅读
ws6 = wb.create_sheet("⑥ 文献阅读")
ws6.sheet_properties.tabColor = "7030A0"
head_row(ws6, 1, ["编号", "简称", "题目", "出处", "优先级", "计划周次", "状态", "笔记文件", "完成日期"],
         widths=[6, 18, 62, 22, 12, 10, 10, 24, 12], height=30)
r = 2
for lit in S.LITERATURE:
    fill_row(ws6, r, [lit["no"], lit["short"], lit["title"], lit["venue"], lit["prio"],
                      lit["when"], "未开始", None, None],
             aligns="clcllcll", band=(r % 2 == 0))
    ws6.row_dimensions[r].height = 30
    if lit["kind"] == "core":
        for cc in range(1, 10):
            ws6.cell(row=r, column=cc).fill = PatternFill("solid", fgColor="FFF2CC")
    r += 1
dv6 = DataValidation(type="list", formula1='"未开始,精读中,已读完,已做笔记"', allow_blank=True)
ws6.add_data_validation(dv6)
dv6.add(f"G2:G{r-1}")
for val, color in [("已读完", C_DONE), ("精读中", C_WIP), ("已做笔记", "BDD7EE")]:
    ws6.conditional_formatting.add(f"G2:G{r-1}",
                                   CellIsRule(operator="equal", formula=[f'"{val}"'],
                                              fill=PatternFill("solid", fgColor=color)))
ws6.freeze_panes = "C2"
ws6.auto_filter.ref = f"A1:I{r-1}"

# ================================================================== 7. 实验记录
ws7 = wb.create_sheet("⑦ 实验记录")
ws7.sheet_properties.tabColor = "00B0F0"
ws7["A1"] = ("实验记录表：每跑一次实验填一行。原则——论文里每个数字都必须能在这张表里找到，"
             "并且能顺着“结果路径”找到原始日志。")
ws7["A1"].font = F_SUB
ws7.merge_cells("A1:J1")
head_row(ws7, 2, ["实验ID", "日期", "实验名称", "关键配置", "总体准确率", "最差组准确率",
                  "随机种子", "结果文件路径", "对应论文表/图", "备注"],
         widths=[12, 12, 26, 34, 12, 13, 10, 30, 14, 24], height=30)
for r in range(3, 43):
    for cc in range(1, 11):
        cell = ws7.cell(row=r, column=cc)
        cell.border = BORDER
        cell.font = F_BODY
        cell.alignment = AL_L if cc in (3, 4, 8, 10) else AL_C
    ws7.cell(row=r, column=2).number_format = "yyyy-mm-dd"
    ws7.row_dimensions[r].height = 22
ws7.freeze_panes = "A3"

# ================================================================== 8. 周报
ws8 = wb.create_sheet("⑧ 周报")
ws8.sheet_properties.tabColor = "A9D08E"
ws8["A1"] = "每周复盘与导师汇报（每周日填，5 行以内发给导师）"
ws8["A1"].font = Font(name="微软雅黑", size=12, bold=True, color=C_HEAD)
head_row(ws8, 3, ["周次", "本周完成", "遇到的问题", "是否已求助", "下周计划", "导师反馈"],
         widths=[8, 40, 34, 12, 34, 30], height=28)
r = 4
for w in range(1, S.TOTAL_WEEKS + 1):
    fill_row(ws8, r, [f"W{w}", None, None, "否", None, None],
             aligns="clllll", band=(r % 2 == 0))
    ws8.row_dimensions[r].height = 30
    r += 1
dv8 = DataValidation(type="list", formula1='"否,已问导师,已问同门,已查资料"', allow_blank=True)
ws8.add_data_validation(dv8)
dv8.add(f"D4:D{r-1}")
ws8.freeze_panes = "B4"

wb.save(OUT)
print("OK ->", OUT)
