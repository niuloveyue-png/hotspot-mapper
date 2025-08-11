import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional

API = "https://frontend-api.pump.fun/projects"

def _get(url: str, params: dict) -> Optional[dict]:
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def fetch_pumpfun_recent(limit: int = 100, kw_any: Optional[List[str]] = None) -> List[Dict]:
    """
    Fetch recent Pump.fun projects (unofficial endpoint). We query several sorts to improve coverage.
    """
    results = []
    for sort in ("createdAt", "marketCap", "holders"):
        data = _get(API, {"offset": 0, "limit": limit, "sort": sort})
        if not data or not isinstance(data, dict):
            continue
        projects = data.get("projects") or data.get("data") or data
        if not isinstance(projects, list):
            continue
        for p in projects:
            name = str(p.get("name") or "").strip()
            symbol = str(p.get("symbol") or "").strip()
            title = f"{name} ({symbol})".strip() or symbol or name
            title_l = title.lower()
            if kw_any:
                if not any(k.lower() in title_l for k in kw_any):
                    # also try in description if present
                    desc = (p.get("description") or "").lower()
                    if not any(k.lower() in desc for k in kw_any):
                        continue
            ts = p.get("createdAt") or p.get("created_at")
            # normalize timestamp
            if isinstance(ts, (int, float)):
                created = datetime.fromtimestamp(ts/1000 if ts>1e12 else ts, tz=timezone.utc).isoformat()
            elif isinstance(ts, str):
                created = ts
            else:
                created = datetime.now(timezone.utc).isoformat()
            results.append({
                "source": "pumpfun",
                "title": title,
                "url": f"https://pump.fun/coin/{p.get('mint')}" if p.get("mint") else "https://pump.fun",
                "score_raw": int(p.get("marketCapUsd") or p.get("marketCap") or 0),
                "timestamp": created,
                "meta": {
                    "mint": p.get("mint"),
                    "marketcap_usd": p.get("marketCapUsd") or p.get("marketCap"),
                    "holders": p.get("holders"),
                    "raydium_pool": p.get("raydiumPool"),
                }
            })
    # de-dup by mint
    seen = set()
    uniq = []
    for x in results:
        m = x["meta"].get("mint")
        if not m or m in seen:
            continue
        seen.add(m)
        uniq.append(x)
    # sort by marketcap (desc)
    uniq.sort(key=lambda x: x.get("score_raw", 0) or 0, reverse=True)
    return uniq
