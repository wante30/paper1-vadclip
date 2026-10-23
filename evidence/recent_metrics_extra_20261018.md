# Recent WSVAD metric checks: additional methods

Checked: 2026-10-18. Scope: the specified recent methods (ReFLIP-VAD, CMSIL/CMIL, Temporal-aware prompt learning, Learning opposite prompts) and an independent-source check of VadCLIP++. No manuscript or bibliography files were changed.

## Reference point and comparability

The current manuscript reports best-run UCF-Crime AUC = 88.25% and XD-Violence AP = 84.94%. Simple differences below are arithmetic against those manuscript values, not matched-protocol gains. Papers may differ in visual features/backbones, splits, checkpoint selection, and evaluation scripts; these published headline metrics must not be presented as controlled comparisons unless those protocols are verified.

## Findings

| Work | Publicly verifiable result | Modality / setup evidence | Assessment against 88.25 UCF AUC / 84.94 XD AP |
|---|---|---|---|
| ReFLIP-VAD (Dev et al., IEEE TCSVT, 2024) | The public abstract indexed by OpenAlex reports UCF-Crime AUC 89.14% and XD-Violence AP 86.29%. | Abstract describes a vision-language approach with visual features, text alignment, prompt encoder, temporal Glimpse-Emphasize module, and MIL-Align. Specific backbone, features, seeds, and test/checkpoint protocol are not stated in the accessible abstract. | Higher by +0.89 AUC / +1.35 AP points. This is a relevant counterexample to any claim that the present best-run values are the highest among recent WSVAD methods. Cross-paper protocol equivalence is unverified. The abstract's linked code URL currently returns 404 through the public GitHub API check. |
| CMSIL (Qian et al., IEEE ICME, 2024; Crossref record title uses “CLIP-Driven Multi-Scale Instance Learning”) | The accessible abstract confirms experiments on both datasets but gives no numeric AUC/AP. | Abstract describes a CLIP vision-language branch that generates pseudo-anomaly cues and a multi-scale instance-learning feature-pyramid branch. The authors' public repository README requests extracted I3D features for UCF/XD; configs set modality=`rgb`, UCF eval metric `AUC@ROC`, XD eval metric `AUC@PR`, and max steps 2,000. | Exact values unknown from the public abstract/repository material checked; do not include numerical comparison until the paper's results table is independently accessible. |
| Temporal-aware prompt learning (Yuan et al., Signal, Image and Video Processing, 2025) | No AUC/AP values were found in the accessible Crossref, OpenAlex, or Semantic Scholar metadata. | The accessible publisher landing page was blocked by its anti-bot challenge in this session; no accessible abstract or method details beyond the title/metadata. Modality, backbone, and evaluation protocol remain unknown. | Metrics unknown; not suitable for a numerical comparison row until checked from the public abstract/full text. DOI metadata confirms online publication 2025-12-13 and issue 19(18), article 1440. |
| Learning opposite prompts (Qiu et al., Knowledge-Based Systems, 2025) | No AUC/AP values or abstract were available in the accessible Crossref, OpenAlex, or Semantic Scholar metadata. | DOI metadata verifies the title, journal, volume 324, article 113600, and 2025 issue date. Specific modalities and evaluation protocol remain unknown. The Elsevier landing page did not expose its abstract in the normal public request. | Metrics unknown; do not infer values from title or secondary claims. |
| VadCLIP++ (Liu et al., Digital Signal Processing, 2026) | The current manuscript's benchmark table lists 88.12% UCF AUC / 85.03% XD AP, but the independently accessible DOI/Crossref and OpenAlex/Semantic Scholar records checked here confirm publication metadata only, not those two scores. | DOI metadata verifies the work and journal publication (vol. 168, article 105560; Jan. 2026). The publisher landing page's abstract/results were not accessible through the normal public request in this check. The title indicates a vision-language method; further details not independently checked here. | Score values remain unverified against the original accessible source in this audit. Keep them only if the paper's Table 1/2 or an author-hosted legal copy is available to check; otherwise mark the source limitation internally. |

## Source links and verification trail

- ReFLIP-VAD, DOI / IEEE record: https://doi.org/10.1109/TCSVT.2024.3482007
- ReFLIP-VAD abstract metadata (OpenAlex record keyed by DOI): https://api.openalex.org/works/https://doi.org/10.1109/tcsvt.2024.3482007
- ReFLIP-VAD Semantic Scholar record: https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/tcsvt.2024.3482007?fields=title,year,venue,abstract,openAccessPdf,externalIds
- CMSIL, DOI / IEEE ICME record: https://doi.org/10.1109/ICME57554.2024.10687724
- CMSIL abstract metadata (OpenAlex): https://api.openalex.org/works/https://doi.org/10.1109/icme57554.2024.10687724
- CMSIL author repository: https://github.com/casperZB/CMSIL (README and configs; source for I3D features and eval metrics)
- Temporal-aware prompt learning, DOI / Springer record: https://doi.org/10.1007/s11760-025-05031-5
- Temporal-aware prompt learning, Crossref record: https://api.crossref.org/works/10.1007/s11760-025-05031-5
- Learning opposite prompts, DOI / publisher record: https://doi.org/10.1016/j.knosys.2025.113600
- Learning opposite prompts, Crossref record: https://api.crossref.org/works/10.1016/j.knosys.2025.113600
- VadCLIP++, DOI / publisher record: https://doi.org/10.1016/j.dsp.2025.105560
- VadCLIP++, Crossref record: https://api.crossref.org/works/10.1016/j.dsp.2025.105560

## Writing implication

Add recent literature to related work based on verified method descriptions, especially ReFLIP-VAD, CMSIL, and the two prompt-learning papers. In the quantitative table, include recent numeric rows only when original results tables or accessible publisher abstracts expose the values and their dataset/metric definitions. ReFLIP-VAD's reported results should be acknowledged; they exceed the manuscript's best-run values, while protocol comparability remains unknown. Do not claim state of the art from the current values alone.
