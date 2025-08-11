import requests
from typing import List, Dict

SEARCH_URL = "https://api.dexscreener.com/latest/dex/search"

def query_pairs(keyword: str) -> List[Dict]:
    try:
        r = requests.get(SEARCH_URL, params={"q": keyword}, timeout=15)
        r.raise_for_status()
        data = r.json() or {}
        return data.get("pairs", []) or []
    except Exception:
        return []

def map_keywords_to_pairs(keywords: List[str], min_liquidity_usd: int, chains: List[str]) -> List[Dict]:
    out = []
    for kw in keywords:
        pairs = query_pairs(kw) or []
        for p in pairs:
            chain = p.get("chainId") or p.get("chain")
            if chains and (chain not in chains):
                continue
            liq = p.get("liquidity",{}).get("usd",0) or 0
            if liq < min_liquidity_usd:
                continue
            out.append({
                "keyword": kw,
                "chain": chain,
                "dex_id": p.get("dexId"),
                "pair_address": p.get("pairAddress"),
                "base_token": p.get("baseToken",{}).get("symbol"),
                "base_name": p.get("baseToken",{}).get("name"),
                "fdv": p.get("fdv"),
                "liquidity_usd": liq,
                "price_usd": p.get("priceUsd"),
                "url": p.get("url"),
                "created_at": p.get("pairCreatedAt")
            })
    return out
