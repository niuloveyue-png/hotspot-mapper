import time
from datetime import datetime
from typing import List, Dict
from pytrends.request import TrendReq

def fetch_google_trends(regions: List[str], kw_seed: List[str], top_n: int) -> List[Dict]:
    pytrends = TrendReq(hl="en-US", tz=360)  # US English, UTC-6 offset for example
    results = []
    for region in regions:
        try:
            pytrends.build_payload(kw_seed, timeframe="now 1-d", geo=region)
            trending = pytrends.related_queries()
            if not trending:
                continue
            for kw in kw_seed:
                rq = trending.get(kw, {})
                for seg in ("top", "rising"):
                    df = rq.get(seg)
                    if df is None:
                        continue
                    for _, row in df.head(top_n).iterrows():
                        phrase = str(row.get("query", "")).strip()
                        value = int(row.get("value", 0)) if not (row.get("value") != row.get("value")) else 0
                        if phrase:
                            results.append({
                                "source": "google_trends",
                                "region": region,
                                "title": phrase,
                                "url": f"https://trends.google.com/trends/explore?geo={region}&q={phrase}",
                                "score_raw": value,
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                "meta": {"segment": seg, "seed_kw": kw}
                            })
            time.sleep(1)
        except Exception as e:
            results.append({
                "source": "google_trends",
                "region": region,
                "title": f"[error] {e}",
                "url": "",
                "score_raw": 0,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "meta": {"segment": "error"}
            })
    return results
