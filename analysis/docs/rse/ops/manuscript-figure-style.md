# Manuscript figure style

All manuscript figure producers must call:

```python
from plotting.style import use_manuscript_style

use_manuscript_style()
```

The function applies SciencePlots `science` and `notebook` styles, Computer
Modern serif text, mathematical labels, inward ticks, tight PDF bounds, and
embedded TrueType fonts. SciencePlots is required; manuscript production fails
instead of silently changing style when it is unavailable.

Figure-specific size, color, and layout settings may follow the shared call.
Do not add plot titles; the manuscript caption provides the title. Prefer
mathematical notation in axes and explain it in the caption.

Declare manuscript producers and PDF outputs in `figures/catalog.yaml`. A
styled figure is not manuscript-ready until it passes the provenance,
regeneration, scientific, and owner-review gates in
`docs/rse/control/visual-review-workflow.md`.
