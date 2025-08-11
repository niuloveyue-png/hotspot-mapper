import os, yaml, pandas as pd
from dotenv import load_dotenv

from .sources.google_trends import fetch_google_trends
from .sources.reddit import fetch_reddit
from .sources.twitter import fetch_twitter
from .sources.pumpfun import fetch_pumpfun_recent
from .mapping.dexscreener import map_keywords_to_pairs
from .scoring import score_items, aggregate_by_keyword
from .export import export_csv, export_report_md
from .notifiers.feishu import send_card
from .notifiers.telegram import send_simple_card

def main():
    load_dotenv()
    with open("config.yaml","r",encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    out_dir = cfg["run"]["out_dir"]
    top_n = cfg["run"]["top_n"]
    lookback = cfg["run"]["lookback_hours"]

    all_items = []

    # Google Trends
    if cfg["sources"]["google_trends"]["enabled"]:
        gt = fetch_google_trends(cfg["sources"]["google_trends"]["regions"],
                                 cfg["sources"]["google_trends"]["kw_seed"],
                                 top_n=top_n)
        all_items.extend(gt)

    # Reddit
    if cfg["sources"]["reddit"]["enabled"]:
        rd = fetch_reddit(cfg["sources"]["reddit"]["subreddits"],
                          cfg["sources"]["reddit"]["min_upvotes"],
                          lookback_hours=lookback,
                          top_n=top_n)
        all_items.extend(rd)

    # Twitter
    if cfg["sources"]["twitter"]["enabled"]:
        tw = fetch_twitter(cfg["sources"]["twitter"]["kw_any"],
                           lookback_hours=lookback,
                           max_results=cfg["sources"]["twitter"]["max_results"],
                           top_n=top_n)
        all_items.extend(tw)

    # Pump.fun recent
    if cfg["sources"].get("pumpfun", {}).get("enabled"):
        pf = fetch_pumpfun_recent(limit=cfg["sources"]["pumpfun"].get("limit", 120),
                                  kw_any=cfg["sources"]["pumpfun"].get("kw_any"))
        all_items.extend(pf)

    # Scoring
    items_scored = score_items(all_items, cfg["scoring"]["weights"])

    # Aggregate
    agg = aggregate_by_keyword(items_scored, cfg["filters"]["whitelist_any"])

    # Mapping on dexscreener
    mappings = []
    if cfg["mapping"]["dexscreener"]["enabled"]:
        keywords = [a["keyword"] for a in agg[:50]]
        mappings = map_keywords_to_pairs(
            keywords=keywords,
            min_liquidity_usd=cfg["mapping"]["dexscreener"]["min_liquidity_usd"],
            chains=cfg["mapping"]["dexscreener"]["chains"]
        )

    # Export
    os.makedirs(out_dir, exist_ok=True)
    # Raw items
    df_items = pd.DataFrame(items_scored)
    df_items.to_csv(f"{out_dir}/items_scored.csv", index=False)

    # Aggregated hotspots
    df_agg = pd.DataFrame(agg)
    df_agg.to_csv(f"{out_dir}/hotspots.csv", index=False)

    # Dex mappings
    df_map = pd.DataFrame(mappings)
    df_map.to_csv(f"{out_dir}/dex_mappings.csv", index=False)

    # Markdown report
    export_report_md(f"{out_dir}/report.md", agg, mappings)

    print(f"Done. Wrote to {out_dir}/")

    # Feishu push (optional)
    notify_cfg = cfg.get("notify", {}).get("feishu", {})
    if notify_cfg.get("enabled") and notify_cfg.get("webhook", "").startswith("http"):
        webhook = notify_cfg["webhook"]
        import os
        secret = os.getenv("FEISHU_BOT_SECRET") or None

        # prepare sections
        hs_items = []
        for h in agg[: notify_cfg.get("max_hotspots", 10)]:
            hs_items.append(f"**{h['keyword']}** | score={h['score_sum']:.2f} | hits={h['hits']} | {h['sources']}")

        map_items = []
        for m in mappings[: notify_cfg.get("max_mappings", 10)]:
            tok = m.get("base_token") or m.get("base_name") or "N/A"
            liq = m.get("liquidity_usd")
            chain = m.get("chain")
            url = m.get("url","")
            map_items.append(f"`{m.get('keyword')}` → {tok} ({chain}) | liq=${liq} | {url}")

        # pump.fun new coins (top by marketcap)
        pf_items = []
        try:
            import pandas as _pd
            df_pf = _pd.read_csv(f"{out_dir}/items_scored.csv")
            df_pf = df_pf[df_pf["source"]=="pumpfun"].copy()
            df_pf.sort_values("score_raw", ascending=False, inplace=True)
            for _, r in df_pf.head(notify_cfg.get("max_mappings", 10)).iterrows():
                title = str(r.get("title",""))
                url = str(r.get("url",""))
                mc = int(r.get("score_raw") or 0)
                pf_items.append(f"{title} | MC=${mc} | {url}")
        except Exception:
            pass

        sections = [
            {"header": "Hotspots（聚合Top）", "items": hs_items or ["暂无"]},
            {"header": "DexScreener 映射", "items": map_items or ["暂无"]},
            {"header": "Pump.fun 新发币", "items": pf_items or ["暂无"]},
        ]
        try:
            resp = send_card(webhook, "Daily Overseas Hotspot → Crypto Mapping", sections, secret=secret)
            print("Feishu push:", resp)
        except Exception as e:
            print("Feishu push error:", e)

    # Telegram push (optional)
    tg_cfg = cfg.get("notify", {}).get("telegram", {})
    if tg_cfg.get("enabled"):
        import os
        token = os.getenv(tg_cfg.get("token_env", "TELEGRAM_BOT_TOKEN"))
        chat_id = tg_cfg.get("chat_id")
        if token and chat_id:
            # reuse sections built above if exist, else rebuild minimal
            try:
                if 'sections' not in locals():
                    hs_items = [f"{h['keyword']} | score={h['score_sum']:.2f} | hits={h['hits']} | {h['sources']}" for h in agg[: tg_cfg.get("max_hotspots", 10)]]
                    map_items = []
                    for m in mappings[: tg_cfg.get("max_mappings", 10)]:
                        tok = m.get("base_token") or m.get("base_name") or "N/A"
                        liq = m.get("liquidity_usd")
                        chain = m.get("chain")
                        url = m.get("url", "")
                        map_items.append(f"{m.get('keyword')} → {tok} ({chain}) | liq=${liq} | {url}")
                    # pump.fun
                    pf_items = []
                    try:
                        import pandas as _pd
                        df_pf = _pd.read_csv(f"{out_dir}/items_scored.csv")
                        df_pf = df_pf[df_pf["source"]=="pumpfun"].copy()
                        df_pf.sort_values("score_raw", ascending=False, inplace=True)
                        for _, r in df_pf.head(tg_cfg.get("max_mappings", 10)).iterrows():
                            title = str(r.get("title",""))
                            url = str(r.get("url",""))
                            mc = int(r.get("score_raw") or 0)
                            pf_items.append(f"{title} | MC=${mc} | {url}")
                    except Exception:
                        pass
                    sections = [
                        {"header": "Hotspots（聚合Top）", "items": hs_items or ["暂无"]},
                        {"header": "DexScreener 映射", "items": map_items or ["暂无"]},
                        {"header": "Pump.fun 新发币", "items": pf_items or ["暂无"]},
                    ]
                resp2 = send_simple_card(token, chat_id, "Daily Overseas Hotspot → Crypto Mapping", sections)
                print("Telegram push:", resp2)
            except Exception as e:
                print("Telegram push error:", e)
        else:
            print("Telegram config missing token or chat_id; skip push")


if __name__ == "__main__":
    main()
