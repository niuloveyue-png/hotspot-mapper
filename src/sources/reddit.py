import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict
import praw

def fetch_reddit(subreddits: List[str], min_upvotes: int, lookback_hours: int, top_n: int) -> List[Dict]:
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "hotspot-mapper/0.1")
    results = []
    if not (client_id and client_secret):
        return results  # silently skip if not configured

    reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
    since = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)

    for sub in subreddits:
        try:
            subreddit = reddit.subreddit(sub)
            for post in subreddit.hot(limit=top_n*5):
                if post.created_utc and datetime.fromtimestamp(post.created_utc, tz=timezone.utc) < since:
                    continue
                if post.score < min_upvotes:
                    continue
                results.append({
                    "source": "reddit",
                    "subreddit": sub,
                    "title": post.title,
                    "url": f"https://www.reddit.com{post.permalink}",
                    "score_raw": post.score,
                    "timestamp": datetime.utcfromtimestamp(post.created_utc).isoformat() + "Z",
                    "meta": {"num_comments": post.num_comments}
                })
        except Exception as e:
            results.append({
                "source": "reddit",
                "subreddit": sub,
                "title": f"[error] {e}",
                "url": "",
                "score_raw": 0,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "meta": {}
            })
    return results
