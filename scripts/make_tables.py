"""Generate manuscript tables from the inspected, fixed evidence snapshot.

No model training or evaluation is performed. All AUC/AP values in the input
ledger are fractions; tables report percent, and differences percentage points.
"""
from __future__ import annotations
import csv, json, statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'paper'/'tables'
OUT.mkdir(parents=True,exist_ok=True)
with (ROOT/'evidence/cscwd_snapshot/results_ledger.csv').open(encoding='utf-8') as f:
    rows=list(csv.DictReader(f))
D={(r['dataset'],r['protocol'],r['condition'],r['seed'],r['metric']):float(r['value'])*100 for r in rows}
assert len(D)==len(rows), 'Duplicate metric identities'

def vals(ds,c,m,proto='clean',seeds=('234','235','236')):
    return [D[(ds,proto,c,str(s),m)] for s in seeds]
def stat(ds,c,m,proto='clean',seeds=('234','235','236')):
    v=vals(ds,c,m,proto,seeds)
    return statistics.mean(v),statistics.stdev(v)
def delta(ds,a,b,m,proto='clean',seeds=('234','235','236')):
    v=[x-y for x,y in zip(vals(ds,a,m,proto,seeds),vals(ds,b,m,proto,seeds))]
    return statistics.mean(v),statistics.stdev(v),sum(x>0 for x in v)
def fmt(ms,signed=False,bold=False):
    a=(f'{ms[0]:+.2f}' if signed else f'{ms[0]:.2f}')
    out=a+r'\,\pm\,'+f'{ms[1]:.2f}'
    return '$'+(r'\mathbf{'+out+'}' if bold else out)+'$'
def write(name,s): (OUT/name).write_text(s,encoding='utf-8')
def mrow(label,entries):return label+' & '+' & '.join(entries)+r' \\'+'\n'

# External benchmark. Published scores are transcribed, not re-evaluated here.
pub=[('Sultani et al.','sultani2018real','84.14','75.18'),
     ('HL-Net','wu2020xdviolence','84.57','80.00'),
     ('RTFM','tian2021rtfm','85.66','78.27'),
     ('UR-DMU','zhou2023urdmu','86.75','82.41'),
     ('CLIP-TSA','joo2023cliptsa','87.58','82.17'),
     ('VadCLIP','wu2024vadclip','88.02','84.51')]
s=r'''\begin{table}[t]
\centering
\caption{Published CLIP-based benchmark results (\%). Earlier comparison rows follow VadCLIP~\cite{wu2024vadclip}; VadCLIP++ follows~\cite{liu2026vadclippp}. Our official-setting result is the best of three runs.}
\label{tab:benchmark}
\small\setlength{\tabcolsep}{5pt}
\begin{tabular}{lrr}\toprule
Method & UCF AUC & XD AP \\\midrule
'''
for n,k,u,x in pub:s+=mrow(n+r'~\cite{'+k+'}',[u,x])
s+=mrow(r'VadCLIP++~\cite{liu2026vadclippp}',['88.12','85.03'])
s+=r'\midrule'+'\n'+mrow('Ours (official setting)',['--',r'\textbf{84.94}'])
s+=r'\bottomrule\end{tabular}\end{table}'+'\n'
write('tab_benchmark.tex',s)

# Full-method metrics, never substitute Stage-1 semantic scores for the final model.
cols=[('UCF','Final','AUC1'),('UCF','Final','AP1'),('UCF','Final','AUC2'),('UCF','Final','AP2'),('XD','T','AP2'),('XD','T','AP1')]
s=r'''\begin{table*}[t]
\centering
\caption{Fixed-epoch results (mean $\pm$ standard deviation, \%) for the same seeds 234--236. Subscripts identify the classification (1) and semantic (2) outputs. $\Delta$ is the paired improvement over retrained VadCLIP.}
\label{tab:controlled}
\small\setlength{\tabcolsep}{4.0pt}
\begin{tabular}{lrrrrrr}\toprule
& \multicolumn{4}{c}{UCF-Crime} & \multicolumn{2}{c}{XD-Violence}\\
\cmidrule(lr){2-5}\cmidrule(lr){6-7}
Method & AUC$_1$ & AP$_1$ & AUC$_2$ & AP$_2$ & AP$_2$ & AP$_1$\\\midrule
'''
s+=mrow('VadCLIP',[fmt(stat(ds,'B0',m)) for ds,c,m in cols])
s+=mrow('Ours',[fmt(stat(ds,c,m),bold=(i<5)) for i,(ds,c,m) in enumerate(cols)])
s+=mrow(r'Paired $\Delta$',[fmt(delta(ds,c,'B0',m),signed=True) for ds,c,m in cols])
s+=r'\bottomrule\end{tabular}\end{table*}'+'\n'
write('tab_controlled.tex',s)

# Official results. The six input measurements are the author-supplied remote-4090 summary.
s=r'''\begin{table}[t]
\centering
\caption{XD-Violence AP (\%) using the original VadCLIP training setting. Each row pairs the same seed; $\Delta$ denotes Ours minus VadCLIP.}
\label{tab:official}
\small\setlength{\tabcolsep}{4.5pt}
\begin{tabular}{lrrr}\toprule
Seed & VadCLIP & Ours & $\Delta$\\\midrule
'''
for seed in ('234','235','236'):
 b=vals('XD','B0','AP2','official_rerun',(seed,))[0];t=vals('XD','T','AP2','official_rerun',(seed,))[0]
 s+=mrow(seed,[f'{b:.2f}',r'\textbf{'+f'{t:.2f}'+'}',f'{t-b:+.2f}'])
s+=r'\midrule'+'\n'+mrow('Mean',[fmt(stat('XD','B0','AP2','official_rerun')),fmt(stat('XD','T','AP2','official_rerun')),fmt(delta('XD','T','B0','AP2','official_rerun'),signed=True)])
s+=r'\bottomrule\end{tabular}\end{table}'+'\n'
write('tab_official.tex',s)

# Mechanism panels separate the two-seed and three-seed populations explicitly.
s=r'''\begin{table}[t]
\centering
\caption{Component and mechanism ablations (\%). Panel (a) uses seeds 234/235; panels (b,c) use 234--236. All values are means. $\Delta$ is relative to the baseline within each panel. C and full Stage 2 share the checkpoint, sample order and three-epoch budget, differing only in $\lambda$.}
\label{tab:ablations}
\small
\setlength{\tabcolsep}{5pt}
\begin{tabular}{lrr}\toprule
\multicolumn{3}{l}{\textbf{(a) Stage 1 components: UCF AUC$_1$}}\\
Variant & AUC & $\Delta$\\\midrule
'''
for name,c in [('VadCLIP','B0'),('+ PVR','A'),('+ PVR + kNN','AE')]:
 a=stat('UCF',c,'AUC1',seeds=('234','235'))[0]
 d='--' if c=='B0' else f"{delta('UCF',c,'B0','AUC1',seeds=('234','235'))[0]:+.2f}"
 s+=mrow(name,[f'{a:.2f}',d])
s+=r'''\midrule
\multicolumn{3}{l}{\textbf{(b) Variation placement: UCF AUC$_1$}}\\
Variant & AUC & $\Delta$\\\midrule
'''
for name,c in [('VadCLIP','B0'),('Post-aggregation + kNN','POST'),('Pre-aggregation + kNN','AE')]:
 a=stat('UCF',c,'AUC1')[0];d='--' if c=='B0' else f"{delta('UCF',c,'B0','AUC1')[0]:+.2f}"
 s+=mrow(name,[f'{a:.2f}',d])
s+=r'''\bottomrule\end{tabular}
\par\vspace{6pt}
\setlength{\tabcolsep}{4pt}
\begin{tabular}{lrrr}\toprule
\multicolumn{4}{l}{\textbf{(c) Semantic adaptation: XD-Violence}}\\
Variant & AP$_2$ & $\Delta$ & AP$_1$\\\midrule
'''
for name,c in [('VadCLIP','B0'),('Stage 1','AE'),('Stage 1 + CLASM (C)','C'),('Stage 1 + Stage 2','T'),('VadCLIP + Stage 2','B0T')]:
 a=stat('XD',c,'AP2')[0];d='--' if c=='B0' else f"{delta('XD',c,'B0','AP2')[0]:+.2f}"
 s+=mrow(name,[f'{a:.2f}',d,f"{stat('XD',c,'AP1')[0]:.2f}"])
s+=r'''\bottomrule\end{tabular}
\end{table}
'''
write('tab_ablations.tex',s)

with (ROOT/'evidence/cscwd_snapshot/complexity.csv').open() as f:cx={(r['dataset'],r['arm']):r for r in csv.DictReader(f)}
s=r'''\begin{table}[t]
\centering
\caption{Neural scoring cost for one 256-snippet window on an RTX 4060 Laptop GPU. Parameters exclude frozen CLIP encoders; peak allocated memory is in MiB.}
\label{tab:complexity}
\small\setlength{\tabcolsep}{3pt}
\begin{tabular}{llrrr}\toprule
Data & Model & Params (M) & Time (ms) & Memory\\\midrule
'''
for ds in ('UCF','XD'):
 for c,name in [('B0','VadCLIP'),('Final','Ours')]:
  r=cx[ds,c];s+=mrow(ds if c=='B0' else '',[name,f"{int(r['params_excl_clip'])/1e6:.3f}",f"{float(r['latency_ms_median']):.2f}",f"{float(r['peak_alloc_mib']):.2f}"])
s+=r'\bottomrule\end{tabular}\end{table}'+'\n'
write('tab_complexity.tex',s)

# Verification record for all calculations used in text/tables.
audit={}
for ds,c,m in cols:
 audit[f'{ds}_{m}']={'baseline':stat(ds,'B0',m),'ours':stat(ds,c,m),'paired':delta(ds,c,'B0',m)}
for key,args in [('PVR',('UCF','A','B0','AUC1')),('kNN_given_PVR',('UCF','AE','A','AUC1'))]:
 audit[key]=delta(*args,seeds=('234','235'))
audit['PRE_POST']=delta('UCF','AE','POST','AUC1')
audit['Stage2_C']=delta('XD','T','C','AP2')
audit['official']=delta('XD','T','B0','AP2','official_rerun')
audit['complexity']={ds:{'latency_delta_percent':(float(cx[ds,'Final']['latency_ms_median'])/float(cx[ds,'B0']['latency_ms_median'])-1)*100,'peak_mib_delta':float(cx[ds,'Final']['peak_alloc_mib'])-float(cx[ds,'B0']['peak_alloc_mib']),'params_delta':int(cx[ds,'Final']['params_excl_clip'])-int(cx[ds,'B0']['params_excl_clip'])} for ds in ('UCF','XD')}
(ROOT/'evidence/cscwd_snapshot/calculated_summary.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
assert round(audit['UCF_AUC1']['paired'][0],2)==.28
assert round(audit['XD_AP2']['paired'][0],2)==1.66
assert round(audit['PVR'][0],2)==.25
assert round(audit['PRE_POST'][0],2)==.67
assert round(audit['Stage2_C'][0],2)==1.64
assert all(audit['complexity'][d]['params_delta']==132736 for d in ('UCF','XD'))
print(json.dumps(audit,indent=2))
