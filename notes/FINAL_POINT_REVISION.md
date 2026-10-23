# 四项定点修订

基于 GitHub `5bea369` 的六页稿完成。该版本 PDF 的正文与用户提供的“已替换 Figure1”版本一致。

1. **C001**：只修改消融分析的一句总结，说明聚合前时序细化改善 UCF-Crime 分类检测，受限适配驱动 XD-Violence 语义 AP 提升。保留 79.46 与 79.23 的完整对照。
2. **C002**：摘要、主结果和结论优先解释官方设置的三种子配对增益 0.73±0.16 pp，保留最佳 AP 84.94。Table I 将本方法标为 `official, best of 3`，取消 84.94 的加粗。表格生成脚本同步这一格式修改。
3. **C003**：保留原始 Figure 1 PNG，用局部矢量覆盖修正时间距离标签、文本侧残差适配和语义概率读出。同步将 (d) 的池化向量回流箭头接到现有文本条件加号。模块位置、四面板风格和图比例保持不变。
4. **C004**：Method 明确拼接仅用于共享聚合或分窗边界，之后分离 A、V，并按式(7)进行残差融合。

标题、研究设计、参数开销、所有实验表的数值、证据 CSV 与参考文献保持不变。没有启动训练、推理或模型评测，没有加入 Figure 2。

## 文件与构建

- `main.pdf`：修订后的六页成稿。
- `paper/main.tex`：主文件，按原项目方式编译。
- `paper/figures/overview_corrected.pdf`：排版使用的局部修正版图。
- `paper/figures/overview.png`：保留的原图。
- `scripts/patch_overview.py`：图的局部修补脚本；已经导出的 PDF 可直接编译，无需重跑修图脚本。
- `scripts/build.py`：原有 pdfLaTeX/BibTeX 构建入口，已同步修正版图的路径。

本次实际使用便携 Tectonic 0.17.0 编译，自动运行 BibTeX。也可在 Overleaf 选择 `paper/main.tex` 为主文件、使用 pdfLaTeX。编译器差异可能造成少量自然断行差异。

## 已完成检查

- PDF 为 6 页 US Letter，保留标准 IEEE 双栏字号与版式。
- 已逐页检查六页渲染，并放大检查 Figure 1。
- 五张活动实验表的数值单元格与修改前逐项一致。
- 24 篇参考文献，未发现未定义引用、缺字或 Overfull 文本溢出。
- Figure 1 仍在第二页；未添加 Figure 2。
- 原 PDF 未覆盖；本次未推送 GitHub。
