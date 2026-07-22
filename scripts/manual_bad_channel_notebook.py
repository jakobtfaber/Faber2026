#!/usr/bin/env python3
"""Jupyter controls for owner-selected, draft-only bad-channel maps."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

import ipywidgets as widgets
import matplotlib
import numpy as np
from IPython import get_ipython
from IPython.display import display as ipy_display
from matplotlib.widgets import SpanSelector


def _load_backend() -> ModuleType:
    path = Path(__file__).with_name("manual_bad_channel_review.py")
    spec = importlib.util.spec_from_file_location("manual_bad_channel_review", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load review backend: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BACKEND = _load_backend()

try:
    import ipympl as _ipympl
except ImportError:  # optional; needed only for interactive click-drag
    _ipympl = None

_MODE_COLORS = {
    "flag": "#d62728",
    "unflag": "#1f77b4",
    "view": "#7f7f7f",
}
_IPYMPL_BACKEND = "module://ipympl.backend_nbagg"


class ManualBadChannelNotebook:
    """Notebook controller; all selections remain drafts until separate approval."""

    def __init__(
        self,
        *,
        bundle_path: Path | str,
        map_path: Path | str,
        output_map_path: Path | str,
        default_frequency_window: tuple[float, float] = (700.0, 750.0),
        reason: str = "owner manual selection",
        evidence: str | None = None,
    ):
        self.bundle_path = Path(bundle_path).expanduser().resolve()
        self.map_path = Path(map_path).expanduser().resolve()
        self.output_map_path = Path(output_map_path).expanduser().resolve()
        self.bundle = BACKEND.load_review_bundle(self.bundle_path)
        payload = json.loads(self.map_path.read_text())
        review_metadata = payload.setdefault("review", {})
        review_metadata["notebook_interface_sha256"] = BACKEND.sha256(Path(__file__))
        self.session = BACKEND.ManualFlaggingSession(payload, self.bundle)

        valid_frequency = self.bundle.frequency_mhz[self.bundle.row_valid]
        if not valid_frequency.size:
            raise ValueError("review bundle has no selectable rows")
        self.frequency_min = float(np.min(valid_frequency))
        self.frequency_max = float(np.max(valid_frequency))
        differences = np.diff(np.unique(np.sort(valid_frequency)))
        positive_differences = differences[differences > 0]
        self._min_span_mhz = (
            float(np.min(positive_differences)) * 0.5
            if positive_differences.size
            else 0.001
        )
        requested_low, requested_high = sorted(default_frequency_window)
        window = (
            max(self.frequency_min, float(requested_low)),
            min(self.frequency_max, float(requested_high)),
        )
        if window[0] >= window[1]:
            window = (self.frequency_min, self.frequency_max)
        self.window = window
        self.pending_span = window

        self.mode = widgets.ToggleButtons(
            options=[
                ("Flag", "flag"),
                ("Unflag", "unflag"),
                ("Set view", "view"),
            ],
            value="flag",
            description="Drag:",
            tooltips=[
                "Drag vertically on a panel to flag that frequency span",
                "Drag vertically to clear flags in that frequency span",
                "Drag vertically to zoom the visible frequency window",
            ],
        )
        self.reason = widgets.Text(value=reason, description="Reason")
        self.evidence = widgets.Text(
            value=evidence or str(self.bundle_path), description="Evidence"
        )
        self.undo_button = widgets.Button(description="Undo")
        self.clear_button = widgets.Button(description="Clear")
        self.refresh_button = widgets.Button(description="Refresh")
        self.save_button = widgets.Button(description="Save draft", button_style="warning")
        self.status = widgets.HTML()
        self.help = widgets.HTML(
            "<b>Click and drag vertically</b> on any panel to select a frequency "
            "span. Frequency is the vertical axis. Use <b>Set view</b> to zoom, "
            "then <b>Flag</b> / <b>Unflag</b> to edit the draft."
        )
        # Canvas must be a direct child of the layout. Nesting ipympl inside
        # widgets.Output swallows mouse events in VS Code / Cursor notebooks.
        self.canvas_box = widgets.Box(
            layout=widgets.Layout(width="100%", overflow="hidden")
        )
        self.figure_output = widgets.Output()
        self._figure = None
        self._span_selectors: list[SpanSelector] = []
        self._interactive_backend = False

        self.undo_button.on_click(lambda _: self._run(self.undo))
        self.clear_button.on_click(lambda _: self._run(self.clear))
        self.refresh_button.on_click(lambda _: self._run(self.refresh))
        self.save_button.on_click(lambda _: self._run(self.save_draft))
        self.mode.observe(lambda _: self._restyle_selectors(), names="value")
        self._set_status("Ready. Drag a vertical span on the figure to edit.")

    def _ensure_interactive_backend(self) -> bool:
        if self._interactive_backend:
            return True
        if _ipympl is None:
            self._set_status(
                "ipympl is missing in this kernel — click-drag disabled. "
                "Install with `pip install ipympl`, restart the kernel, re-run.",
                error=True,
            )
            return False
        matplotlib.use(_IPYMPL_BACKEND, force=True)
        shell = get_ipython()
        if shell is not None:
            shell.run_line_magic("matplotlib", "widget")
        self._interactive_backend = True
        return True

    def _set_status(self, message: str, *, error: bool = False) -> None:
        selected = int(self.session.selected_rows.sum())
        color = "#b00020" if error else "#222"
        low, high = self.pending_span
        self.status.value = (
            f'<span style="color:{color}"><b>{selected} rows selected.</b> '
            f"Last span {low:.3f}–{high:.3f} MHz. {message}</span>"
        )

    def _run(self, action: Callable[[], Any]) -> None:
        try:
            action()
        except Exception as error:  # notebook must surface errors in place
            self._set_status(f"Error: {error}", error=True)

    def apply_span(self, minimum_mhz: float, maximum_mhz: float, *, mode: str) -> None:
        """Apply a frequency span. Used by click-drag and tests."""
        low, high = sorted((float(minimum_mhz), float(maximum_mhz)))
        self.pending_span = (low, high)
        if mode == "flag":
            self.flag_span()
        elif mode == "unflag":
            self.unflag_span()
        elif mode == "view":
            self.set_view(low, high)
        else:
            raise ValueError(f"unknown mode: {mode}")

    def flag_span(self) -> None:
        self.session.add_span(*self.pending_span)
        self.render()
        self._set_status("Draft selection changed; not approved or applied downstream.")

    def unflag_span(self) -> None:
        self.session.remove_span(*self.pending_span)
        self.render()
        self._set_status("Draft selection changed; not approved or applied downstream.")

    def set_view(self, minimum_mhz: float, maximum_mhz: float) -> None:
        low = max(self.frequency_min, min(float(minimum_mhz), float(maximum_mhz)))
        high = min(self.frequency_max, max(float(minimum_mhz), float(maximum_mhz)))
        if high - low < self._min_span_mhz:
            raise ValueError("view span is too narrow")
        self.window = (low, high)
        self.pending_span = self.window
        self.render()
        self._set_status("Visible frequency window updated.")

    def undo(self) -> None:
        self.session.undo()
        self.render()
        self._set_status("Last draft change undone.")

    def clear(self) -> None:
        self.session.clear()
        self.render()
        self._set_status("All draft selections cleared.")

    def refresh(self) -> None:
        self.render()
        self._set_status("Figure refreshed.")

    def save_draft(self) -> None:
        self.session.save_draft(
            self.output_map_path,
            reason=self.reason.value,
            evidence=self.evidence.value,
        )
        self._set_status(f"Draft saved to {self.output_map_path}; owner approval pending.")

    def _on_span_select(self, minimum_mhz: float, maximum_mhz: float) -> None:
        if abs(maximum_mhz - minimum_mhz) < self._min_span_mhz:
            return
        self._run(
            lambda: self.apply_span(minimum_mhz, maximum_mhz, mode=self.mode.value)
        )

    def _selector_props(self) -> dict[str, Any]:
        return {
            "alpha": 0.28,
            "facecolor": _MODE_COLORS.get(self.mode.value, "#d62728"),
        }

    def _restyle_selectors(self) -> None:
        props = self._selector_props()
        for selector in self._span_selectors:
            selector.props = props
            artist = getattr(selector, "_selection_artist", None)
            if artist is not None:
                artist.set_facecolor(props["facecolor"])
                artist.set_alpha(props["alpha"])

    def _attach_selectors(self, panels: dict[str, Any]) -> None:
        self._span_selectors = []
        props = self._selector_props()
        for key in ("before", "after", "spectrum"):
            selector = SpanSelector(
                panels[key],
                self._on_span_select,
                "vertical",
                useblit=False,
                props=props,
                interactive=False,
                drag_from_anywhere=True,
            )
            self._span_selectors.append(selector)

    def _close_figure(self) -> None:
        import matplotlib.pyplot as plt

        self._span_selectors = []
        self.canvas_box.children = ()
        if self._figure is not None:
            plt.close(self._figure)
            self._figure = None

    def render(self) -> None:
        import matplotlib.pyplot as plt

        self._close_figure()
        self.figure_output.clear_output(wait=True)
        self._figure, panels = BACKEND.build_review_figure(self.session, *self.window)
        self._attach_selectors(panels)
        if self._interactive_backend:
            canvas = self._figure.canvas
            if hasattr(canvas, "layout"):
                canvas.layout.width = "100%"
                canvas.layout.height = "auto"
            # Keep a hard reference on the box so selectors are not garbage-collected.
            self.canvas_box.children = (canvas,)
            return
        with self.figure_output:
            ipy_display(self._figure)
            plt.close(self._figure)
            self._figure = None
            self._span_selectors = []

    def widget(self) -> widgets.VBox:
        warning = widgets.HTML(
            "<b>Draft only.</b> No automatic flags are loaded. "
            "A one-dimensional channel map cannot remove time-local or diagonal RFI."
        )
        buttons = widgets.HBox(
            [
                self.undo_button,
                self.clear_button,
                self.refresh_button,
                self.save_button,
            ]
        )
        metadata = widgets.HTML(
            f"<code>{self.bundle.metadata['event']}</code> / "
            f"<code>{self.bundle.metadata['instrument']}</code><br>"
            f"Input map: <code>{self.map_path}</code><br>"
            f"Draft output: <code>{self.output_map_path}</code>"
        )
        return widgets.VBox(
            [
                warning,
                metadata,
                self.help,
                self.mode,
                widgets.HBox([self.reason, self.evidence]),
                buttons,
                self.status,
                self.canvas_box,
                self.figure_output,
            ]
        )

    def display(self) -> None:
        interactive = self._ensure_interactive_backend()
        ipy_display(self.widget())
        self.render()
        if interactive:
            self._set_status(
                f"Interactive canvas ready ({matplotlib.get_backend()}). "
                "Drag vertically to edit."
            )
        else:
            self._set_status(
                "Static figure only — click-drag unavailable without ipympl.",
                error=True,
            )
