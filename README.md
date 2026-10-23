# CSCWD manuscript — Placement-Aware Refinement

## 2026-10-15 XD 消融更正（当前）

按作者最终截图更新 Table IV(c)：Stage 1 为 77.60 AP（+0.03 pp），VadCLIP + Stage 2 为 79.15 AP（+1.58 pp）。完整模型仍为 79.23 AP，主结果 +1.66±0.34 pp 和其他统计量保持。此前误读的 79.55 未应用。制表脚本读取独立的均值更正 CSV，不合成逐 seed 数据；来源见 `evidence/cscwd_snapshot/xd_ablation_corrections_20261015.md`。当前六页稿保留已补齐 UCF 官方结果的摘要和 Figure 1。

## 2026-10-15 UCF 结果更正（先前）

已按作者确认的同方法、同协议结果更正 UCF AUC₁，并补充 UCF 官方设置的三种子配对结果。固定轮数增益为 +0.41 ± 0.11 pp，官方设置为 +0.35 ± 0.03 pp；其他指标经作者确认保持原值。当前版本保留六页和现有 Figure 1。来源与计算规则见 `evidence/cscwd_snapshot/ucf_corrections_20261015.md`。

## 2026-10-13 四项定点修订（历史）

当前 `main.pdf` 为六页定点修订稿，Figure 1 已替换为二次生成版本 `paper/figures/overview_regenerated.png`，统一主要字号并简化重复公式和装饰；原图与局部修正版均保留。正文调整 matched gain 的呈现顺序、两项细化的作用说明，以及共享预处理与残差融合的区分。所有实验数值不变，未加入 Figure 2。详见 `notes/FINAL_POINT_REVISION.md`。


## 主要文件

- `main.pdf`：完整英文论文，IEEE 双栏，US Letter，6 页。
- `paper/main.tex`：主 LaTeX 文件；Overleaf 中将其设为 Main document。
- `paper/sections/`：正文各章节。
- `paper/figures/overview_regenerated.png`：当前使用的四面板架构图，保留蓝灰风格并提高主要文字可读性。
- `paper/figures/overview_regenerated.prompt.txt`：生图及局部修正的提示词记录。
- 原图完整版本仍保留在此前交付的 LaTeX 源码包中；GitHub 仓库只保存用于排版的无内嵌图注版本。
- `paper/tables/`：从证据 CSV 自动生成的五张表。
- `refs/references.bib`：24 篇引用文献。
- `evidence/cscwd_snapshot/results_ledger.csv`：保留原始快照。
- `evidence/cscwd_snapshot/ucf_auc1_corrections_20261015.csv`：作者提供的新 AUC₁ 数据，单位为百分数；制表脚本在原快照上按键应用这些更正。
- `evidence/cscwd_snapshot/complexity.csv`：原始精度的延迟、显存、参数量。
- `evidence/cscwd_snapshot/calculated_summary.json`：均值、标准差、配对差值与开销计算。
- `notes/REVISION_NOTES.md`：中文修改和数据来源说明。
- `notes/validation.json`：构建及基础版式检查结果。

## 编译

本地安装 Python 3.9+ 和完整 TeX Live / MiKTeX 后，在项目根目录运行：

```sh
python scripts/build.py
```

脚本重新生成表格，直接使用 `paper/figures/overview_regenerated.png`，再编译论文和参考文献。它不下载数据、不运行训练、不评测模型、不访问 GPU。编译输出写入 `build/`，最终 PDF 更新为 `main.pdf`。

Overleaf：上传本 ZIP 的项目目录，选择 `paper/main.tex` 作为主文件，使用 pdfLaTeX。表格 .tex 和最终 PNG 已随包提供，不需要先运行 Python。更换图片只需更新 `paper/figures/overview_regenerated.png`，随后重新编译 `paper/main.tex`。

数值改变时，修改证据文件并运行 `python scripts/make_tables.py`。正文中的数值陈述也须同步修改，不能只改变表格。

可选检查：安装 PyMuPDF 后运行 `python scripts/validate.py`。

## 署名

作者栏沿用原稿的 `Anonymous Authors`。最终作者、单位、邮箱尚未提供，需在提交前由作者替换。论文正文、公式、图表及参考文献均已完成；这不是模板占位稿。

本包不包含原始训练数据或模型检查点；本文件随用户要求同步至 GitHub；原始研究实验文件位于 `evidence/`，CSCWD 稿使用独立快照 `evidence/cscwd_snapshot/`。

## Earlier Figure 1 replacement (archived)

The supplied four-panel image is inserted as `paper/figures/overview.png` (original, with baked caption: `overview_source_with_caption.png`). Only the baked-in caption area was cropped; the image's four panels were preserved without re-generation. The paper uses a native LaTeX `\caption` to avoid duplicate figure legends. `scripts/build.py` now uses the supplied image and does not overwrite it with the former generated TikZ figure.

## Earlier repository sync notes

- `paper/main.tex` and `paper/sections/` contain the Oct 13, 2026 six-page manuscript.
- `paper/figures/overview.png` is a 256-color, losslessly packaged-by-index figure with the original four-panel layout; only internal palette precision differs from the supplied RGB image.
- The existing historical `evidence/results_ledger.csv`, `evidence/complexity.csv`, and research generation scripts remain available; manuscript tables use the isolated `evidence/cscwd_snapshot/` files.
- `main.pdf` is an optimized six-page build artifact.
