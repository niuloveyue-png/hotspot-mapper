import os, requests, math
from typing import List, Dict, Optional

API_BASE = "https://api.telegram.org"

def _post(token: str, method: str, data: dict) -> Dict:
    url = f"{API_BASE}/bot{token}/{method}"
    r = requests.post(url, json=data, timeout=15)
    try:
        return r.json()
    except Exception:
        return {"status_code": r.status_code, "text": r.text}

def _chunk(text: str, n: int = 3800) -> List[str]:
    # Telegram hard limit ~4096 chars; keep a safety margin
    return [text[i:i+n] for i in range(0, len(text), n)]

def send_markdown(token: str, chat_id: str, text: str, disable_preview: bool = True) -> List[Dict]:
    results = []
    for chunk in _chunk(text):
        data = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "MarkdownV2",
            "disable_web_page_preview": disable_preview
        }
        # escape minimal set for MarkdownV2
        safe = (chunk
                .replace("_","\\_")
                .replace("*","\\*")
                .replace("[","\\[")
                .replace("]","\\]")
                .replace("(","\\(")
                .replace(")","\\)")
                .replace("~","\\~")
                .replace("`","\\`")
                .replace(">","\\>")
                .replace("#","\\#")
                .replace("+","\\+")
                .replace("-","\\-")
                .replace("=","\\=")
                .replace("|","\\|")
                .replace("{","\\{")
                .replace("}","\\}")
                .replace(".","\\.")
                .replace("!","\\!"))
        data["text"] = safe
        results.append(_post(token, "sendMessage", data))
    return results

def send_simple_card(token: str, chat_id: str, title: str, sections: List[Dict]) -> List[Dict]:
    """
    sections: [{header: str, items: [str, ...]}, ...]
    Renders a Markdown-style message.
    """
    lines = [f"*{title}*"]
    for sec in sections:
        lines.append(f"\n*{sec.get('header','')}*")
        for it in sec.get("items", []):
            lines.append(f"- {it}")
    text = "\n".join(lines)
    return send_markdown(token, chat_id, text, disable_preview=False)
