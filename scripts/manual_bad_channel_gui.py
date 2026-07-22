#!/usr/bin/env python3
"""Standalone click-drag editor for draft manual bad-channel maps."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np


def _load_backend() -> ModuleType:
    path = Path(__file__).with_name("manual_bad_channel_review.py")
    spec = importlib.util.spec_from_file_location("manual_bad_channel_review", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load review backend: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BACKEND = _load_backend()


class ManualBadChannelGUI:
    """Native Matplotlib reviewer; all saves remain unapproved drafts."""

    MODES = ("flag", "unflag")

    def __init__(
        self,
        *,
        bundle_path: Path | str,
        map_path: Path | str,
        output_map_path: Path | str,
        default_frequency_window: tuple[float, float] = (700.0, 750.0),
        band_width_mhz: float = 50.0,
        reason: str = "owner manual selection",
        evidence: str | None = None,
        build: bool = True,
    ):
        self.bundle_path = Path(bundle_path).expanduser().resolve()
        self.map_path = Path(map_path).expanduser().resolve()
        self.output_map_path = Path(output_map_path).expanduser().resolve()
        self.bundle = BACKEND.load_review_bundle(self.bundle_path)
        payload = json.loads(self.map_path.read_text())
        payload.setdefault("review", {})["gui_interface_sha256"] = BACKEND.sha256(
            Path(__file__)
        )
        self.session = BACKEND.ManualFlaggingSession(payload, self.bundle)

        valid_frequency = self.bundle.frequency_mhz[self.bundle.row_valid]
        if not valid_frequency.size:
            raise ValueError("review bundle has no selectable rows")
        self.frequency_min = float(np.min(valid_frequency))
        self.frequency_max = float(np.max(valid_frequency))
        self.band_width_mhz = float(band_width_mhz)
        if not np.isfinite(self.band_width_mhz) or self.band_width_mhz <= 0:
            raise ValueError("band width must be finite and positive")
        low, high = sorted(map(float, default_frequency_window))
        low = max(self.frequency_min, low)
        high = min(self.frequency_max, high)
        if low >= high:
            low, high = self.frequency_min, min(
                self.frequency_max, self.frequency_min + self.band_width_mhz
            )
        self.window = (low, high)
        self.mode = "flag"
        self.reason = reason
        self.evidence = evidence or str(self.bundle_path)
        self.status_message = "Ready. Drag vertically to flag frequency rows."

        self.figure = None
        self.data_axes: dict[str, Any] = {}
        self.control_axes: dict[str, Any] = {}
        self.span_selectors: list[Any] = []
        self._buttons: list[Any] = []
        self._mode_selector = None
        self._colorbar_axis = None
        self._status_artist = None
        if build:
            self.build()

    @property
    def selected_count(self) -> int:
        return int(self.session.selected_rows.sum())

    def _set_status(self, message: str) -> None:
        self.status_message = message
        if self._status_artist is not None:
            retained = 1.0 - self.selected_count / max(
                int(self.bundle.row_valid.sum()), 1
            )
            self._status_artist.set_text(
                f"{self.selected_count} rows selected; retained {retained:.3%}. "
                f"{message}"
            )
        if self.figure is not None:
            self.figure.canvas.draw_idle()

    def set_mode(self, mode: str) -> None:
        normalized = str(mode).lower()
        if normalized not in self.MODES:
            raise ValueError(f"unknown mode: {mode}")
        self.mode = normalized
        self._set_status(
            "Drag vertically to flag rows."
            if normalized == "flag"
            else "Drag vertically to restore draft rows."
        )
        self._restyle_selectors()

    def apply_span(
        self, minimum_mhz: float, maximum_mhz: float, *, mode: str | None = None
    ) -> None:
        active_mode = self.mode if mode is None else str(mode).lower()
        if active_mode == "flag":
            self.session.add_span(minimum_mhz, maximum_mhz)
            message = "Draft rows flagged; no downstream data changed."
        elif active_mode == "unflag":
            self.session.remove_span(minimum_mhz, maximum_mhz)
            message = "Draft rows restored; no downstream data changed."
        else:
            raise ValueError(f"unknown mode: {active_mode}")
        self._set_status(message)
        self.redraw()

    def _on_drag(self, minimum_mhz: float, maximum_mhz: float) -> None:
        self.apply_span(minimum_mhz, maximum_mhz)

    def undo(self) -> None:
        self.session.undo()
        self._set_status("Last draft change undone.")
        self.redraw()

    def clear(self) -> None:
        self.session.clear()
        self._set_status("All draft selections cleared.")
        self.redraw()

    def _shift_band(self, direction: int) -> None:
        width = self.window[1] - self.window[0]
        low = self.window[0] + direction * self.band_width_mhz
        high = low + width
        if high > self.frequency_max:
            high = self.frequency_max
            low = max(self.frequency_min, high - width)
        if low < self.frequency_min:
            low = self.frequency_min
            high = min(self.frequency_max, low + width)
        self.window = (float(low), float(high))
        self._set_status(f"Viewing {low:.3f}–{high:.3f} MHz.")
        self.redraw()

    def previous_band(self) -> None:
        self._shift_band(-1)

    def next_band(self) -> None:
        self._shift_band(1)

    def save_draft(self) -> None:
        self.session.save_draft(
            self.output_map_path,
            reason=self.reason,
            evidence=self.evidence,
        )
        self._set_status(
            f"Draft saved to {self.output_map_path}; owner approval remains pending."
        )

    def _display_rows(self) -> np.ndarray:
        low, high = self.window
        rows = np.flatnonzero(
            (self.bundle.frequency_mhz >= low)
            & (self.bundle.frequency_mhz <= high)
        )
        if not rows.size:
            raise ValueError("review interval contains no frequency rows")
        return rows[np.argsort(self.bundle.frequency_mhz[rows])]

    def _selected_frequency_spans(self, rows: np.ndarray) -> list[tuple[float, float]]:
        selected = self.session.selected_rows[rows]
        padded = np.pad(selected, (1, 1))
        edges = np.diff(padded.astype(np.int8))
        starts = np.flatnonzero(edges == 1)
        stops = np.flatnonzero(edges == -1)
        frequency = self.bundle.frequency_mhz[rows]
        spacing = np.diff(frequency)
        half_step = 0.5 * float(np.median(spacing)) if spacing.size else 0.001
        return [
            (
                float(frequency[start] - half_step),
                float(frequency[stop - 1] + half_step),
            )
            for start, stop in zip(starts, stops, strict=True)
        ]

    def _disconnect_selectors(self) -> None:
        for selector in self.span_selectors:
            selector.disconnect_events()
        self.span_selectors = []

    def _selector_color(self) -> str:
        return "#d62728" if self.mode == "flag" else "#1f77b4"

    def _restyle_selectors(self) -> None:
        color = self._selector_color()
        for selector in self.span_selectors:
            artist = getattr(selector, "_selection_artist", None)
            if artist is not None:
                artist.set_facecolor(color)

    def _draw_panels(self) -> None:
        from matplotlib.widgets import SpanSelector

        self._disconnect_selectors()
        for axis in self.data_axes.values():
            axis.clear()
        self._colorbar_axis.clear()

        rows = self._display_rows()
        frequency = self.bundle.frequency_mhz[rows]
        valid = self.bundle.row_valid[rows]
        before = np.where(
            valid[:, None], self.bundle.dynamic_spectrum[rows], np.nan
        )
        after = BACKEND.mask_preview(before, self.session.selected_rows[rows])
        finite = before[np.isfinite(before)]
        limit = max(
            0.5,
            float(np.percentile(np.abs(finite), 99.5)) if finite.size else 0.5,
        )
        extent = (
            float(self.bundle.time_ms[0]),
            float(self.bundle.time_ms[-1]),
            float(frequency[0]),
            float(frequency[-1]),
        )
        cmap = __import__("matplotlib").colormaps["RdBu_r"].copy()
        cmap.set_bad("0.76")
        before_image = self.data_axes["before"].imshow(
            np.ma.masked_invalid(before),
            origin="lower",
            aspect="auto",
            extent=extent,
            cmap=cmap,
            vmin=-limit,
            vmax=limit,
            interpolation="nearest",
        )
        self.data_axes["after"].imshow(
            np.ma.masked_invalid(after),
            origin="lower",
            aspect="auto",
            extent=extent,
            cmap=cmap,
            vmin=-limit,
            vmax=limit,
            interpolation="nearest",
        )
        self.data_axes["before"].set_title("Before proposed manual flags")
        self.data_axes["after"].set_title("After proposed manual flags — draft only")
        for axis in (self.data_axes["before"], self.data_axes["after"]):
            axis.set_ylabel("Frequency (MHz)")
            axis.set_xlabel("Aligned relative time (ms)")

        spectrum = self.data_axes["spectrum"]
        spectrum.plot(
            self.bundle.on_spectrum[rows][valid],
            frequency[valid],
            color="black",
            lw=0.6,
            label="before",
        )
        retained = valid & ~self.session.selected_rows[rows]
        spectrum.plot(
            self.bundle.on_spectrum[rows][retained],
            frequency[retained],
            color="#d62728",
            lw=0.8,
            label="retained after draft",
        )
        spectrum.set_xlabel("Time-integrated burst spectrum")
        spectrum.set_ylabel("Frequency (MHz)")
        spectrum.legend(frameon=False, loc="best")
        for low, high in self._selected_frequency_spans(rows):
            for axis in self.data_axes.values():
                axis.axhspan(low, high, color="#d62728", alpha=0.13)

        self.figure.colorbar(
            before_image,
            cax=self._colorbar_axis,
            label="Standardized intensity",
        )
        props = {"alpha": 0.28, "facecolor": self._selector_color()}
        self.span_selectors = [
            SpanSelector(
                axis,
                self._on_drag,
                "vertical",
                useblit=True,
                props=props,
                button=1,
                interactive=False,
                drag_from_anywhere=True,
            )
            for axis in self.data_axes.values()
        ]
        for axis in self.data_axes.values():
            axis.set_ylim(float(frequency[0]), float(frequency[-1]))

    def _make_button(self, key: str, label: str, bounds, callback) -> None:
        from matplotlib.widgets import Button

        axis = self.figure.add_axes(bounds)
        button = Button(axis, label)
        button.on_clicked(lambda _event: callback())
        self.control_axes[key] = axis
        self._buttons.append(button)

    def _on_key(self, event) -> None:
        if event.key == "f":
            self.set_mode("flag")
        elif event.key == "u":
            self.set_mode("unflag")
        elif event.key in {"ctrl+z", "cmd+z"}:
            self.undo()
        elif event.key == "left":
            self.previous_band()
        elif event.key == "right":
            self.next_band()
        elif event.key == "s":
            self.save_draft()

    def build(self):
        import matplotlib.pyplot as plt
        from matplotlib.widgets import RadioButtons

        if self.figure is not None:
            return self.figure
        self.figure = plt.figure(figsize=(14, 10))
        manager = getattr(self.figure.canvas, "manager", None)
        if manager is not None and hasattr(manager, "set_window_title"):
            manager.set_window_title("Faber2026 manual bad-channel review")
        self.data_axes = {
            "before": self.figure.add_axes((0.07, 0.72, 0.77, 0.22)),
            "after": self.figure.add_axes((0.07, 0.41, 0.77, 0.22)),
            "spectrum": self.figure.add_axes((0.07, 0.17, 0.77, 0.17)),
        }
        self._colorbar_axis = self.figure.add_axes((0.855, 0.41, 0.015, 0.53))
        mode_axis = self.figure.add_axes((0.90, 0.75, 0.085, 0.12))
        self._mode_selector = RadioButtons(mode_axis, ("Flag", "Unflag"), active=0)
        self._mode_selector.on_clicked(self.set_mode)
        self.control_axes["mode"] = mode_axis

        controls = [
            ("previous", "Previous 50 MHz", self.previous_band),
            ("next", "Next 50 MHz", self.next_band),
            ("undo", "Undo", self.undo),
            ("clear", "Clear", self.clear),
            ("refresh", "Refresh", self.redraw),
            ("save", "Save draft", self.save_draft),
            ("quit", "Quit", self.close),
        ]
        left, gap = 0.07, 0.008
        width = (0.78 - gap * (len(controls) - 1)) / len(controls)
        for index, (key, label, callback) in enumerate(controls):
            self._make_button(
                key,
                label,
                (left + index * (width + gap), 0.075, width, 0.045),
                callback,
            )
        self._status_artist = self.figure.text(0.07, 0.025, "", fontsize=9)
        self.figure.text(
            0.91,
            0.64,
            "Drag vertically\non any panel.\n\nShortcuts:\nF flag\nU unflag\n←/→ bands\nS save",
            va="top",
            fontsize=8,
        )
        self.figure.canvas.mpl_connect("key_press_event", self._on_key)
        self._draw_panels()
        self._set_status(self.status_message)
        return self.figure

    def redraw(self) -> None:
        if self.figure is None:
            return
        self._draw_panels()
        self._set_status(self.status_message)
        self.figure.canvas.draw_idle()

    def show(self) -> None:
        import matplotlib.pyplot as plt

        self.build()
        plt.show(block=True)

    def close(self) -> None:
        import matplotlib.pyplot as plt

        self._disconnect_selectors()
        if self.figure is not None:
            plt.close(self.figure)
            self.figure = None


def parser() -> argparse.ArgumentParser:
    root = Path(__file__).parents[1]
    default_bundle = Path(
        "/Users/jakobfaber/Data/Faber2026/review/manual-bad-channels/"
        "zach-chime/zach_chime_manual_review_bundle.npz"
    )
    default_map = root / "analysis/rfi/manual-bad-channels/chime-frb/zach.json"
    command = argparse.ArgumentParser(description=__doc__)
    command.add_argument("--bundle", type=Path, default=default_bundle)
    command.add_argument("--map", dest="map_path", type=Path, default=default_map)
    command.add_argument("--output-map", type=Path, default=default_map)
    command.add_argument("--frequency-low", type=float, default=700.0)
    command.add_argument("--frequency-high", type=float, default=750.0)
    command.add_argument("--band-width", type=float, default=50.0)
    command.add_argument("--reason", default="owner manual selection")
    command.add_argument("--evidence")
    command.add_argument("--backend", default="macosx")
    return command


def main() -> int:
    args = parser().parse_args()
    import matplotlib

    matplotlib.use(args.backend, force=True)
    gui = ManualBadChannelGUI(
        bundle_path=args.bundle,
        map_path=args.map_path,
        output_map_path=args.output_map,
        default_frequency_window=(args.frequency_low, args.frequency_high),
        band_width_mhz=args.band_width,
        reason=args.reason,
        evidence=args.evidence,
    )
    gui.show()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
