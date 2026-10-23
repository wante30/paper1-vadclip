# XD 消融均值更正（2026-10-15）

## 最终确认值

作者说明此前看串行，以最后提供的截图为准。仍为原 fixed-epoch 协议、seeds 234–236 的三次均值。

| 方法 | XD AP₂（%） | 与 baseline 的显示均值差（pp） |
| --- | ---: | ---: |
| VadCLIP | 77.57 | — |
| Stage 1 | 77.60 | +0.03 |
| VadCLIP + Stage 2 | 79.15 | +1.58 |
| Stage 1 + Stage 2 | 79.23 | +1.66 |

当前真正变化的两项为 Stage 1：77.44 → 77.60，以及 VadCLIP + Stage 2：79.46 → 79.15。完整模型 79.23 及其主结果 +1.66±0.34 pp 保持原值。作者上一张表中给出的 79.55 已撤回，没有应用到论文。

## 来源与边界

- 最终截图保存为 correction_sources_20261015/xd_ablation_confirmed.png，SHA-256：d7b7648c009179b5fe0bd0526c6f73726eeddf3c4d5d3db42c15ffdea61e7b27。
- CSV 只记录作者提供的三种子均值，不合成新的逐 seed 值，也不覆盖 results_ledger.csv。
- 作者确认其他结果沿用：CLASM-only 的 77.59、XD AP₁、official-setting 及其统计量保持不变。
- 两项更正仅用于原本报告均值的 Table IV(c) 及对应文字；未从这些均值推出新的标准差、逐 seed 正提升次数或显著性。
- 与 baseline 的新差值按两位小数的显示均值计算。完整模型比 Stage 2-only 高 0.08 pp，只陈述均值差，不称为显著协同。

## 联动范围

制表脚本读取专用均值 CSV，复现 Table IV(c)。正文将 VadCLIP + Stage 2 的结果改为 79.15，并说明完整模型为 79.23。主表、摘要（包括已补充的 UCF 官方结果）、结论、Figure 1、其他指标和六页结构保持。没有训练、推理或重新评测。

未被当前 main.tex 引用的 numbers_results.tex、tab_stage1.tex、tab_stage2.tex、tab_ablation.tex 等是历史派生文件，不作为本版结果来源，未用均值更正去重写其旧逐 seed 统计。
