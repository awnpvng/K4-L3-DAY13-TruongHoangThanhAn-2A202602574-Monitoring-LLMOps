"""Render a static HTML dashboard from data/logs.jsonl following config/dashboard.yaml.

Usage:
    python scripts/render_dashboard.py
    # then open data/dashboard.html in a browser and screenshot it
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

LOG_PATH = Path("data/logs.jsonl")
CONFIG_PATH = Path("config/dashboard.yaml")
OUTPUT_PATH = Path("data/dashboard.html")


def percentile(values: list[float], pct: int) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    k = (len(values) - 1) * (pct / 100)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return values[int(k)]
    return values[f] + (values[c] - values[f]) * (k - f)


def load_records(window_minutes: int) -> list[dict]:
    records = []
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        try:
            ts = datetime.fromisoformat(rec.get("ts", "").replace("Z", "+00:00"))
        except ValueError:
            continue
        if ts >= cutoff:
            records.append(rec)
    return records


def build_latency_panel(records: list[dict]) -> dict:
    sent = [r for r in records if r.get("event") == "response_sent"]
    latencies = [r["latency_ms"] for r in sent if r.get("latency_ms") is not None]
    ttfts = [r["ttft_ms"] for r in sent if r.get("ttft_ms") is not None]
    return {
        "p50": round(percentile(latencies, 50), 1),
        "p95": round(percentile(latencies, 95), 1),
        "p99": round(percentile(latencies, 99), 1),
        "ttft_p95": round(percentile(ttfts, 95), 1),
        "sample": len(sent),
    }


def build_traffic_panel(records: list[dict], window_minutes: int) -> dict:
    received = [r for r in records if r.get("event") == "request_received"]
    rate = round(len(received) / window_minutes, 2) if window_minutes else 0.0
    return {"count": len(received), "rate_per_minute": rate}


def build_errors_panel(records: list[dict]) -> dict:
    received = [r for r in records if r.get("event") == "request_received"]
    failed = [r for r in records if r.get("event") == "request_failed"]
    error_rate = round(len(failed) / len(received) * 100, 2) if received else 0.0
    by_type: dict[str, int] = {}
    for r in failed:
        et = r.get("error_type", "unknown")
        by_type[et] = by_type.get(et, 0) + 1
    tool_calls = [r for r in records if r.get("tool_success") is not None]
    tool_ok = [r for r in tool_calls if r.get("tool_success") is True]
    tool_success_rate = round(len(tool_ok) / len(tool_calls) * 100, 2) if tool_calls else 100.0
    return {
        "error_rate_pct": error_rate,
        "by_type": by_type,
        "tool_success_rate_pct": tool_success_rate,
    }


def build_cost_panel(records: list[dict]) -> dict:
    sent = [r for r in records if r.get("event") == "response_sent"]
    total = round(sum(r.get("cost_usd", 0.0) for r in sent), 6)
    return {"total_usd": total, "sample": len(sent)}


def build_tokens_panel(records: list[dict]) -> dict:
    sent = [r for r in records if r.get("event") == "response_sent"]
    tokens_in = sum(r.get("tokens_in", 0) for r in sent)
    tokens_out = sum(r.get("tokens_out", 0) for r in sent)
    return {"tokens_in": tokens_in, "tokens_out": tokens_out}


def build_quality_panel(records: list[dict]) -> dict:
    sent = [r for r in records if r.get("event") == "response_sent"]
    scores = [r["quality_score"] for r in sent if r.get("quality_score") is not None]
    mean = round(sum(scores) / len(scores), 3) if scores else 0.0
    return {"mean": mean, "sample": len(scores)}


def render_html(cfg: dict, window_minutes: int, panels: dict) -> str:
    dash = cfg["dashboard"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    def threshold_status(value: float, threshold: dict) -> str:
        op = threshold["operator"]
        limit = threshold["value"]
        ok = (value <= limit) if op == "lte" else (value >= limit)
        return "OK" if ok else "BREACH"

    latency = panels["latency"]
    traffic = panels["traffic"]
    errors = panels["errors"]
    cost = panels["cost"]
    tokens = panels["tokens"]
    quality = panels["quality"]

    latency_th = next(p for p in dash["panels"] if p["id"] == "latency")["threshold"]
    traffic_th = next(p for p in dash["panels"] if p["id"] == "traffic")["threshold"]
    errors_th = next(p for p in dash["panels"] if p["id"] == "errors")["threshold"]
    cost_th = next(p for p in dash["panels"] if p["id"] == "cost")["threshold"]
    tokens_th = next(p for p in dash["panels"] if p["id"] == "tokens")["threshold"]
    quality_th = next(p for p in dash["panels"] if p["id"] == "quality")["threshold"]

    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<title>{dash['title']}</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #0b0f14; color: #e6edf3; margin: 0; padding: 24px; }}
  h1 {{ font-size: 20px; margin-bottom: 4px; }}
  .meta {{ color: #9aa7b2; margin-bottom: 20px; font-size: 13px; }}
  .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
  .panel {{ background: #141a21; border: 1px solid #2a333d; border-radius: 8px; padding: 16px; }}
  .panel h2 {{ margin: 0 0 12px; font-size: 15px; color: #cbd5e1; }}
  .metric {{ font-size: 26px; font-weight: 700; }}
  .unit {{ font-size: 13px; color: #9aa7b2; margin-left: 6px; }}
  .row {{ display: flex; justify-content: space-between; margin-top: 8px; font-size: 13px; color: #b7c2cc; }}
  .status-OK {{ color: #4ade80; font-weight: 600; }}
  .status-BREACH {{ color: #f87171; font-weight: 600; }}
  .threshold {{ margin-top: 10px; font-size: 12px; color: #8a97a3; }}
</style>
</head>
<body>
  <h1>{dash['title']}</h1>
  <div class="meta">
    Time range: last {window_minutes} minutes &middot; Refresh: {dash['refresh_seconds']}s &middot; Generated: {now} &middot; Source: data/logs.jsonl
  </div>
  <div class="grid">
    <div class="panel">
      <h2>Latency percentiles and TTFT</h2>
      <div class="metric">{latency['p95']}<span class="unit">ms (P95)</span></div>
      <div class="row"><span>P50</span><span>{latency['p50']} ms</span></div>
      <div class="row"><span>P99</span><span>{latency['p99']} ms</span></div>
      <div class="row"><span>TTFT P95</span><span>{latency['ttft_p95']} ms</span></div>
      <div class="threshold">Threshold: P95 &le; {latency_th['value']} ms &mdash;
        <span class="status-{threshold_status(latency['p95'], latency_th)}">{threshold_status(latency['p95'], latency_th)}</span>
      </div>
    </div>
    <div class="panel">
      <h2>Request traffic</h2>
      <div class="metric">{traffic['count']}<span class="unit">requests</span></div>
      <div class="row"><span>Rate</span><span>{traffic['rate_per_minute']} req/min</span></div>
      <div class="threshold">Threshold: rate &ge; {traffic_th['value']} req/min &mdash;
        <span class="status-{threshold_status(traffic['rate_per_minute'], traffic_th)}">{threshold_status(traffic['rate_per_minute'], traffic_th)}</span>
      </div>
    </div>
    <div class="panel">
      <h2>Error rate and retrieval success</h2>
      <div class="metric">{errors['error_rate_pct']}<span class="unit">% error rate</span></div>
      <div class="row"><span>Retrieval success</span><span>{errors['tool_success_rate_pct']}%</span></div>
      <div class="row"><span>By type</span><span>{errors['by_type'] or '-'}</span></div>
      <div class="threshold">Threshold: error rate &le; {errors_th['value']}% &mdash;
        <span class="status-{threshold_status(errors['error_rate_pct'], errors_th)}">{threshold_status(errors['error_rate_pct'], errors_th)}</span>
      </div>
    </div>
    <div class="panel">
      <h2>Cost over time</h2>
      <div class="metric">${cost['total_usd']}<span class="unit">total</span></div>
      <div class="row"><span>Sample</span><span>{cost['sample']} responses</span></div>
      <div class="threshold">Threshold: total &le; ${cost_th['value']} &mdash;
        <span class="status-{threshold_status(cost['total_usd'], cost_th)}">{threshold_status(cost['total_usd'], cost_th)}</span>
      </div>
    </div>
    <div class="panel">
      <h2>Input and output tokens</h2>
      <div class="metric">{tokens['tokens_in'] + tokens['tokens_out']}<span class="unit">tokens</span></div>
      <div class="row"><span>Input</span><span>{tokens['tokens_in']}</span></div>
      <div class="row"><span>Output</span><span>{tokens['tokens_out']}</span></div>
      <div class="threshold">Threshold: sum &le; {tokens_th['value']} tokens &mdash;
        <span class="status-{threshold_status(tokens['tokens_in'] + tokens['tokens_out'], tokens_th)}">{threshold_status(tokens['tokens_in'] + tokens['tokens_out'], tokens_th)}</span>
      </div>
    </div>
    <div class="panel">
      <h2>Quality proxy</h2>
      <div class="metric">{quality['mean']}<span class="unit">/ 1.0</span></div>
      <div class="row"><span>Sample</span><span>{quality['sample']} responses</span></div>
      <div class="threshold">Threshold: mean &ge; {quality_th['value']} &mdash;
        <span class="status-{threshold_status(quality['mean'], quality_th)}">{threshold_status(quality['mean'], quality_th)}</span>
      </div>
    </div>
  </div>
</body>
</html>
"""


def main() -> None:
    if not LOG_PATH.exists():
        print(f"Error: {LOG_PATH} not found. Run the app and send some requests first.")
        return
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    window_minutes = cfg["dashboard"]["time_range_minutes"]
    records = load_records(window_minutes)

    panels = {
        "latency": build_latency_panel(records),
        "traffic": build_traffic_panel(records, window_minutes),
        "errors": build_errors_panel(records),
        "cost": build_cost_panel(records),
        "tokens": build_tokens_panel(records),
        "quality": build_quality_panel(records),
    }

    html = render_html(cfg, window_minutes, panels)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"Dashboard written to {OUTPUT_PATH.resolve()}")
    print(f"Records in window ({window_minutes} min): {len(records)}")


if __name__ == "__main__":
    main()
