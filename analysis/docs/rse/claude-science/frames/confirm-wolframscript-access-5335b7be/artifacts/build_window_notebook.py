"""Assemble window_tuning.ipynb — an ipywidgets notebook for interactively re-defining the
on/off-pulse windows per CHIME burst and watching the per-subband Lorentzian fits update live.
Opens in Deepnote (drop-in Jupyter), VS Code, or JupyterLab. Reads local data via window_refit.
"""
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

nb = new_notebook()
cells = []

cells.append(new_markdown_cell(
    "# CHIME per-burst scintillation: interactive window tuning\n\n"
    "Re-define the **on-pulse** and **off-pulse** time windows (and optional RFI bands) for each "
    "burst and watch the de-scallop + auto-RFI + per-subband Lorentzian fit update live.\n\n"
    "- **burst window** (blue) = on-pulse time bins used for the ACF\n"
    "- **off window** (grey) = off-pulse bins used for de-scalloping + RFI statistics; "
    "needs \u2265 50 bins for the pipeline off-pulse-mean de-scallop, else a time-median flat-field is used\n"
    "- **RFI bands** = frequency ranges (MHz) to mask on top of the pipeline + auto-flag\n\n"
    "Each subband ACF is harmonic-masked at k\u00d70.390625 MHz (the CHIME coarse-channel comb) before fitting. "
    "\u03b3 (decorrelation bandwidth) and the derived \u03b1 update on every refit. "
    "**Green = resolved** (amplitude clears noise, \u03b3 not railed, well-determined); grey = unresolved.\n\n"
    "> Runs against your local `.npz` data. The first refit of a burst loads its spectrum "
    "(a few seconds for the wide bursts); later refits of the same burst reuse the cached config."
))

cells.append(new_code_cell(
    "import os, sys, json\n"
    "os.environ.setdefault('FLITS_ROOT', "
    "'/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/dsa110-FLITS')\n"
    "sys.path.insert(0, '/Users/jakobfaber/Developer/scratch')\n"
    "import numpy as np\n"
    "import matplotlib.pyplot as plt\n"
    "import ipywidgets as W\n"
    "from IPython.display import display\n"
    "import window_refit as wr\n\n"
    "CHOICES_PATH = '/Users/jakobfaber/Developer/scratch/window_choices.json'\n"
    "CHOICES = json.load(open(CHOICES_PATH))\n"
    "BURSTS = ['casey','whitney','phineas','mahi','freya','zach','chromatica',"
    "'wilhelm','oran','hamilton','johndoeII','isha']\n"
    "COMB = 0.390625\n"
    "print('backend ready;', len(BURSTS), 'bursts')"
))

cells.append(new_markdown_cell("## Interactive panel"))

# the main interactive cell
panel = r'''
_state = {}   # name -> last refit result (for the save cell)

def _plot(r):
    order = r['order']; cf = r['center_freqs']; n = len(order)
    fig, axes = plt.subplots(1, n, figsize=(3.3*n, 3.2), sharex=True)
    if n == 1: axes = [axes]
    for ax, i in zip(axes, order):
        f = r['fits'][int(i)]
        if f['ok']:
            ax.plot(f['lp'], f['ap'], color='#c0392b', lw=1.0, label='data')
            col = '#1e8449' if f['resolved'] else '#7f8c8d'
            lab = f"\u03b3={f['gamma']:.3f}\u00b1{f['gamma_err']:.3f}\nm={f['m']:.2f} " + \
                  ('RESOLVED' if f['resolved'] else 'unres.')
            ax.plot(f['lp'], f['model'], color=col, lw=1.8, ls='--', label=lab)
        ax.axhline(0, color='k', lw=0.4, alpha=0.4)
        ax.set_xlim(0, wr.LAG_MAX); ax.set_title(f"{cf[i]:.0f} MHz", fontsize=9)
        ax.set_xlabel('lag (MHz)'); ax.legend(fontsize=6.5, loc='upper right')
    axes[0].set_ylabel('ACF (norm to lag 0)')
    a = r['alpha']
    astr = (f"\u03b1={a['alpha']:+.2f}\u00b1{a['alpha_err']:.2f} (n={a['n']})" if a else "\u03b1 = n/a (<2 resolved)")
    fig.suptitle(f"{r['name']}  |  {astr}  |  RFI +{r['rfi_new']} ch  |  {r['method']}", fontsize=10)
    fig.tight_layout(); plt.show()

def make_panel(name):
    ch = CHOICES[name]
    b0, b1 = ch['burst_lims']; o0, o1 = ch['off_lims']
    # probe ntime once so slider ranges are correct
    r0 = wr.refit(name, (b0, b1), (o0, o1), ch.get('rfi_bands_mhz', []))
    nt = r0['ntime']; _state[name] = r0
    burst_sl = W.IntRangeSlider(value=[b0, b1], min=0, max=nt, step=1,
                                description='on-pulse', continuous_update=False,
                                layout=W.Layout(width='700px'))
    off_sl = W.IntRangeSlider(value=[o0, o1], min=0, max=nt, step=1,
                              description='off-pulse', continuous_update=False,
                              layout=W.Layout(width='700px'))
    rfi_tx = W.Text(value=json.dumps(ch.get('rfi_bands_mhz', [])),
                    description='RFI bands', layout=W.Layout(width='700px'))
    status = W.HTML()
    out = W.Output()

    def run(_=None):
        try:
            bands = json.loads(rfi_tx.value) if rfi_tx.value.strip() else []
        except Exception as e:
            status.value = f"<b style='color:#c0392b'>RFI bands not valid JSON: {e}</b>"; return
        b = list(burst_sl.value); o = list(off_sl.value)
        status.value = "refitting\u2026"
        r = wr.refit(name, b, o, bands)
        _state[name] = r
        # persist into CHOICES in memory (save cell writes to disk)
        CHOICES[name]['burst_lims'] = b; CHOICES[name]['off_lims'] = o
        CHOICES[name]['rfi_bands_mhz'] = bands
        nres = sum(1 for i in r['order'] if r['fits'][int(i)]['ok'] and r['fits'][int(i)]['resolved'])
        status.value = f"<b>{name}</b>: {nres} resolved subband(s)  |  off-window {o[1]-o[0]} bins"
        with out:
            out.clear_output(wait=True); _plot(r)

    btn = W.Button(description='refit', button_style='primary')
    btn.on_click(run)
    burst_sl.observe(run, names='value'); off_sl.observe(run, names='value')
    run()
    return W.VBox([W.HTML(f"<h3>{name}</h3>"), burst_sl, off_sl, rfi_tx,
                   W.HBox([btn, status]), out])

dd = W.Dropdown(options=BURSTS, value='chromatica', description='burst')
panel_box = W.Output()
def switch(_=None):
    with panel_box:
        panel_box.clear_output(wait=True); display(make_panel(dd.value))
dd.observe(switch, names='value')
display(dd, panel_box)
switch()
'''
cells.append(new_code_cell(panel.strip()))

cells.append(new_markdown_cell(
    "## Save your window choices\n\n"
    "Run this after tuning. Writes the current windows + RFI bands for **all** bursts back to "
    "`window_choices.json`, which the batch driver `run_persubband_fits.py` consumes to regenerate "
    "the full-sample figures and the `persubband_fit_results.jsonl` table."
))
cells.append(new_code_cell(
    "for _n in BURSTS:\n"
    "    CHOICES[_n]['_default_windows'] = (_n not in _state)\n"
    "json.dump(CHOICES, open(CHOICES_PATH, 'w'), indent=2)\n"
    "edited = [n for n in BURSTS if not CHOICES[n].get('_default_windows', True)]\n"
    "print('wrote', CHOICES_PATH)\n"
    "print('tuned this session:', edited)"
))

nb['cells'] = cells
nb['metadata'] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
}
out_path = "/Users/jakobfaber/Developer/scratch/window_tuning.ipynb"
with open(out_path, "w") as fh:
    nbf.write(nb, fh)
print("WROTE", out_path, "with", len(cells), "cells")
