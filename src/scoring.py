from datetime import datetime, timezone
from typing import List, Dict
import math

def score_items(items: List[Dict], weights: Dict) -> List[Dict]:
    # Normalize by source
    # twitter: likes/retweets; reddit: upvotes; google_trends: value
    half_life = weights.get("recency_hours_half_life", 24)
    def recency_boost(ts: str) -> float:
        try:
            dt = datetime.fromisoformat(ts.replace("Z","+00:00"))
        except Exception:
            return 1.0
        hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0
        return 2 ** (-hours / half_life)  # newer → closer to 1, older → decay

    enriched = []
    for it in items:
        src = it.get("source")
        base = 0.0
        if src == "twitter":
            m = it.get("meta",{})
            base = m.get("likes",0)*weights.get("twitter_like_scale",0.001) + m.get("retweets",0)*weights.get("twitter_retweet_scale",0.002)
        elif src == "reddit":
            base = it.get("score_raw",0)*weights.get("reddit_upvote_scale",0.002)
        elif src == "google_trends":
            base = (it.get("score_raw",0) or 0)/100.0
        else:
            base = it.get("score_raw",0)/100.0
        s = base * recency_boost(it.get("timestamp",""))
        it2 = dict(it)
        it2["score"] = s
        enriched.append(it2)
    return enriched

def aggregate_by_keyword(items: List[Dict], whitelist: List[str]):
    # very naive keyword picking: keep phrases with any whitelist token
    buckets = {}
    for it in items:
        title = (it.get("title") or "").lower()
        matched = [w for w in whitelist if w in title]
        if not matched:
            continue
        key = title
        buckets.setdefault(key, []).append(it)
    agg = []
    for key, arr in buckets.items():
        score_sum = sum(x.get("score",0) for x in arr)
        sources = sorted({x.get("source") for x in arr})
        agg.append({
            "keyword": key,
            "hits": len(arr),
            "sources": ",".join(sources),
            "score_sum": score_sum
        })
    agg.sort(key=lambda x: (x["score_sum"], x["hits"]), reverse=True)
    return agg
