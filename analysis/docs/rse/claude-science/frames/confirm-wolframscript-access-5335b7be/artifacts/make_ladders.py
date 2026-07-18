import sys, os, numpy as np, json
sys.path.insert(0,"scint_analysis")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import window_refit as wr, window_optimize as wo
figstyle = globals().get("apply_figure_style") or __import__("kernel", fromlist=["apply_figure_style"]).apply_figure_style if False else None
try:
    from kernel import apply_figure_style
    apply_figure_style(sizes=(9,8,7))
except Exception as e:
    pass

def prof_of(name):
    bl,ol=wr.default_windows(name); spec,_,_=wr._build_spec(name,bl,ol)
    p=np.ma.filled(np.ma.mean(spec.power,axis=0),np.nan); return np.nan_to_num(p,nan=np.nanmedian(p))

FOCAL="#c1272d"; DATA="#2b2b2b"; ENV="#4877b0"
def ladder(name, savepath):
    p=prof_of(name); sel=wo.select_windows(p)
    r=wr.refit(name, sel["burst_core"], sel["off_lims"])
    cf=r["center_freqs"]; order=list(r["order"])  # low->high freq
    order_hi2lo=order[::-1]
    a=r["alpha"]
    n=len(order_hi2lo)
    fig,axes=plt.subplots(n,1,figsize=(3.6,1.15*n+0.6),sharex=True)
    if n==1: axes=[axes]
    for ax,i in zip(axes,order_hi2lo):
        f=r["fits"][int(i)]
        if not f["ok"]:
            ax.text(0.5,0.5,f"{cf[i]:.0f} MHz — no fit",transform=ax.transAxes,ha="center",va="center",color="0.5"); ax.set_yticks([]); continue
        lp=np.asarray(f["lp"]); ap=np.asarray(f["ap"]); model=np.asarray(f["model"])
        ax.plot(lp,ap,'.',ms=2.5,color=DATA,alpha=0.55,zorder=1)
        oo=np.argsort(lp)
        ax.plot(lp[oo],model[oo],'-',lw=1.6,color=FOCAL,zorder=3,
                label=f"fit ({f['model_sel']})")
        # two-comp broad envelope shown separately
        if f.get("gamma_b"):
            broad=f["A_b"]/(1+(lp[oo]/f["gamma_b"])**2)+f["c0"]
            ax.plot(lp[oo],broad,'--',lw=1.0,color=ENV,zorder=2,label="broad env.")
        res=r"$\checkmark$" if f["resolved"] else "unres"
        railed = " (env. railed)" if (f.get("gamma_b") and f["gamma_b"]>=19.9) else ""
        gtxt=rf"$\nu_d$={f['gamma']:.3f}$\pm${f['gamma_err']:.3f} MHz {res}"
        mtxt=rf"$m$={f['m']:.2f}   {f['model_sel']}{railed}"
        # headroom so the annotation box clears the data
        y0,y1=ax.get_ylim(); ax.set_ylim(y0, y1 + 0.55*(y1-y0))
        blk=f"{cf[i]:.0f} MHz\n{gtxt}\n{mtxt}"
        ax.text(0.975,0.94,blk,transform=ax.transAxes,ha="right",va="top",linespacing=1.5,
                bbox=dict(boxstyle="round,pad=0.3",fc="white",ec="0.8",alpha=0.85))
        ax.axhline(0,color="0.7",lw=0.6,zorder=0)
        ax.margins(x=0.02)
        ax.set_xlim(0, wr.LAG_MAX)
    axes[-1].set_xlabel("frequency lag (MHz)")
    axes[n//2].set_ylabel("ACF")
    atxt = (rf"$\alpha$ = {a['alpha']:+.2f} $\pm$ {a['alpha_err']:.2f}  (n={a['n']}"
            + (", provisional)" if a.get("provisional") else ")")) if a else r"$\alpha$: n/a"
    fig.suptitle(f"{name}: scintillation ACF ladder\n{atxt}", fontsize=9)
    fig.tight_layout(rect=[0,0,1,0.97])
    fig.savefig(savepath,dpi=200)
    # bbox check
    rr=fig.canvas.get_renderer()
    import matplotlib as mpl
    texts=[(t,t.get_window_extent(rr)) for t in fig.findobj(mpl.text.Text) if t.get_text().strip() and t.get_visible()]
    ov=[(x,y) for k,(x,bx) in enumerate(texts) for y,by in texts[k+1:] if bx.overlaps(by)]
    plt.close(fig)
    return a, len(ov)

for nm in ["chromatica","zach","freya","hamilton"]:
    out=f"/Users/jakobfaber/Developer/scratch/{nm}_acf_ladder.png"
    a,nov=ladder(nm,out)
    print(f"{nm}: saved {os.path.basename(out)}  alpha={a['alpha']:+.2f} n={a['n']}{' PROV' if a and a.get('provisional') else ''}  text_overlaps={nov}" if a else f"{nm}: saved, alpha=n/a overlaps={nov}")
