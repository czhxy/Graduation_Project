# tools/ —— 文档生成与校验工具

> `docs/` 里的 6 份 Word + 1 份 Excel 是**由脚本生成**的，不是手改的。
> 想改内容就改这里，然后重新生成；**不要直接编辑 `docs/*.docx`**，否则下次重生成会被覆盖。

## 文件说明

| 文件 | 作用 |
|---|---|
| `plan_spec.py` | ★ **唯一数据源**：26 周任务、6 阶段、6 里程碑、16 篇文献、5 个基础补课模块、时间锚点 |
| `docx_kit.py` | 排版库：封面/标题/正文/表格/提示框/代码块/页码，支持 `**行内加粗**` |
| `gen_doc00.py` ~ `gen_doc05.py` | 分别生成 docs 下 00~05 号 Word |
| `gen_xlsx06.py` | 生成 06_进度追踪表.xlsx（含公式、下拉、条件格式、甘特图） |
| `verify_docs.py` | 校验所有 docx 能否解析、段落/表格/字数、XML 顺序是否合法 |
| `audit.py` | 一致性审计：跨文档章节引用是否真实存在、数字口径是否自洽、Excel 结构 |
| `check_xlsx.py` | 检查 xlsx 公式重算后的缓存值（配合 LibreOffice recalculate 用） |
| `read_task.py` | 重新读取任务书原文（含表格），改题或核对要求时用 |

## 依赖

```bash
# 本机已有 Python 3.12 即可，不需要 conda 环境
python -m pip install python-docx openpyxl
```

## 一条命令重新生成全部文档

```powershell
cd tools
$py = "python"      # 换成你的 python 路径
python gen_doc00.py; python gen_doc01.py; python gen_doc02.py
python gen_doc03.py; python gen_doc04.py; python gen_doc05.py
python gen_xlsx06.py
```

## 改内容的正确姿势

| 想改什么 | 改哪里 |
|---|---|
| 周计划、里程碑、文献清单、任务 | `plan_spec.py` → 再跑对应的 `gen_*.py` |
| 某份文档的某段文字 | 对应 `gen_docXX.py` 里那段字符串 |
| 排版样式（字体/行距/表格底色） | `docx_kit.py` |
| Excel 的列、公式、条件格式 | `gen_xlsx06.py` |

改完务必跑一次：

```bash
python verify_docs.py
python audit.py
```

## 坑（都踩过）

1. **Word 锁文件**：Word 开着文档时同目录会生成 `~$xxx.docx`。批量读 docx 的脚本必须先排除
   `~$` 前缀的文件，否则报 `PackageNotFoundError`。`verify_docs.py` 已处理。
2. **表格列宽**：只设单元格宽度（`tcW`）不生效，必须同时设 `gridCol`（`table.columns[i].width`）。
   `docx_kit._apply_widths()` 已统一处理。
3. **`tcPr` 元素顺序**：`w:tcBorders` 必须排在 `w:shd` 之前，否则 Word 打开会提示"内容有问题"。
4. **表格无边框不可靠**：`tblBorders val=none` 在 LibreOffice 里未必生效，封面改用制表位排版。
5. **Markdown 星号**：python-docx 不会把 `**粗体**` 变粗，会原样输出星号。`docx_kit` 已内置解析。
6. **表格跨页断行**：加 `w:cantSplit` 让每一行完整显示。
7. **xlsx 公式不自动算**：openpyxl 只写公式不算值，需要 LibreOffice 重算或 Excel 打开后按 F9。
