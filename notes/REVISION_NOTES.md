# 本次完整论文修订说明

## 1. 交付内容

论文标题：**Placement-Aware Refinement for CLIP-Based Weakly Supervised Video Anomaly Detection**。

主文件为 `main.pdf`。使用 IEEEtran conference、US Letter、标准双栏字号；正文与参考文献合计六页。包含一张四面板架构图、五张表和 24 篇参考文献。作者栏沿用原稿的 Anonymous Authors，提交前需替换为最终署名、单位与邮箱。

这是对现有工作及已完成实验的整稿重写，没有启动新训练、新数据集评测或新增随机种子。没有推送或覆盖 GitHub 远端文件。

## 2. 叙事与写法

全文围绕“时序证据进入的位置”和“辅助语义监督更新的位置”组织，而不是罗列模块或描述探索过程。

- 摘要突出问题、两个方法设计、完整模型提升、官方设置下的 84.94 AP，以及低额外神经网络评分开销。
- 引言不再以“两阶段看起来不相关”开场；改为直接建立共同设计原则。
- 方法正面解释 PVR、kNN 混合和受限语义适配各自的操作与能力。
- 结果分析突出 PVR 独立有效性、PRE/POST 位置对照和等预算语义目标对照。
- 删除 narrow but useful、moderate gains、we do not claim synergy、limitations are equally clear、within seed noise 等自我降格或未经检验的统计解释。
- 不新增独立的局限性清单。已报告且影响结果解释的事实仍保留，例如 XD 分类 AP 和 B0+Stage2 数值；没有改写成不存在的全面提升或协同增益。
- 多 seed 与实验设置留在一次设置说明、必要表注和结果表中，不再成为摘要和讨论的反复主题。

## 3. GitHub 文件检查与数据生成

查看的论文仓库为 `wante30/paper1-vadclip`，master 对应本次读取版本 `6fa1268`。关键文件：

- `paper/main.tex`
- `scripts/make_tables.py`
- `scripts/measure_complexity.py`
- `evidence/results_ledger.csv`
- `evidence/complexity.csv`
- `evidence/formula_code_audit.md`
- `evidence/consistency_checks.csv`
- `refs/references.bib`

另查看了上游 `nwpu-zxr/VadCLIP` 的 `src/model.py`（原实验采用的 c41067f0 版本），核对分类、logit 加权视频聚合、文本侧残差和余弦评分的依赖关系。

交付包保留与本文表格相关的 130 条指标记录。它是从已读取 GitHub 账本提取的数值快照，不是重新训练或新评测的输出。生成脚本按指标、配置、种子集合明确计算均值和配对差；两种子 PVR 消融与三种子主结果分开处理。

官方 XD 的六个数值在仓库中来自 `evidence/manual/xd_official_protocol_remote4090.csv`，其来源说明是作者提供的远程 RTX 4090 实验摘要。本次沿用这一已提供结果，没有把该摘要说成重新下载并审计过的原始 metrics.json。原始模型和训练日志不包含在本交付包。

## 4. 实验表的最终组织

**Table I：代表性公开 benchmark。** 保留 CLIP-feature 对比，加入 VadCLIP++ 及本文官方设置最佳 84.94 AP。用一句表注标明本文 best of three；不把固定轮数均值混入该排名。本文官方 UCF 未提供，留“—”，不填入另一设置下的数值。

**Table II：完整模型受控结果。** 补齐最终两阶段模型的 UCF 四项主要指标，并保留 XD 语义 AP 与分类 AP。

| UCF 指标 | B0 | 最终两阶段模型 | 配对平均提升（pp） |
|---|---:|---:|---:|
| AUC1 | 86.24684 | 86.52989 | +0.28305 |
| AP1 | 29.26072 | 30.04303 | +0.78232 |
| AUC2 | 84.57313 | 85.00823 | +0.43510 |
| AP2 | 26.45635 | 27.30193 | +0.84558 |

这里 AUC2 是最终模型的 **+0.44 pp**，不是旧 Stage 1 的 +0.24 pp。此前未找到最终完整指标时的边界，现在已由 GitHub 账本补齐。表中 AP2 的显示值 27.30−26.46 与配对均值四舍五入到 +0.85 的差异，来自先算原始差值再显示，不是算术错误。

**Table III：官方设置配对结果。** 完整保留 234/235/236 的 84.21→84.94、81.77→82.65、82.74→83.31，以及均值和配对提升。

**Table IV：三个消融子表。** (a) B0 / PVR / PVR+kNN，统一 seeds 234/235；(b) PRE / POST，统一 seeds 234–236；(c) Stage 2 / CLASM-only / B0+Stage2，统一 seeds 234–236。PVR-only +0.25、kNN 条件增量 +0.11、PRE/POST +0.67、语义目标相对 C +1.64 均从保存值计算。

**Table V：复杂度。** 用原始精度重新计算，延迟显示两位小数：28.88→29.84 ms、17.44→18.06 ms。相对增加分别为 3.31477% 和 3.57011%，故正文 3.3–3.6% 正确。显存按脚本 `/2**20` 的实际定义改为 MiB，增加约 1.01 MiB。

旧 Stage 1 的 Within/Cross/Macro/dMAP 记录没有混充最终模型结果；论文也不声称所有定位指标一致提高。

## 5. 关键技术修正

- 明确差分对象是原始 CLIP snippet feature，不是像素帧差或光流。
- 明确先差分、再以相同边界聚合，残差注入发生在聚合之后、时序模型之前。
- 原始全序列差分可能包含聚合段/测试窗口边界的变化，因此采用 pre-aggregation snippet variation，避免声称每个差分都严格在段内部。
- 短序列仅保证 PRE/POST 在有效位置一致，不声称加入残差后的模型等于基线。
- 零初始化限定为残差输出为零、Z=A，不声称含图混合的整个 Stage 1 初始等于原 VadCLIP。
- kNN 项稀疏，但与稠密原图混合后仍保留稠密成分；没有宣称稀疏计算加速。
- 图中保留 s1→加权池化 a→文本条件以及 h 与适配文本之间的余弦评分。
- Stage 2 的保持对象是 Stage 1 检查点的分类输出，不是“完整模型与原始基线的分类输出相同”。
- 分类对 mlp1 的偏导为零；不再把语义对参数的偏导写成每一个输入下都必定非零。
- 计时脚本接收已给定的 appearance/variation tensor；正文用“neural scoring latency”，说明包含 prompt encoding，不把视频解码、视觉特征抽取和差分预处理算进这 3.3–3.6%。

## 6. 图与版式

Figure 1 保留第二页顶部跨双栏的位置。最终按用户本次上传的 PNG 原图直接替换此前的 TikZ 版本，四个面板均保持原样，未再使用图像生成。仅裁掉图片底部自带的 Figure 1 图注，改用 LaTeX `\caption{}` 生成单一图注。原图保存在 `paper/figures/overview_source_with_caption.png`，正文实际嵌入 `paper/figures/overview.png`。

原四组 paired-seed 折线图删除，证据由表格和保留 CSV 承担。没有再增加重复架构图。全部表格和参考文献已编译，不含待填结果占位。

## 7. 写作规范与文献核对

本次实际阅读的公开写作资料：

- https://github.com/mikubaka88/CCFA-Skills/blob/main/ccf-paper-writer/SKILL.md
- https://github.com/mikubaka88/CCFA-Skills/blob/main/ccf-humanization/references/humanization-policy.md
- https://github.com/mikubaka88/CCFA-Skills/blob/main/ccf-paper-writer/references/storyline-blueprint.md
- https://github.com/Adkid-Zephyr/anti-defensive-writing-Skill/blob/main/skills/anti-defensive-writing/SKILL.md

采用直接陈述科学内容、突出贡献而不写自我辩护的原则；不把减少防御性语言理解为改动数据、隐藏必要条件或虚构方法能力。

新增直接相近的 VadCLIP++（Digital Signal Processing 168, 105560, 2026），比较其动态提示差分与本文聚合前特征差分位置的区别。其公开结果 88.12 AUC / 85.03 AP 保留在公开比较中，本文没有虚构 SOTA。

新增 CSCWD 2025 的 Customizing Visual-Language Foundation Models for Multi-modal Anomaly Detection and Reasoning，作为视觉语言异常分析应用背景。同步将 PEL4VAD、MGFN、CLIP-Adapter、Houlsby adapter、LoRA 的书目整理为可核实的正式发表信息。

主要核对入口：

- VadCLIP: https://arxiv.org/abs/2308.11681
- VadCLIP++: https://doi.org/10.1016/j.dsp.2025.105560
- PEL4VAD: https://doi.org/10.1109/TIP.2024.3451935
- MGFN: https://doi.org/10.1609/aaai.v37i1.25112
- CLIP-Adapter: https://doi.org/10.1007/s11263-023-01891-x
- Houlsby adapter: https://proceedings.mlr.press/v97/houlsby19a.html
- CSCWD 2025 related paper: https://doi.org/10.1109/CSCWD64889.2025.11033177

## 8. 本次验证与提交前资料

已运行表格生成、算术断言、用户原图嵌入和正文编译，并逐页查看渲染结果；检查六页、US Letter、图在第二页、引用/公式交叉引用、溢出和防御性语句残留。机器检查结果见 `validation.json`。

最终作者顺序、单位、邮箱、资助信息未提供，未擅自添加。提交前按目标届次的作者指南处理署名、授权及 AI 辅助使用说明。这个检查属于提交资料准备，不要求补充研究实验。
