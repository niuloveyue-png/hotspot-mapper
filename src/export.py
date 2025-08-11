import os, csv
from typing import List, Dict

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def export_csv(path: str, rows: List[Dict], fieldnames: List[str]):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k,"") for k in fieldnames})

def export_report_md(path: str, hotspots: List[Dict], mappings: List[Dict]):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Daily Hotspot → Crypto Mapping Report\n\n")
        f.write("## Hotspots (Aggregated)\n\n")
        for h in hotspots[:50]:
            f.write(f"- **{h['keyword']}** — score={h['score_sum']:.3f}, hits={h['hits']}, sources={h['sources']}\n")
        f.write("\n## DexScreener Matches\n\n")
        for m in mappings[:100]:
            f.write(f"- `{m.get('keyword')}` → {m.get('base_token')} ({m.get('chain')}) — liq=${m.get('liquidity_usd')} — {m.get('url')}\n")
