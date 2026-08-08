#!/usr/bin/env python3
"""
🚀 CloneIA - Telegram Channel Cloner (Backend Engine)
"""
import asyncio
import os
import sys
import time
import json
import re
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')

if not API_ID or not API_HASH:
    print("❌ ERRO: Configure o TELEGRAM_API_ID e TELEGRAM_API_HASH no arquivo .env")
    sys.exit(1)

SESSION = 'cloneia_session'
CACHE_DIR = Path('clone_cache')
TEMP_DIR = Path('temp_clone')
PROGRESS_FILE = Path('progress.json')
CONFIG_FILE = Path('config.json')

last_print_time = 0
current_status = {
    "status": "idle",
    "message": "Aguardando...",
    "action": "",
    "current_mb": 0,
    "total_mb": 0,
    "percent": 0,
    "msg_current": 0,
    "msg_total": 0
}

def load_filters():
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text())
    except:
        pass
    return {}

def update_status(**kwargs):
    current_status.update(kwargs)
    try:
        PROGRESS_FILE.write_text(json.dumps(current_status))
    except:
        pass

def progress_callback(current, total, action_name):
    global last_print_time
    now = time.time()
    if now - last_print_time > 1:
        percent = (current / total) * 100 if total > 0 else 0
        current_mb = current / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        
        print(f"   ⏳ {action_name}: {current_mb:.1f} MB / {total_mb:.1f} MB ({percent:.1f}%)", flush=True)
        
        update_status(
            status="running",
            action=action_name,
            current_mb=round(current_mb, 1),
            total_mb=round(total_mb, 1),
            percent=round(percent, 1)
        )
        last_print_time = now

def load_posted(origin_id, dest_id):
    cache_file = CACHE_DIR / f'posted_{origin_id}_{dest_id}.json'
    if cache_file.exists():
        return set(json.loads(cache_file.read_text()))
    return set()

def save_posted(origin_id, dest_id, posted):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f'posted_{origin_id}_{dest_id}.json'
    cache_file.write_text(json.dumps(list(posted)))

def process_text(text, filters):
    if not text:
        return text

    if filters.get('remove_links'):
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    if filters.get('remove_mentions'):
        text = re.sub(r'@[a-zA-Z0-9_]+', '', text)
        
    replace_from = filters.get('replace_from', '')
    replace_to = filters.get('replace_to', '')
    if replace_from:
        text = text.replace(replace_from, replace_to)
        
    signature = filters.get('signature', '')
    if signature:
        text = f"{text}\n\n{signature}"
        
    return text.strip()

def check_blacklist(text, filters):
    blacklist = filters.get('blacklist', '')
    if not blacklist or not text:
        return False
        
    words = [w.strip().lower() for w in blacklist.split(',') if w.strip()]
    text_lower = text.lower()
    for word in words:
        if word in text_lower:
            return True
    return False

def is_media_allowed(msg, filters):
    if msg.photo:
        return filters.get('f_photo', True)
    if msg.video or getattr(msg, 'video_note', None):
        return filters.get('f_video', True)
    if msg.audio or msg.voice:
        return filters.get('f_audio', True)
    if msg.document: # Outros documentos
        return filters.get('f_document', True)
    if not msg.media:
        return filters.get('f_text', True)
    return True

async def clone_message(client, msg, dest_entity, posted, origin_id, dest_id, total_msgs, current_idx, filters):
    update_status(msg_current=current_idx, msg_total=total_msgs, percent=0, action="", current_mb=0, total_mb=0)
    try:
        raw_text = msg.text or ''
        
        # 1. Checar Blacklist
        if check_blacklist(raw_text, filters):
            msg_txt = f"[{current_idx}/{total_msgs}] Ignorado (Blacklist)"
            print(f"🚫 {msg_txt}", flush=True)
            update_status(status="running", message=msg_txt)
            posted.add(msg.id)
            save_posted(origin_id, dest_id, posted)
            return

        # 2. Checar Filtro de Mídia
        if not is_media_allowed(msg, filters):
            msg_txt = f"[{current_idx}/{total_msgs}] Ignorado (Filtro de Mídia)"
            print(f"⏭️ {msg_txt}", flush=True)
            update_status(status="running", message=msg_txt)
            posted.add(msg.id)
            save_posted(origin_id, dest_id, posted)
            return

        # 3. Tratar Texto
        caption = process_text(raw_text, filters)
        
        if msg.media:
            msg_txt = f"[{current_idx}/{total_msgs}] Iniciando DOWNLOAD da mídia..."
            print(f"\n📥 {msg_txt}", flush=True)
            update_status(status="running", message=msg_txt)
            
            temp_path = await client.download_media(
                msg, 
                file=str(TEMP_DIR) + '/',
                progress_callback=lambda c, t: progress_callback(c, t, "Download")
            )
            if temp_path:
                msg_txt = f"[{current_idx}/{total_msgs}] Download concluído! Iniciando UPLOAD..."
                print(f"📤 {msg_txt}", flush=True)
                update_status(status="running", message=msg_txt, percent=0, current_mb=0, total_mb=0)
                
                await client.send_file(
                    dest_entity,
                    temp_path,
                    caption=caption,
                    force_document=False,
                    progress_callback=lambda c, t: progress_callback(c, t, "Upload")
                )
                try:
                    os.remove(temp_path)
                except:
                    pass
                print(f"✨ [{current_idx}/{total_msgs}] MÍDIA CLONADA COM SUCESSO!", flush=True)
            else:
                print(f"⚠️ [{current_idx}/{total_msgs}] Mídia vazia, pulando...", flush=True)
        elif caption:
            await client.send_message(dest_entity, caption)
            print(f"📝 [{current_idx}/{total_msgs}] Texto clonado!", flush=True)
        
        posted.add(msg.id)
        save_posted(origin_id, dest_id, posted)
        
    except FloodWaitError as e:
        msg_txt = f"FloodWait: aguardando {e.seconds}s..."
        print(f"⏳ {msg_txt}", flush=True)
        update_status(status="waiting", message=msg_txt)
        await asyncio.sleep(e.seconds + 1)
        await clone_message(client, msg, dest_entity, posted, origin_id, dest_id, total_msgs, current_idx, filters)
    except Exception as e:
        print(f"❌ [{current_idx}/{total_msgs}] Erro na clonagem: {e}", flush=True)
        posted.add(msg.id)
        save_posted(origin_id, dest_id, posted)

async def main():
    if len(sys.argv) < 3:
        print("Uso: python cloneia.py <origin_id> <dest_id> [topic_id]")
        sys.exit(1)
        
    try:
        origin_id = int(sys.argv[1])
    except:
        origin_id = sys.argv[1]
        
    try:
        dest_id = int(sys.argv[2])
    except:
        dest_id = sys.argv[2]
        
    topic_id = None
    if len(sys.argv) >= 4 and sys.argv[3].strip():
        topic_id = int(sys.argv[3])

    filters = load_filters()

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    update_status(status="starting", message="Conectando ao Telegram...")
    
    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        update_status(status="error", message="Autenticação necessária via Terminal!")
        print("📲 Autenticação necessária! Siga os passos no terminal.")
        await client.start()
        
    origin = await client.get_entity(origin_id)
    dest = await client.get_entity(dest_id)
    
    posted = load_posted(origin_id, dest_id)
    update_status(status="analyzing", message="Buscando mensagens...")
    
    messages = []
    kwargs = {}
    if topic_id:
        kwargs['reply_to'] = topic_id
        
    async for msg in client.iter_messages(origin, **kwargs):
        if msg.id not in posted:
            messages.append(msg)
            
    messages.reverse()
    total = len(messages)
    
    if total == 0:
        update_status(status="completed", message="Todas as mensagens já foram clonadas!")
        await client.disconnect()
        return

    update_status(status="running", message=f"{total} novas mensagens encontradas!")
    
    for i, msg in enumerate(messages, 1):
        await clone_message(client, msg, dest, posted, origin_id, dest_id, total, i, filters)
        await asyncio.sleep(1)
        
    update_status(status="completed", message="Clonagem Completa!", percent=100)
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
