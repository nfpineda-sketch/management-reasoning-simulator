"""P3-149 and P3-150: the faculty and development OBSERVER of a persisted shadow trace. Read-only.

It shows one shadow encounter to a faculty or development reader: which family and case, which common core,
whether the arrival was eligible, the actions the engine executed and the minute each takes effect, every
run kept apart, the key channels over time, what failed, and whether the trace replays.

What it cannot do, by construction and by test:

- it issues no order, alters no state, selects no authority, changes no score, and makes no witness "the
  active one": it takes a trace -- plain data -- and returns plain data or a page;
- it is not part of the encounter page. No resident-facing module imports it (the store's own
  ``RESIDENT_READERS_FORBIDDEN`` names them), so a resident cannot reach anything here;
- it writes nothing but the report a reader asks for, and never inside the repository.

LOW, CENTER_REFERENCE and HIGH are DEVELOPMENT TEST WITNESSES of a development region. None is the answer,
CENTER_REFERENCE least of all; the envelope is a derived summary of the three and not a trajectory.

Use, as a tool:  python3 -m runtime_shadow_observer --store DIR --list
                 python3 -m runtime_shadow_observer --store DIR --id TRACE_ID --out REPORT.html
"""
from __future__ import annotations

import argparse
import html
import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence

import runtime_shadow_families as fam
import runtime_shadow_store as store

OBSERVER_VERSION = "P3-149"
#: The channels shown per family, in order: (channel, label, unit). The core's own names and readings, and
#: the units the core itself states for them; where it states none, the label says "core units".
CHANNELS = {
    "opioid": (("central_availability", "Central availability", "fraction"),
               ("respiratory_rate", "Respiratory rate", "breaths/min"),
               ("ventilation", "Ventilation (W)", "relative to need"),
               ("paco2", "PaCO2", "mmHg"),
               ("spo2", "SpO2", "%"),
               ("delivery_rel", "Oxygen delivery (DO2)", "relative to arrival")),
    "gi_bleed": (("V", "Volume channel (V)", "core units"),
                 ("map", "Mean arterial pressure", "mmHg"),
                 ("monitor_rate_bpm", "Heart rate", "beats/min"),
                 ("hb", "Haemoglobin", "g/dL"),
                 ("spo2", "SpO2", "%"),
                 ("delivery_rel", "Oxygen delivery (DO2)", "relative to arrival"),
                 # P3-174: the Amendment-2 witnesses only (the session's own run, committed profile, carries none of these)
                 ("relative_delivery", "Delivery relative to arrival (Amendment 2)", "fraction of arrival"),
                 ("relative_perfusion", "Perfusion relative to arrival (Amendment 2)", "fraction of arrival"),
                 (fam.TRACE_AMENDMENT_2[0], "Systemic burden F (Amendment 2)", "fraction, 0 to 1"),
                 ("collapse_burden", "Collapse burden (Amendment 2)", "fraction, 0 to 1"),
                 ("category_index", "Observable category (0 none, 1 somnolent, 2 obtunded, 3 unresponsive)", "index")),
}
DEFAULT_CHANNELS = (("map", "Mean arterial pressure", "mmHg"), ("monitor_rate_bpm", "Heart rate", "beats/min"),
                    ("respiratory_rate", "Respiratory rate", "breaths/min"), ("spo2", "SpO2", "%"),
                    ("delivery_rel", "Oxygen delivery (DO2)", "relative to arrival"))
WITNESS_LABEL = "DEVELOPMENT TEST WITNESS"
SESSION_LABEL = "SESSION RUN"
ENVELOPE_LABEL = "Envelope: minimum to maximum of the witnesses, a derived summary and not a trajectory"
CONDITION_TEXT = {
    "clock_at_arrival": "No time has passed: the encounter's clock and the engine's own are at 0",
    "engine_state_is_a_fresh_arrival": "The engine's state is a fresh arrival's, field by field",
    "monitor_is_the_authored_arrival": "The monitor shows the authored arrival and nothing else",
    "nothing_administered": "Nothing has been administered, ordered or disposed",
    "nothing_on_the_diagnostic_record": "Nothing is on the diagnostic record",
}
STATE_TEXT = {
    fam.COMPLETE: "Every run reached the encounter's minute and nothing was reported",
    fam.COMPLETE_WITH_UNSUPPORTED_ACTIONS: "Every run reached the encounter's minute; some executed actions "
                                           "have no representation in the shadow",
    fam.PARTIAL: "The session ran, but not all of it: see what is missing below",
    fam.FAILED: "The session's run failed or does not replay",
    fam.REJECTED: "The arrival was rejected: nothing ran, and the encounter was legacy-only",
}
#: Status role of each state, for the page's reserved status colours (always with an icon and a label).
STATE_ROLE = {fam.COMPLETE: "good", fam.COMPLETE_WITH_UNSUPPORTED_ACTIONS: "warning", fam.PARTIAL: "serious",
              fam.FAILED: "critical", fam.REJECTED: "critical"}
ROLE_ICON = {"good": "✓", "warning": "!", "serious": "▲", "critical": "✕"}


# -- the view: plain data from plain data -------------------------------------------------------------------------

def _number_or_none(value: Any) -> float | None:
    """A finite number, or None. Nothing that is not a finite number is ever drawn or formatted as one."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return value


def _run_label(name: str, run: Mapping) -> str:
    if run.get("role") == store.WITNESS_RUN:
        parameter = run.get("parameter") if isinstance(run.get("parameter"), Mapping) else {}
        value = _number_or_none(parameter.get("declared"))
        return f"{WITNESS_LABEL} · {name} ({value:g})" if value is not None else \
            f"{WITNESS_LABEL} · {name}"
    return SESSION_LABEL


def _ordered_runs(trace: Mapping) -> list:
    """The runs in reading order: the session's own run, then the witnesses as the family declares them."""
    runs = {str(name): run for name, run in trace["runs"].items() if isinstance(run, Mapping)} \
        if isinstance(trace.get("runs"), Mapping) else {}
    order = [store.SESSION_RUN_NAME] + [str(name) for name in (trace.get("expected_witnesses") or [])]
    names = [name for name in order if name in runs] + sorted(name for name in runs if name not in order)
    return [(name, runs[name]) for name in names]


def _series(trace: Mapping, channel: str) -> list:
    out = []
    for name, run in _ordered_runs(trace):
        points = []
        for row in run.get("minutes") or []:
            channels = row.get("channels") if isinstance(row, Mapping) else None
            value = _number_or_none(channels.get(channel)) if isinstance(channels, Mapping) else None
            if value is not None and isinstance(row.get("minute"), int) and not isinstance(row.get("minute"), bool):
                points.append([row["minute"], value])
        if points:
            out.append({"run": name, "label": _run_label(name, run), "role": run.get("role"), "points": points})
    return out


def _envelope(series: Sequence) -> dict | None:
    """Minimum and maximum of the WITNESSES per minute, only where every witness has that minute."""
    witnesses = [item for item in series if item["role"] == store.WITNESS_RUN]
    if len(witnesses) < 2:
        return None
    by_minute = [dict(item["points"]) for item in witnesses]
    common = sorted(set(by_minute[0]).intersection(*by_minute[1:]))
    if not common:
        return None
    return {"label": ENVELOPE_LABEL, "minutes": common,
            "min": [min(points[m] for points in by_minute) for m in common],
            "max": [max(points[m] for points in by_minute) for m in common],
            "witnesses": [item["run"] for item in witnesses]}


def view(trace: Mapping, *, replay: Mapping | None = None) -> dict:
    """The read-only view of one persisted trace. Pure: the trace it is given is never changed.

    ``replay`` is ``runtime_shadow_store.replay(trace)`` when the reader asked for one; it is folded into the
    status, so a trace that does not replay is never shown as complete.
    """
    trace = deepcopy(dict(trace))
    family = str(trace.get("family") or "")
    # Integrity is checked for EVERY view, replayed or not: a trace that does not pass verification is never
    # shown with the status it carries, and the page says it is not verified.
    checked = store.verify(trace)
    folded = replay if replay is not None or checked["verified"] else {
        "reproduces": False, "refused": fam.REPLAY_MISMATCH, "why": checked["why"], "runs": {}}
    recorded = trace.get("status") if isinstance(trace.get("status"), Mapping) else {}
    status = fam.status_with_replay(recorded, folded)
    channels = []
    for key, label, unit in CHANNELS.get(family, DEFAULT_CHANNELS):
        series = _series(trace, key)
        if series:
            channels.append({"key": key, "label": label, "unit": unit, "series": series,
                             "envelope": _envelope(series)})
    runs = []
    for name, run in _ordered_runs(trace):
        runs.append({"name": name, "label": _run_label(name, run), "role": run.get("role"),
                     "witness": run.get("witness"), "parameter": run.get("parameter"),
                     "adapter": run.get("adapter"), "snapshot": (run.get("snapshot") or {}).get("id"),
                     "minutes": len(run.get("minutes") or []), "last_valid_minute": run.get("last_valid_minute"),
                     "failed": bool(run.get("failed")), "failures": list(run.get("failures") or []),
                     "replay": ((replay or {}).get("runs") or {}).get(name)})
    eligibility = trace.get("arrival") if isinstance(trace.get("arrival"), Mapping) else {}
    differences = [(list(row) + [None, None, None])[:3] for row in (eligibility.get("differences") or [])
                   if isinstance(row, (list, tuple))]
    actions = [{key: row.get(key) for key in ("shadow_order_id", "order_minute", "placed_minute", "kind", "order_id",
                                              "submission_id", "disposition", "effective_minute", "why")}
               for row in (trace.get("actions") or []) if isinstance(row, Mapping)]
    return {
        "observer": OBSERVER_VERSION,
        "provenance": {"authority": trace.get("authority"), "use": trace.get("use"),
                       "resident_visible": trace.get("resident_visible"),
                       "runtime_authority": trace.get("runtime_authority"),
                       "common_core_runtime_authority": trace.get("common_core_runtime_authority")},
        "identity": {"family": family, "case_id": trace.get("case_id"), "encounter_id": trace.get("encounter_id"),
                     "session_minutes": trace.get("session_minutes"), "turns": trace.get("turns"),
                     "trace_digest": trace.get("trace_digest")},
        "lineage": dict(trace.get("lineage") or {}),
        "arrival": {"eligible": bool(eligibility.get("eligible")),
                    "conditions": [{"name": name, "holds": bool(holds), "text": CONDITION_TEXT.get(name, name)}
                                   for name, holds in (eligibility.get("conditions") or {}).items()],
                    "differences": differences},
        "integrity": {"verified": bool(checked["verified"]), "why": checked["why"],
                      "inconsistencies": list(checked.get("inconsistencies") or [])},
        "actions": actions,
        "region": trace.get("region"),
        "witness_policy": trace.get("witness_policy"),
        "selected_witness": None,
        "runs": runs,
        "channels": channels,
        "status": {**status, "text": STATE_TEXT.get(status.get("state"), ""),
                   "role": STATE_ROLE.get(status.get("state"), "critical")},
        "replay": ({"asked": False, "text": "not replayed for this view"} if replay is None else
                   {"asked": True, "replayed": bool(replay.get("replayed")),
                    "nothing_to_replay": bool(replay.get("nothing_to_replay")),
                    "reproduces": bool(replay.get("reproduces")), "refused": replay.get("refused"),
                    "why": replay.get("why") or "", "runs": dict(replay.get("runs") or {})}),
        "divergences": _divergence_counts(trace.get("divergences") or []),
    }


def _divergence_counts(divergences: Sequence) -> dict:
    counts: dict = {}
    for item in divergences:
        counts[str(item.get("status"))] = counts.get(str(item.get("status")), 0) + 1
    return dict(sorted(counts.items()))


# -- the page -----------------------------------------------------------------------------------------------------

_CSS = """
.viz-root{color-scheme:light;--surface-1:#fcfcfb;--page:#f9f9f7;--text-primary:#0b0b0b;--text-secondary:#52514e;
--muted:#898781;--grid:#e1e0d9;--axis:#c3c2b7;--border:rgba(11,11,11,0.10);--series-1:#2a78d6;
--w-low:#86b6ef;--w-center:#2a78d6;--w-high:#104281;--session:#898781;--band:#cde2fb;
--good:#0ca30c;--warning:#fab219;--serious:#ec835a;--critical:#d03b3b}
@media (prefers-color-scheme: dark){:root:where(:not([data-theme="light"])) .viz-root{color-scheme:dark;
--surface-1:#1a1a19;--page:#0d0d0d;--text-primary:#f0efec;--text-secondary:#c3c2b7;--muted:#898781;
--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,0.10);--series-1:#3987e5;
--w-low:#184f95;--w-center:#3987e5;--w-high:#9ec5f4;--session:#898781;--band:#0d366b}}
:root[data-theme="dark"] .viz-root{color-scheme:dark;--surface-1:#1a1a19;--page:#0d0d0d;--text-primary:#f0efec;
--text-secondary:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,0.10);
--series-1:#3987e5;--w-low:#184f95;--w-center:#3987e5;--w-high:#9ec5f4;--session:#898781;--band:#0d366b}
html,body{margin:0}
.viz-root{background:var(--page);color:var(--text-primary);font:14px/1.45 system-ui,-apple-system,"Segoe UI",
sans-serif;padding:16px;min-height:100vh;box-sizing:border-box}
.wrap{max-width:1120px;margin:0 auto}
h1{font-size:20px;margin:0 0 4px}h2{font-size:15px;margin:24px 0 8px}
.banner{border:1px solid var(--border);border-left:4px solid var(--critical);background:var(--surface-1);
padding:10px 12px;border-radius:6px;margin:0 0 16px;color:var(--text-secondary)}
.banner strong{color:var(--text-primary)}
.card{background:var(--surface-1);border:1px solid var(--border);border-radius:8px;padding:12px;overflow-x:auto}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:4px 10px 4px 0;border-bottom:1px solid var(--grid);vertical-align:top}
th{color:var(--text-secondary);font-weight:600}td.num,th.num{text-align:right}
.muted{color:var(--text-secondary)}.mono{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;
word-break:break-all}
.chip{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--border);border-radius:999px;
padding:2px 10px;background:var(--surface-1);font-weight:600}
.dot{width:16px;height:16px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;
font-size:11px;color:#fff;line-height:1}
.dot.good{background:var(--good)}.dot.warning{background:var(--warning);color:#0b0b0b}
.dot.serious{background:var(--serious)}.dot.critical{background:var(--critical)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px}
.legend{display:flex;flex-wrap:wrap;gap:6px 16px;margin:0 0 10px;color:var(--text-secondary)}
.key{display:inline-flex;align-items:center;gap:6px}.key i{display:inline-block;width:18px;height:0;
border-top:2px solid}.key i.band{height:10px;border:0;background:var(--band)}
figure{margin:0}figcaption{font-weight:600;margin:0 0 2px}figcaption span{font-weight:400;
color:var(--text-secondary)}
svg{display:block;width:100%;height:auto;overflow:visible}svg text{fill:var(--muted);font-size:11px}
svg text.end{fill:var(--text-secondary)}.chart{position:relative;outline:none}
.chart:focus-visible{box-shadow:0 0 0 2px var(--series-1);border-radius:4px}
.tip{position:absolute;pointer-events:none;background:var(--surface-1);border:1px solid var(--border);
border-radius:6px;padding:6px 8px;font-size:12px;box-shadow:0 2px 8px rgba(0,0,0,.12);display:none;
white-space:nowrap;z-index:2}
.tip b{color:var(--text-primary)}.tip div{display:flex;align-items:center;gap:6px;color:var(--text-secondary)}
.tip i{display:inline-block;width:12px;border-top:2px solid}
details{margin-top:8px}summary{cursor:pointer;color:var(--text-secondary)}
"""

_JS = """
(function(){
  var data = JSON.parse(document.getElementById('viz-data').textContent);
  document.querySelectorAll('.chart').forEach(function(box){
    var chart = data[box.dataset.chart], svg = box.querySelector('svg'), tip = box.querySelector('.tip');
    var hair = svg.querySelector('.hair'), index = -1;
    function show(i){
      if(i < 0 || i >= chart.minutes.length){ return; }
      index = i;
      var x = chart.x[i];
      hair.setAttribute('x1', x); hair.setAttribute('x2', x); hair.style.display = '';
      while(tip.firstChild){ tip.removeChild(tip.firstChild); }
      var head = document.createElement('b'); head.textContent = 'Minute ' + chart.minutes[i]; tip.appendChild(head);
      chart.series.forEach(function(s){
        var v = s.values[i]; if(v === null || v === undefined){ return; }
        var row = document.createElement('div'), key = document.createElement('i'), val = document.createElement('b');
        key.style.borderTopColor = 'var(' + s.color + ')';
        val.textContent = (Math.round(v * 1000) / 1000).toString();
        var name = document.createElement('span'); name.textContent = s.label;
        row.appendChild(key); row.appendChild(val); row.appendChild(name); tip.appendChild(row);
      });
      tip.style.display = 'block';
      var rect = svg.getBoundingClientRect(), px = x / chart.width * rect.width;
      tip.style.left = Math.min(Math.max(px + 10, 0), Math.max(rect.width - tip.offsetWidth, 0)) + 'px';
      tip.style.top = '8px';
    }
    function hide(){ tip.style.display = 'none'; hair.style.display = 'none'; index = -1; }
    box.addEventListener('pointermove', function(e){
      var rect = svg.getBoundingClientRect(), x = (e.clientX - rect.left) / rect.width * chart.width;
      var best = 0, gap = Infinity;
      chart.x.forEach(function(v, i){ var d = Math.abs(v - x); if(d < gap){ gap = d; best = i; } });
      show(best);
    });
    box.addEventListener('pointerleave', hide);
    box.addEventListener('blur', hide);
    box.addEventListener('focus', function(){ show(chart.minutes.length - 1); });
    box.addEventListener('keydown', function(e){
      if(e.key === 'ArrowLeft'){ show(Math.max(index - 1, 0)); e.preventDefault(); }
      if(e.key === 'ArrowRight'){ show(Math.min(index + 1, chart.minutes.length - 1)); e.preventDefault(); }
      if(e.key === 'Escape'){ hide(); }
    });
  });
})();
"""


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def _color(series: Mapping, witness_count: int) -> str:
    """The colour ROLE of a series. The witnesses are an ordered tier, so they take one hue stepped by order;
    the session's run takes the series colour when it is alone and the neutral one beside witnesses."""
    if series["role"] == store.WITNESS_RUN:
        return {"LOW": "--w-low", "CENTER_REFERENCE": "--w-center", "HIGH": "--w-high"}.get(series["run"],
                                                                                              "--w-center")
    return "--session" if witness_count else "--series-1"


def _ticks(low: float, high: float, count: int = 4) -> tuple:
    """Clean, round tick values that always span [low, high], and the decimals their labels need."""
    if high - low < 1e-9:
        pad = max(abs(low) * 0.01, 0.01)
        low, high = low - pad, high + pad
    raw = (high - low) / max(count, 1)
    magnitude = 10 ** math.floor(math.log10(raw))
    step = next(m * magnitude for m in (1, 2, 2.5, 5, 10) if m * magnitude >= raw * (1 - 1e-9))
    first = math.floor(low / step + 1e-9) * step
    ticks = [first]
    while ticks[-1] < high - step * 1e-6 and len(ticks) < 16:
        ticks.append(first + step * len(ticks))
    decimals = max(0, min(6, -math.floor(math.log10(step) + 1e-9))) + (1 if step / magnitude == 2.5 else 0)
    return [round(value, 10) for value in ticks], decimals


def _number(value: float, decimals: int | None = None) -> str:
    if decimals is not None:
        text = f"{value:.{decimals}f}"
    else:
        text = f"{value:.3f}".rstrip("0").rstrip(".") if abs(value) < 1000 else f"{value:,.0f}"
    return "0" if text in ("-0", "") or (text.strip("-0.") == "" and decimals is None) else text


def _chart(channel: Mapping, index: int) -> tuple:
    """(svg markup, data for the hover layer) of one channel: one panel, one axis, every run its own line."""
    width, height, left, right, top, bottom = 360.0, 200.0, 46.0, 74.0, 10.0, 24.0
    series = channel["series"]
    witnesses = sum(1 for item in series if item["role"] == store.WITNESS_RUN)
    minutes = sorted({point[0] for item in series for point in item["points"]})
    values = [point[1] for item in series for point in item["points"]]
    ticks, decimals = _ticks(min(values), max(values))
    low, high = ticks[0], ticks[-1]
    first, last = minutes[0], max(minutes[-1], minutes[0] + 1)

    def x_of(minute):
        return left + (minute - first) / (last - first) * (width - left - right)

    def y_of(value):
        return top + (high - value) / (high - low) * (height - top - bottom)

    parts = [f'<svg viewBox="0 0 {width:g} {height:g}" role="img" aria-label="{_e(channel["label"])} over time, '
             f'one line per run">']
    for tick in ticks:
        y = y_of(tick)
        parts.append(f'<line x1="{left:g}" x2="{width - right:g}" y1="{y:.1f}" y2="{y:.1f}" stroke="var(--grid)" '
                     f'stroke-width="1"/><text x="{left - 6:g}" y="{y + 3.5:.1f}" text-anchor="end">'
                     f'{_e(_number(tick, decimals))}</text>')
    parts.append(f'<line x1="{left:g}" x2="{width - right:g}" y1="{height - bottom:g}" y2="{height - bottom:g}" '
                 f'stroke="var(--axis)" stroke-width="1"/>')
    for minute in sorted({first, minutes[len(minutes) // 2], minutes[-1]}):
        parts.append(f'<text x="{x_of(minute):.1f}" y="{height - 8:g}" text-anchor="middle">{minute} min</text>')
    envelope = channel.get("envelope")
    if envelope:
        upper = " ".join(f"{x_of(m):.1f},{y_of(v):.1f}" for m, v in zip(envelope["minutes"], envelope["max"]))
        lower = " ".join(f"{x_of(m):.1f},{y_of(v):.1f}" for m, v in
                         reversed(list(zip(envelope["minutes"], envelope["min"]))))
        parts.append(f'<polygon points="{upper} {lower}" fill="var(--band)" opacity="0.55"/>')
    short = lambda name: "session" if name == store.SESSION_RUN_NAME else name.replace("_REFERENCE", "")
    ends, stopped = [], []
    for item in series:
        color = _color(item, witnesses)
        path = " ".join(f"{x_of(m):.1f},{y_of(v):.1f}" for m, v in item["points"])
        parts.append(f'<polyline points="{path}" fill="none" stroke="var({color})" stroke-width="2" '
                     f'stroke-linejoin="round" stroke-linecap="round"/>')
        last_minute, last_value = item["points"][-1]
        if last_minute < minutes[-1]:
            stopped.append((x_of(last_minute), y_of(last_value), item["run"], color, last_minute))
        else:
            ends.append((y_of(last_value), x_of(last_minute), item["run"], color))
    # A run that stopped early ends WHERE IT STOPPED: a ring on its last recorded minute and its label beside
    # it. Nothing is drawn past that minute -- no line, no leader -- so a failed run never reads as a course.
    for index, (x, y, name, color, minute) in enumerate(stopped):
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="var(--surface-1)" stroke="var({color})" '
                     f'stroke-width="2"/><text class="end" x="{x + 8:.1f}" y="{max(top + 9, y - 7 - 12 * index):.1f}">'
                     f'{_e(short(name))} stopped at min {minute}</text>')
    # direct labels at the line ends; runs that end together share one label, and labels never overlap
    ends.sort()
    groups: list = []
    for y, x, name, color in ends:
        if groups and abs(groups[-1]["y"] - y) < 1.0:
            groups[-1]["names"].append(name)
        else:
            groups.append({"y": y, "x": x, "names": [name], "color": color})
    place = top + 4
    for group in groups:
        place = max(place, group["y"])
        count = len(group["names"])
        label = ("all runs" if count == len(series) > 1 else f"{count} runs" if count > 2 else
                 " = ".join(short(name) for name in group["names"]))
        parts.append(f'<line x1="{group["x"]:.1f}" x2="{width - right + 8:g}" y1="{group["y"]:.1f}" '
                     f'y2="{place:.1f}" stroke="var(--axis)" stroke-width="1"/>'
                     f'<text class="end" x="{width - right + 11:g}" y="{place + 3.5:.1f}">{_e(label)}</text>')
        place += 13
    parts.append(f'<line class="hair" x1="0" x2="0" y1="{top:g}" y2="{height - bottom:g}" stroke="var(--axis)" '
                 f'stroke-width="1" style="display:none"/></svg>')
    data = {"width": width, "minutes": minutes, "x": [round(x_of(m), 2) for m in minutes],
            "series": [{"label": item["label"], "color": _color(item, witnesses),
                        "values": [dict(item["points"]).get(m) for m in minutes]} for item in series]}
    return "".join(parts), data


def _in_run_order(shown: Mapping, rows: Mapping) -> list:
    """Replay rows in the order the runs are shown, then any the trace does not hold (a missing witness)."""
    order = [run["name"] for run in shown["runs"]]
    return [(name, rows[name]) for name in order if name in rows] + sorted(
        (name, row) for name, row in rows.items() if name not in order)


def _table(headers: Sequence, rows: Sequence, numeric: Sequence = ()) -> str:
    head = "".join(f'<th class="{"num" if i in numeric else ""}">{_e(h)}</th>' for i, h in enumerate(headers))
    body = "".join("<tr>" + "".join(f'<td class="{"num" if i in numeric else ""}">{cell}</td>'
                                    for i, cell in enumerate(row)) + "</tr>" for row in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _chip(role: str, label: str) -> str:
    return (f'<span class="chip"><span class="dot {_e(role)}" aria-hidden="true">{_e(ROLE_ICON.get(role, "!"))}'
            f'</span>{_e(label)}</span>')


def render_html(shown: Mapping) -> str:
    """One self-contained page for one view. Every label that comes from data is escaped."""
    identity, lineage, status = shown["identity"], shown["lineage"], shown["status"]
    out = ['<!doctype html><html lang="en"><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width, initial-scale=1">'
           f'<title>Shadow trace · {_e(identity["family"])} · {_e(identity["case_id"])}</title>'
           f'<style>{_CSS}</style></head><body><div class="viz-root"><div class="wrap">']
    out.append('<div class="banner"><strong>NONAUTHORITATIVE SHADOW · DEVELOPMENT ONLY.</strong> '
               'Faculty and development view of a shadow trace. The legacy engine was the only runtime '
               'authority in this encounter; nothing here was shown to a resident, entered a score or changed '
               'the patient. This page is read-only and is not clinical validation.</div>')
    out.append(f'<h1>Shadow trace · {_e(identity["family"])} · {_e(identity["case_id"])}</h1>')
    out.append(f'<p class="muted">{_e(identity["session_minutes"])} minutes · {_e(identity["turns"])} turns '
               f'· observer {_e(shown["observer"])}</p>')
    out.append('<h2>Status</h2><div class="card">'
               f'<p>{_chip(status["role"], status["state"])} <span class="muted">{_e(status["text"])}</span></p>')
    integrity = shown["integrity"]
    out.append(f'<p>{_chip("good" if integrity["verified"] else "critical", "TRACE VERIFIED" if integrity["verified"] else "TRACE NOT VERIFIED")}'
               f' <span class="muted">{_e("labelled, sealed and consistent with itself" if integrity["verified"] else integrity["why"])}</span></p>')
    if status["items"]:
        out.append(_table(("Code", "Where", "Minute", "Detail"),
                          [(_e(item["code"]), _e(item["where"]), _e(item["minute"]), _e(item["detail"]))
                           for item in status["items"]], numeric=(2,)))
    else:
        out.append('<p class="muted">Nothing was reported.</p>')
    out.append("</div>")
    out.append('<h2>Common core and arrival</h2><div class="card">')
    out.append(_table(("Common core", "Core digest", "Lineage", "Historical closure"),
                      [(_e(lineage.get("core_version")),
                        f'<span class="mono">{_e(lineage.get("core_digest"))}</span>',
                        _chip("good" if lineage.get("certified") else "critical",
                              "CERTIFIED MEMBER" if lineage.get("certified") else "NOT CERTIFIED"),
                        f'<span class="mono">{_e(str(lineage.get("phase2_digest"))[:16])}…</span>')]))
    arrival = shown["arrival"]
    out.append(f'<p>{_chip("good" if arrival["eligible"] else "critical", "ARRIVAL ELIGIBLE" if arrival["eligible"] else "ARRIVAL REJECTED")}'
               f' <span class="mono muted">{_e(identity["encounter_id"])}</span></p>')
    out.append(_table(("Arrival condition", "Holds"),
                      [(_e(item["text"]), _chip("good" if item["holds"] else "critical",
                                                "yes" if item["holds"] else "no"))
                       for item in arrival["conditions"]]))
    if arrival["differences"]:
        out.append("<details><summary>What differs from an untouched arrival</summary>" + _table(
            ("Field", "Live", "Arrival"),
            [(_e(row[0]), _e(row[1]), _e(row[2])) for row in arrival["differences"]]) + "</details>")
    out.append("</div>")
    out.append('<h2>Actions the engine executed</h2><div class="card">')
    if shown["actions"]:
        out.append(_table(("Order minute", "Effective minute", "Action", "Disposition", "Why"),
                          [(_e(row["order_minute"]), _e("—" if row["effective_minute"] is None
                                                         else row["effective_minute"]),
                            _e(row["kind"]), _e(row["disposition"]), _e(row["why"]))
                           for row in shown["actions"]], numeric=(0, 1)))
        out.append('<p class="muted">An action the engine executed at minute m is first present in the shadow '
                   'state of the effective minute. An order held until a result is mirrored at the minute the '
                   'engine really ran it, never at the minute it was placed; HELD_NOT_EXECUTED is one the engine '
                   'has not run. FROM_ENGINE_STATE is a contributor the run carries that no order explains; '
                   'NOT_MIRRORED is an order the shadow could not mirror, so the run does not carry it.</p>')
    else:
        out.append('<p class="muted">No action was executed.</p>')
    out.append("</div>")
    out.append('<h2>Runs</h2><div class="card">')
    if shown["region"]:
        region = shown["region"]
        out.append(f'<p class="muted">LOW, CENTER_REFERENCE and HIGH are <strong>development test '
                   f'witnesses</strong> of {_e(region["classification"])} for '
                   f'<span class="mono">{_e(region["parameter"])}</span>. None is selected, preferred or '
                   f'averaged, and CENTER_REFERENCE is not the answer. The session run uses the committed '
                   f'profile.</p>')
    rows = []
    for run in shown["runs"]:
        value = _number_or_none(run["parameter"].get("declared")
                                if isinstance(run["parameter"], Mapping) else None)
        replayed = run.get("replay")
        rows.append((_e(run["label"]), _e("—" if value is None else f"{value:g}"), _e(run["minutes"]),
                     _e(run["last_valid_minute"]),
                     _chip("critical", "FAILED") if run["failed"] else _chip("good", "ran"),
                     "<span class=\"muted\">not replayed</span>" if replayed is None else
                     _chip("good" if replayed["reproduces"] else "critical",
                           "replays exactly" if replayed["reproduces"] else "REPLAY MISMATCH")))
    out.append(_table(("Run", "Parameter value", "Minutes", "Last valid minute", "Run", "Replay"), rows,
                      numeric=(1, 2, 3)) if rows else '<p class="muted">No run opened.</p>')
    out.append("</div>")
    data: dict = {}
    if shown["channels"]:
        out.append('<h2>Key channels over time</h2><div class="card"><div class="legend">')
        seen = []
        witnesses = any(item["role"] == store.WITNESS_RUN for item in shown["channels"][0]["series"])
        for item in shown["channels"][0]["series"]:
            if item["run"] not in seen:
                seen.append(item["run"])
                out.append(f'<span class="key"><i style="border-top-color:var({_color(item, int(witnesses))})">'
                           f'</i>{_e(item["label"])}</span>')
        if any(channel.get("envelope") for channel in shown["channels"]):
            out.append(f'<span class="key"><i class="band"></i>{_e(ENVELOPE_LABEL)}</span>')
        out.append('</div><div class="grid">')
        for index, channel in enumerate(shown["channels"]):
            svg, chart = _chart(channel, index)
            data[str(index)] = chart
            out.append(f'<figure><figcaption>{_e(channel["label"])} <span>{_e(channel["unit"])}</span>'
                       f'</figcaption><div class="chart" tabindex="0" data-chart="{index}">{svg}'
                       f'<div class="tip" role="status"></div></div></figure>')
        out.append("</div><details><summary>Table view: every run, every channel</summary>")
        for channel in shown["channels"]:
            minutes = sorted({point[0] for item in channel["series"] for point in item["points"]})
            picked = sorted(set(minutes[::max(len(minutes) // 8, 1)]) | {minutes[-1]})
            lookup = [dict(item["points"]) for item in channel["series"]]
            out.append(f'<p><strong>{_e(channel["label"])}</strong> <span class="muted">{_e(channel["unit"])}'
                       f'</span></p>' + _table(
                ["Minute"] + [item["label"] for item in channel["series"]],
                [[_e(minute)] + [_e("" if points.get(minute) is None else _number(points[minute]))
                                 for points in lookup] for minute in picked],
                numeric=tuple(range(len(channel["series"]) + 1))))
        out.append("</details></div>")
    replay = shown["replay"]
    out.append('<h2>Replay</h2><div class="card">')
    if not replay["asked"]:
        out.append('<p class="muted">This view was built without replaying the trace.</p>')
    elif replay.get("nothing_to_replay"):
        out.append(f'<p>{_chip("serious", "NOTHING TO REPLAY")} <span class="muted">{_e(replay["why"])}</span></p>')
    elif not replay["replayed"]:
        out.append(f'<p>{_chip("critical", replay.get("refused") or "NOT REPLAYED")} '
                   f'<span class="muted">{_e(replay["why"])}</span></p>')
    else:
        out.append(f'<p>{_chip("good" if replay["reproduces"] else "critical", "REPLAYS EXACTLY" if replay["reproduces"] else "REPLAY MISMATCH")}'
                   f' <span class="muted">every run replayed from its own artifact; state and readings '
                   f'compared minute by minute</span></p>')
        out.append(_table(("Run", "Recorded minutes", "Replayed minutes", "First mismatch", "Note"),
                          [(_e(name), _e(row["recorded"]), _e(row["minutes"]),
                            _e("—" if row["first_mismatch"] is None else row["first_mismatch"]),
                            _e(row["why"])) for name, row in _in_run_order(shown, replay["runs"])],
                          numeric=(1, 2, 3)))
    out.append("</div>")
    if shown["divergences"]:
        out.append('<h2>Differences from the legacy engine</h2><div class="card">' + _table(
            ("Class", "Count"), [(_e(name), _e(count)) for name, count in shown["divergences"].items()],
            numeric=(1,)) + '<p class="muted">A difference is two architectures differing. The legacy engine '
                            'is not clinical ground truth and is never a calibration target.</p></div>')
    out.append(f'<p class="muted mono">trace {_e(identity["trace_digest"])}</p>')
    # data can never close, open or comment out the script element: no angle bracket or ampersand survives
    embedded = (json.dumps(data, allow_nan=False).replace("<", "\\u003c").replace(">", "\\u003e")
                .replace("&", "\\u0026"))
    out.append(f'</div></div><script type="application/json" id="viz-data">{embedded}</script>'
               f'<script>{_JS}</script></body></html>')
    return "".join(out)


# -- the tool -----------------------------------------------------------------------------------------------------

# -- P3-162: the faculty trace-review package ---------------------------------------------------------------------

#: The channel each mapped treatment is EXPECTED to move first: the state variable its certified contributor
#: writes. Declared here so a reviewer can hold the observed first effect against it; a treatment with no
#: entry has no declared expectation and says so. Nothing here is a magnitude or a clinical claim.
EXPECTED_FIRST_CHANNEL = {
    "crystalloid": "V", "packed_red_cells": "V", "proton_pump_inhibitor": "V", "oxygen": "fio2",
    "naloxone_reversal": "central_availability",
}
NOT_ATTRIBUTABLE = "NOT_ATTRIBUTABLE"
#: What a faculty reviewer is asked. Judgment only: nothing about the implementation.
FACULTY_QUESTIONS = {
    "gi_bleed": (
        "Is the ORDER in which the channels respond to each treatment the order you would expect in this "
        "patient (what moves first, what follows)?",
        "Is the untreated course believable as a direction (it is not calibrated as a speed)?",
        "Which treatments a resident would reasonably give here are marked as not represented, and does "
        "their absence change what the trace can be used to discuss?",
        "Is this case a suitable candidate for a future resident case, and what would have to be true first?",
        # P3-177: the three Amendment-2 witnesses (consciousness and collapse). Judgment only; no witness is preferred.
        "Does the impairment appear too EARLY or too LATE in the untreated course, as a direction (it is not calibrated as "
        "a speed)? Read each witness apart: none is the answer.",
        "Does the recovery look too FAST or too SLOW once treatment restores delivery? The faculty reading is that the "
        "impairment, starting near 0.80, crosses below 0.50 in about 3 to 5 simulated minutes after the upstream physiology has "
        "recovered, without having to normalise below 0.25 in that interval.",
        "Is the category progression (none, somnolent, obtunded, unresponsive) educationally plausible, step by step?",
        "Does the collapse (impending, then established) appear too early or too late, and is it right that it needs both "
        "perfusion and delivery failing for minutes, never one alone?",
        "The two GI cases give the SAME shadow impairment timeline (it is read relative to each patient's own arrival) while "
        "the legacy ladder separates them by absolute pressure. Is that acceptable, or would any trajectory mislead a resident?",
        "An established collapse is physiological state only and does not end the encounter, which the legacy engine alone "
        "decides. Is the way the trace states that boundary clear enough to review without misreading it as an outcome?",
    ),
    "opioid": (
        "In this run every channel downstream of the reversal responds in the same simulated minute. Is a "
        "same-minute response acceptable, or do you expect a visible order (ventilation, then carbon "
        "dioxide, then oxygenation)?",
        "The speed at which the untreated patient worsens is a synthetic development value with no interval. "
        "What range of worsening, if any, would you accept for a development patient like this one?",
        "The three witness runs differ only in how strongly under-ventilation lowers oxygenation. Does any of "
        "the three look implausible as a direction? (None is preferred or selected.)",
        "The legacy patient can arrest while the shadow run still shows a pulse and a fixed level of "
        "consciousness. Is a terminal and consciousness representation required before this case could be "
        "discussed as a candidate resident case?",
    ),
}
UNRESOLVED_PARAMETERS = {
    "gi_bleed": ("the committed profile is a development default: no magnitude is faculty-approved",
                 "PHASE2_AMENDMENT_2 witnesses: every magnitude is a FACULTY_DEFINED_DEVELOPMENT_BEHAVIORAL_REGION, in three "
                 "named witnesses (LOW, CENTER_REFERENCE, HIGH), none selected, none calibrated, no clinical validation",
                 "the Amendment-2 composite is supported for GI only: opioid, ACS, pulmonary edema, embolism and asthma do "
                 "not declare it, and an opioid-specific consciousness mechanism is deferred"),
    "opioid": ("opioid deepening rate: one committed synthetic value, no interval (not identifiable from the "
               "repository's evidence)",
               "naloxone recovery rate: one committed synthetic value",
               "transmission fraction: a CONDITIONAL development region, valid only at the committed deepening "
               "rate; three witnesses, none selected",
               "respiratory quotient: declared for the development analysis"),
}


def _contributor_of(row: Mapping, contributors: Sequence, taken: set) -> Mapping | None:
    """The replay contributor one mirrored action built: by identity first, else the only untaken one that
    starts at the action's effective minute. None when it cannot be told."""
    named = [item for item in contributors if item.get("id") == row.get("shadow_order_id")]
    if len(named) == 1:
        return named[0]
    minute = row.get("effective_minute")
    if minute is None:
        return None
    timed = [item for item in contributors if item.get("id") not in taken and item.get("start_minute") == minute]
    return timed[0] if len(timed) == 1 else None


def first_effects(trace: Mapping, run_name: str | None = None) -> list:
    """For each treatment the shadow built: the first minute and the channels in which the run differs from
    the SAME run without that treatment, then the order in which the other channels follow. Never raises.

    The comparison run is the trace's own replay artifact with that one contributor removed, through the
    layer's one from-artifact path: no new physiology, nothing fitted. A treatment whose contributor cannot
    be told apart in the artifact is ``NOT_ATTRIBUTABLE``, not guessed.
    """
    out = []
    try:
        runs = trace.get("runs") or {}
        name = run_name or (store.SESSION_RUN_NAME if store.SESSION_RUN_NAME in runs else None)
        run = runs.get(name) or {}
        scenario = store.again_scenario(run.get("replay_input") or {})
        contributors = list(scenario.get("contributors") or [])
        built = [row for row in (trace.get("actions") or [])
                 if isinstance(row, Mapping) and row.get("disposition") == fam.BUILT]
        taken = {row.get("shadow_order_id") for row in built}
        whole = fam.artifact_rows(scenario) if built else []
        for row in built:
            entry = {"shadow_order_id": row.get("shadow_order_id"), "kind": row.get("kind"),
                     "order_minute": row.get("order_minute"), "effective_minute": row.get("effective_minute"),
                     "run": name, "contributor_type": None, "expected_first_channel": None,
                     "first_minute": None, "observed_first_channels": [], "downstream": [],
                     "expected_is_among_the_first": None, "status": NOT_ATTRIBUTABLE}
            item = _contributor_of(row, contributors, taken)
            if item is None:
                out.append(entry)
                continue
            without = dict(scenario, contributors=[other for other in contributors if other is not item])
            base = fam.artifact_rows(without)
            onset = {}
            for mine, theirs in zip(whole, base):
                for channel, value in mine["channels"].items():
                    if channel not in onset and value != theirs["channels"].get(channel):
                        onset[channel] = mine["minute"]
            order = sorted(onset.items(), key=lambda pair: (pair[1], pair[0]))
            start = order[0][1] if order else None
            expected = EXPECTED_FIRST_CHANNEL.get(str(item.get("type")))
            leading = [channel for channel, minute in order if minute == start]
            entry.update(contributor_type=item.get("type"), expected_first_channel=expected, first_minute=start,
                         observed_first_channels=leading,
                         downstream=[[channel, minute] for channel, minute in order if minute != start],
                         expected_is_among_the_first=None if expected is None else expected in leading,
                         status="NO_EFFECT_IN_THIS_RUN" if start is None else "OBSERVED")
            out.append(entry)
    except Exception as error:
        out.append({"status": "COULD_NOT_BE_COMPUTED", "why": f"{type(error).__name__}: {str(error)[:120]}"})
    return out


def _arrival_values(trace: Mapping) -> dict:
    run = (trace.get("runs") or {}).get(store.SESSION_RUN_NAME) or {}
    anchors = ((run.get("replay_input") or {}).get("scenario") or {}).get("anchors") or {}
    return {key: anchors.get(key) for key in ("sbp", "dbp", "hr", "spo2", "respiratory_rate", "lactate",
                                              "consciousness_level", "fio2") if key in anchors}


def review_entry(trace: Mapping) -> dict:
    """Everything the review package says about one persisted trace. Read-only; the trace is not changed."""
    trace = deepcopy(dict(trace))
    replay = store.replay(trace)
    shown = view(trace, replay=replay)
    family = shown["identity"]["family"]
    witnesses = [name for name in (trace.get("expected_witnesses") or [])]
    effects = {store.SESSION_RUN_NAME: first_effects(trace)}
    for name in witnesses:
        effects[name] = first_effects(trace, name)
    return {
        "identity": shown["identity"], "generation": trace.get("generation"), "status": shown["status"],
        "terminal_boundary": trace.get("terminal_boundary"),
        "integrity": shown["integrity"], "initial_state": _arrival_values(trace),
        "arrival_eligible": shown["arrival"]["eligible"],
        "actions": shown["actions"], "held_orders": list(trace.get("held_orders") or []),
        "first_effects": effects,
        "region": trace.get("region"), "witnesses": [
            {"name": run["name"], "parameter": run["parameter"], "failed": run["failed"],
             "last_valid_minute": run["last_valid_minute"]} for run in shown["runs"] if run["witness"]],
        "selected_witness": None,
        "failures": [failure for run in shown["runs"] for failure in run["failures"]],
        "replay": {"reproduces": bool(replay.get("reproduces")), "replayed": bool(replay.get("replayed")),
                   "refused": replay.get("refused")},
        "unresolved_synthetic_parameters": list(UNRESOLVED_PARAMETERS.get(family, ())),
        "faculty_questions": list(FACULTY_QUESTIONS.get(family, ())),
        "view": shown,
    }


def _write(path: Path, text: str) -> None:
    """The observer's ONE write: a page a reader asked for, at a place the caller has already checked is
    outside the repository. It never writes to the trace store."""
    path.parent.mkdir(parents=True, exist_ok=True)
    target = path.resolve()
    if path.is_symlink() or target == store.repository_root() or store.repository_root() in target.parents:
        raise PermissionError("a page is never written through a link or inside the repository")
    path.write_text(text, encoding="utf-8")


def _md(value: Any) -> str:
    text = str("" if value is None else value)
    for mark, plain in (("|", "/"), ("\n", " "), ("\r", " "), ("<", "‹"), (">", "›"), ("`", "'"), ("[", "("),
                        ("]", ")"), ("*", "·")):
        text = text.replace(mark, plain)
    return text


def review_markdown(entries: Sequence) -> str:
    """The index of a review package: one section per trace, plain markdown, faculty-judgment questions only."""
    lines = ["# Shadow trace review package — DEVELOPMENT ONLY", "",
             "Non-authoritative shadow runs recorded beside the legacy engine. Not shown to residents, not "
             "scored, not clinically validated. No witness is selected and no parameter is approved.", ""]
    for index, entry in enumerate(entries, start=1):
        identity, status = entry["identity"], entry["status"]
        lines += [f"## {index}. {_md(identity['family'])} · {_md(identity['case_id'])} · "
                  f"{_md(identity['session_minutes'])} min · {_md(identity['turns'])} turns", "",
                  f"- status: **{_md(status.get('state'))}** {_md(', '.join(status.get('codes') or []))}",
                  f"- trace verified: {entry['integrity']['verified']} · replay: "
                  f"{'exact' if entry['replay']['reproduces'] else 'NOT REPRODUCED'}"
                  f"{'' if entry['replay']['replayed'] or entry['replay']['reproduces'] else ' (refused)'}",
                  f"- arrival eligible: {entry['arrival_eligible']} · initial state: "
                  + ", ".join(f"{_md(key)} {_md(value)}" for key, value in entry["initial_state"].items()), "",
                  "### Action timeline", "", "| ordered | effective | action | disposition | note |",
                  "|---|---|---|---|---|"]
        for row in entry["actions"]:
            lines.append(f"| {_md(row.get('order_minute'))} | {_md(row.get('effective_minute'))} | "
                         f"{_md(row.get('kind'))} | {_md(row.get('disposition'))} | {_md(row.get('why'))[:160]} |")
        lines += ["", "### First causal channel, expected and observed", "",
                  "| run | action | expected first | observed first (minute) | then | agrees |", "|---|---|---|---|---|---|"]
        for run, effects in entry["first_effects"].items():
            for effect in effects:
                if effect.get("status") in ("COULD_NOT_BE_COMPUTED",):
                    lines.append(f"| {_md(run)} | — | — | {_md(effect.get('status'))} | — | — |")
                    continue
                then = ", ".join(f"{channel} ({minute})" for channel, minute in effect["downstream"][:8])
                seen = (", ".join(effect["observed_first_channels"]) + f" ({effect['first_minute']})"
                        if effect["first_minute"] is not None else effect["status"])
                agrees = {True: "yes", False: "NO", None: "no expectation declared"}[
                    effect["expected_is_among_the_first"]]
                lines.append(f"| {_md(run)} | {_md(effect['kind'])} @ {_md(effect['order_minute'])} | "
                             f"{_md(effect['expected_first_channel'])} | {_md(seen)} | {_md(then)} | {agrees} |")
        if not any(entry["first_effects"].values()):
            lines.append("| — | no treatment was built in this trace | — | — | — | — |")
        lines += ["", "### Region witnesses", ""]
        if entry["witnesses"]:
            region = entry["region"] or {}
            condition = region.get("conditional_on")
            lines.append(f"{_md(region.get('classification'))}"
                         + (f"; conditional on {_md(condition.get('parameter'))} = {_md(condition.get('value'))}"
                            if condition else f" for {_md(region.get('parameter'))}") + ". None selected.")
            lines += [f"- {_md(w['name'])}: {_md((w['parameter'] or {}).get('declared'))}"
                      f"{' — FAILED, last valid minute ' + _md(w['last_valid_minute']) if w['failed'] else ''}"
                      for w in entry["witnesses"]]
        else:
            lines.append("This family runs no development region.")
        boundary = entry.get("terminal_boundary") or {}
        lines += ["", "### Terminal boundary", "",
                  f"**{_md(boundary.get('state'))}** — {_md(boundary.get('why'))}",
                  f"- legacy engine: terminal {_md((boundary.get('legacy') or {}).get('terminal'))}"
                  f", minute {_md((boundary.get('legacy') or {}).get('minute'))}",
                  f"- common-core run: pulse present {_md((boundary.get('core') or {}).get('pulse_present'))}; "
                  + "; ".join(f"{_md(name)} {_md(value)}" for name, value in
                              ((boundary.get('core') or {}).get('predicates') or {}).items())]
        beside = boundary.get("amendment_2")
        if beside:
            lines += ["", f"Amendment-2 witnesses beside the legacy engine: {_md(beside.get('note'))}", ""] + [
                f"- {_md(name)}: **{_md(row.get('state'))}** (collapse state {_md(row.get('collapse_state_index'))}, observable "
                f"category {_md(row.get('category_index'))}, pulse present {_md(row.get('pulse_present'))})"
                for name, row in (beside.get("witnesses") or {}).items()]
        lines += ["", "### Failures", ""] + ([f"- {_md(f.get('classification'))} at minute {_md(f.get('minute'))}: "
                                             f"{_md(f.get('message'))[:160]}" for f in entry["failures"]] or ["none"])
        lines += ["", "### Unresolved synthetic parameters", ""] + [
            f"- {_md(item)}" for item in entry["unresolved_synthetic_parameters"]]
        lines += ["", "### Questions for faculty", ""] + [
            f"{number}. {_md(item)}" for number, item in enumerate(entry["faculty_questions"], start=1)] + [""]
    return "\n".join(lines) + "\n"


def write_review_package(traces: Sequence, destination: str | Path) -> dict:
    """Write the review package -- ``index.md`` and one report page per trace -- into a directory outside the
    repository. Returns what happened; never raises."""
    try:
        directory = Path(destination)
        if not directory.is_absolute():
            return {"written": False, "why": "the package path must be absolute"}
        resolved = directory.resolve()
        if resolved == store.repository_root() or store.repository_root() in resolved.parents:
            return {"written": False, "why": "a review package is run data and is never written inside the "
                                             "repository"}
        entries, skipped = [], 0
        for trace in traces:
            try:
                entries.append(review_entry(trace))
            except Exception:
                skipped += 1               # one trace that cannot be read does not cost the others their page
        files = []
        for index, entry in enumerate(entries, start=1):
            family = store._safe(entry["identity"]["family"], "trace")
            name = f"trace_{index:02d}_{family}.html"
            _write(directory / name, render_html(entry["view"]))
            files.append(name)
        _write(directory / "index.md", review_markdown(entries))
        return {"written": True, "path": str(directory), "files": ["index.md"] + files, "traces": len(entries),
                "skipped": skipped, "why": ""}
    except Exception as error:
        return {"written": False, "why": f"the package could not be written: {type(error).__name__}"}


def observe(identifier: str, *, environ: Mapping[str, str] | None = None, replay: bool = True) -> dict | None:
    """The view of one stored trace, replayed unless asked not to. None when the store holds no such trace."""
    trace = store.load(identifier, environ=environ)
    if trace is None:
        return None
    return view(trace, replay=store.replay(trace) if replay else None)


def write_report(shown: Mapping, destination: str | Path) -> dict:
    """Write the page where a reader asked, never inside the repository. Returns what happened; never raises."""
    try:
        path = Path(destination)
        if not path.is_absolute():
            return {"written": False, "why": "the report path must be absolute"}
        resolved = path.resolve()
        if resolved == store.repository_root() or store.repository_root() in resolved.parents:
            return {"written": False, "why": "a report is run data and is never written inside the repository"}
        _write(path, render_html(shown))
        return {"written": True, "path": str(path), "why": ""}
    except Exception as error:
        return {"written": False, "why": f"the report could not be written: {type(error).__name__}"}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Faculty and development observer of persisted shadow traces. "
                                                 "Read-only.")
    parser.add_argument("--store", help="the shadow trace store directory (absolute, outside the repository)")
    parser.add_argument("--list", action="store_true", help="list the stored traces; * marks the furthest "
                                                            "record of each attempt")
    parser.add_argument("--heads", action="store_true", help="list only the furthest record of each attempt")
    parser.add_argument("--id", help="the identity of the trace to show")
    parser.add_argument("--out", help="write the report page here (absolute, outside the repository)")
    parser.add_argument("--no-replay", action="store_true", help="do not replay the trace")
    parser.add_argument("--review", help="write a faculty review package of the furthest record of every "
                                         "attempt into this directory (absolute, outside the repository)")
    args = parser.parse_args(argv)
    environ = {store.STORE_FLAG: args.store} if args.store else None
    if not store.configured(environ):
        print(store.refused_root(environ) or store.NOT_CONFIGURED)
        return 2
    if args.review:
        heads = [row for row in store.records(environ=environ)
                 if not row["unreadable"] and row["head"] and row["verified"]]
        traces = [trace for trace in (store.load(row["trace_id"], environ=environ) for row in heads)
                  if trace is not None]
        outcome = write_review_package(traces, args.review)
        print(f'{outcome["path"]} ({outcome["traces"]} traces)' if outcome["written"] else outcome["why"])
        return 0 if outcome["written"] else 2
    if args.list or args.heads or not args.id:
        for row in store.records(environ=environ):
            if row["unreadable"]:
                print(f'{store.UNREADABLE} {row["path"]}')
                continue
            if args.heads and not row["head"]:
                continue
            # a record that does not pass verification is never listed with the state it carries
            state = row["state"] if row["verified"] else f'{store.NOT_VERIFIED} ({row["why"][:60]})'
            print(f'{row["trace_id"]} {"*" if row["head"] else " "} {row["family"]:<10} {row["case_id"]:<14} '
                  f'm{row["session_minutes"]:<4} t{row["turns"]:<3} {state}  {",".join(row["codes"])}')
        return 0
    shown = observe(args.id, environ=environ, replay=not args.no_replay)
    if shown is None:
        print("no stored trace with that identity")
        return 1
    status, replayed = shown["status"], shown["replay"]
    told = ("not asked" if not replayed["asked"] else "nothing to replay" if replayed.get("nothing_to_replay") else
            f'refused ({replayed.get("refused")})' if not replayed["replayed"] else
            "exact" if replayed["reproduces"] else "MISMATCH")
    print(f'{shown["identity"]["family"]} {shown["identity"]["case_id"]}: {status["state"]} '
          f'{",".join(status["codes"])} | trace: {"verified" if shown["integrity"]["verified"] else "NOT VERIFIED"}'
          f' | replay: {told}')
    if args.out:
        outcome = write_report(shown, args.out)
        print(outcome["path"] if outcome["written"] else outcome["why"])
        return 0 if outcome["written"] else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
