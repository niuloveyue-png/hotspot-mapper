import time, base64, hmac, hashlib, json, requests
from typing import List, Dict, Optional

def _sign(secret: str, timestamp: str) -> str:
    string_to_sign = f"{timestamp}\n{secret}"
    h = hmac.new(secret.encode("utf-8"), string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
    return base64.b64encode(h).decode("utf-8")

def send_text(webhook: str, text: str, secret: Optional[str] = None) -> Dict:
    timestamp = str(int(time.time()))
    payload = {"msg_type": "text", "content": {"text": text}}
    headers = {"Content-Type": "application/json"}
    if secret:
        payload["timestamp"] = timestamp
        payload["sign"] = _sign(secret, timestamp)
    r = requests.post(webhook, headers=headers, data=json.dumps(payload), timeout=15)
    return {"status_code": r.status_code, "body": r.text}

def send_post(webhook: str, title: str, lines: List[str], secret: Optional[str] = None) -> Dict:
    """Rich text 'post' message (Markdown-like)"""
    timestamp = str(int(time.time()))
    content_lines = [[{"tag": "text", "text": line + "\n"}] for line in lines]
    payload = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": title,
                    "content": content_lines
                }
            }
        }
    }
    headers = {"Content-Type": "application/json"}
    if secret:
        payload["timestamp"] = timestamp
        payload["sign"] = _sign(secret, timestamp)
    r = requests.post(webhook, headers=headers, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), timeout=15)
    return {"status_code": r.status_code, "body": r.text}

def send_card(webhook: str, title: str, sections: List[Dict], secret: Optional[str] = None) -> Dict:
    """Interactive card with sections: each section is {'header': str, 'items': [str, str, ...]}"""
    timestamp = str(int(time.time()))
    elements = []
    for sec in sections:
        elements.append({"tag": "hr"})
        elements.append({"tag": "markdown", "content": f"**{sec.get('header','')}**"})
        for item in sec.get("items", []):
            elements.append({"tag": "markdown", "content": f"- {item}"})
    card = {
        "config": {"wide_screen_mode": True},
        "header": {"template": "blue", "title": {"content": title, "tag": "plain_text"}},
        "elements": elements[1:] if elements and elements[0].get("tag") == "hr" else elements
    }
    payload = {"msg_type": "interactive", "card": card}
    if secret:
        payload["timestamp"] = timestamp
        payload["sign"] = _sign(secret, timestamp)
    headers = {"Content-Type": "application/json"}
    r = requests.post(webhook, headers=headers, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), timeout=15)
    return {"status_code": r.status_code, "body": r.text}
