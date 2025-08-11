import subprocess, json, shlex
from datetime import datetime, timedelta, timezone
from typing import List, Dict

def _run(cmd: str) -> str:
    p = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip())
    return p.stdout

def fetch_twitter(kw_any: List[str], lookback_hours: int, max_results: int, top_n: int) -> List[Dict]:
    # Build query: (kw1 OR kw2 ...) lang:en -lang:zh -filter:replies
    since = (datetime.now(timezone.utc) - timedelta(hours=lookback_hours)).strftime("%Y-%m-%d")
    ors = " OR ".join([shlex.quote(k) for k in kw_any])
    query = f"({ors}) lang:en -lang:zh since:{since}"
    cmd = f"snscrape --jsonl --max-results {max_results} twitter-search {shlex.quote(query)}"
    try:
        out = _run(cmd)
    except Exception as e:
        return [{
            "source": "twitter",
            "title": f"[error] {e}",
            "url": "",
            "score_raw": 0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "meta": {}
        }]
    results = []
    for line in out.splitlines():
        try:
            obj = json.loads(line)
            results.append({
                "source": "twitter",
                "title": obj.get("content","")[:200],
                "url": obj.get("url",""),
                "score_raw": (obj.get("likeCount",0) or 0) + 2*(obj.get("retweetCount",0) or 0),
                "timestamp": obj.get("date",""),
                "meta": {"likes": obj.get("likeCount",0), "retweets": obj.get("retweetCount",0)}
            })
        except Exception:
            continue
    # Keep top_n by score_raw
    results.sort(key=lambda x: x.get("score_raw",0), reverse=True)
    return results[:top_n]
