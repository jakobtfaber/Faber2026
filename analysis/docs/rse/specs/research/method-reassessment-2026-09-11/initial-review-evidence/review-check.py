from pathlib import Path
import sys, json, csv, collections, math, hashlib
import numpy as np
ROOT=Path('/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026')
E=ROOT/'analysis/docs/rse/specs/research/method-reassessment-2026-09-11'
sys.path.insert(0,str(E));sys.path.insert(0,str(ROOT/'analysis'))
import injection_recovery as ir
import kernel_switch_check as ks
import make_report as mr
from scattering.scat_analysis.burstfit import analytic_gaussian_exp_convolution as analytic, gaussian_powerlaw_convolution as fft
from scattering.scat_analysis.turbulence import alpha_from_beta
out={}
recs=mr.load(); prod=mr.load_prod(); summary=list(csv.DictReader((E/'results/summary.csv').open()))
out['cases']=dict(count=len(recs),arms=dict(collections.Counter(r['case']['arm'] for r in recs)),production=len(prod),inventory_matches={c.id for c in ir.inventory()}=={r['case']['id'] for r in recs})
errors=[]
for row in summary:
 r=next(r for r in recs if r['case']['id']==row['id']);cs=r['case'];c=r['classification'];q=r['result']['quantiles'][c['shape_param']]
 tr=ir.Truth(**cs['truth']);case=ir.Case(cs['id'],cs['arm'],tr,cs['model'],cs['snr'],cs['s2_factor'],cs['seed'],cs['note'])
 rebuilt=ir.classify(case,r['result'])
 for key in c:
  x,y=c[key],rebuilt[key]
  if isinstance(x,float) and math.isnan(x) and isinstance(y,float) and math.isnan(y): continue
  if x!=y:errors.append((cs['id'],'classification',key))
 for key in ['shape_p16','shape_p50','shape_p84','log10_tau_true','log10_tau_p50','alpha_p50']:
  if float(row[key]) != c[key]:errors.append((cs['id'],'summary',key))
 for key in ['p16','p50','p84']:
  if c['shape_'+key]!=q[key]:errors.append((cs['id'],'quantiles',key))
 a=np.array(r['result']['shape_samples']);
 if not np.all(np.isfinite(a)):errors.append((cs['id'],'invalid samples'))
out['consistency_errors']=errors
report=(E/'injection-recovery-results.md').read_text()
out['report_sections_exact']={k:v in report for k,v in {'harness_table':mr.table(recs),'production_table':mr.prod_table(prod),'verdicts':mr.verdicts(recs,prod),'kernel_switch_section':'\n'.join(mr.kernel_switch_section())}.items()}
a=[r for r in recs if r['case']['arm']=='a' and r['case']['truth']['kind']=='thin']
out['arm_a']=dict(n=len(a),coverage95=sum(r['classification']['shape_covered_95'] for r in a),coverage68=sum(r['classification']['shape_p16']<=r['classification']['true_shape']<=r['classification']['shape_p84'] for r in a),small_tau_seconds=sorted({r['case']['truth']['tau_1ghz'] for r in a}),dsa_tau_over_dt={str(b):ir.tau_nu(.00015,ir.scattering_index(b),np.array([1400.]))[0]/ir.BANDS['D']['dt'] for b in [3.3,3.67,3.9]})
out['production']=[{k:r.get(k) for k in ['case','tau_1ghz_true','beta_quantiles','mass_above','ncall','maxcall']} for r in prod]
out['branch_discontinuity']=ks.branch_discontinuity()
out['alpha_switch']=[alpha_from_beta(3.98-1e-10),alpha_from_beta(3.98)]
out['isolated_alpha_change']=[]
for band,m,t0 in zip(['CHIME','DSA'],ks.ppi.make_bands('exp',3.,32.,20260911),[4.,1.]):
 t=np.asarray(m.time);f=np.asarray(m.freq);tt=np.broadcast_to(t[None,:],(len(f),len(t)));z=(.085*f**-.79)[:,None]
 norm=lambda x:x/x.sum(axis=1,keepdims=True)
 A=analytic(tt,t0,z,(.0288*f**-4)[:,None]);B=analytic(tt,t0,z,(.0288*f**-out['alpha_switch'][0])[:,None]);ch=len(f)//2
 out['isolated_alpha_change'].append(dict(band=band,raw_max_over_peak=float(abs(A-B).max()/A.max()),middle_channel_area_normalized=float(abs(norm(A)[ch]-norm(B)[ch]).max()/norm(A)[ch].max())))
from scipy.integrate import quad
C=math.sqrt(math.pi/4); a=math.pi**2/16
out['thick_integral']=quad(lambda t:C*t**(-1.5)*math.exp(-a/t),0,np.inf)[0]
out['thick_truncated_first_moments']={str(T):quad(lambda t:C*t**(-.5)*math.exp(-a/t),0,T)[0] for T in [10,100,1000]}
rng=np.random.default_rng(32);d=rng.normal(size=(3,8));K=rng.normal(size=(3,8));s2=1.8
exact=sum(-.5*(x@np.linalg.solve(np.eye(8)+s2*np.outer(k,k),x)+np.linalg.slogdet(np.eye(8)+s2*np.outer(k,k))[1]) for x,k in zip(d,K))
out['gain_marginal_direct_covariance_error']=ir.band_loglike(d,K,s2)-exact
out['kernel_check']=ir.check_kernel()
state=json.loads((Path(__file__).parent/'reviewed-state.json').read_text())
out['changed_since_snapshot']=[r['path'] for r in state['files'] if hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()!=r['sha256']]
(Path(__file__).parent/'check-results.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['production','kernel_check']},indent=2))
