#!/usr/bin/env python3
"""
🚀 CloneIA - Telegram Channel Cloner
Clone conteúdo de canais/grupos do Telegram, incluindo os protegidos!
"""
import asyncio
import os
import time
import json
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')

if not API_ID or not API_HASH:
    print("❌ ERRO: Configure o TELEGRAM_API_ID e TELEGRAM_API_HASH no arquivo .env")
    exit(1)

SESSION = 'cloneia_session'
CACHE_DIR = Path('clone_cache')
TEMP_DIR = Path('temp_clone')

last_print_time = 0

def progress_callback(current, total, action_name):
    global last_print_time
    now = time.time()
    if now - last_print_time > 3:
        percent = (current / total) * 100 if total > 0 else 0
        current_mb = current / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        print(f"   ⏳ {action_name}: {current_mb:.1f} MB / {total_mb:.1f} MB ({percent:.1f}%)", flush=True)
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

async def clone_message(client, msg, dest_entity, posted, origin_id, dest_id, total_msgs, current_idx):
    try:
        caption = msg.text or ''
        
        if msg.media:
            print(f"\n📥 [{current_idx}/{total_msgs}] Iniciando DOWNLOAD da mídia...", flush=True)
            temp_path = await client.download_media(
                msg, 
                file=str(TEMP_DIR) + '/',
                progress_callback=lambda c, t: progress_callback(c, t, "Download")
            )
            if temp_path:
                print(f"📤 [{current_idx}/{total_msgs}] Download concluído! Iniciando UPLOAD...", flush=True)
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
        elif msg.text:
            await client.send_message(dest_entity, msg.text)
            print(f"📝 [{current_idx}/{total_msgs}] Texto clonado!", flush=True)
        
        posted.add(msg.id)
        save_posted(origin_id, dest_id, posted)
        
    except FloodWaitError as e:
        print(f"⏳ FloodWait: o Telegram pediu para aguardar {e.seconds}s...", flush=True)
        await asyncio.sleep(e.seconds + 1)
        await clone_message(client, msg, dest_entity, posted, origin_id, dest_id, total_msgs, current_idx)
    except Exception as e:
        print(f"❌ [{current_idx}/{total_msgs}] Erro na clonagem: {e}", flush=True)
        posted.add(msg.id)
        save_posted(origin_id, dest_id, posted)

async def main():
    print("=" * 60)
    print(" 🚀 CloneIA - Telegram Channel Cloner")
    print("=" * 60)
    
    origin_input = input("📌 Digite o ID ou Link do Canal/Grupo de ORIGEM: ")
    try:
        origin_id = int(origin_input)
    except:
        origin_id = origin_input
        
    dest_input = input("📌 Digite o ID ou Link do Canal/Grupo de DESTINO: ")
    try:
        dest_id = int(dest_input)
    except:
        dest_id = dest_input
        
    topic_input = input("📌 Digite o ID do Tópico (Deixe em branco para o canal todo): ")
    topic_id = int(topic_input) if topic_input.strip() else None

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    print("\n🔄 Conectando ao Telegram...")
    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        print("📲 Autenticação necessária! Siga os passos abaixo:")
        await client.start()
        
    print("✅ Conectado com sucesso!\n")
    
    origin = await client.get_entity(origin_id)
    dest = await client.get_entity(dest_id)
    
    posted = load_posted(origin_id, dest_id)
    if posted:
        print(f"📋 {len(posted)} mensagens já foram clonadas antes e serão ignoradas.")
    
    print("🔎 Buscando mensagens...")
    messages = []
    
    kwargs = {}
    if topic_id:
        kwargs['reply_to'] = topic_id
        
    async for msg in client.iter_messages(origin, **kwargs):
        if msg.id not in posted:
            messages.append(msg)
            
    messages.reverse() # Mais antigos primeiro
    total = len(messages)
    
    print(f"📊 {total} novas mensagens para clonar encontradas!\n")
    
    for i, msg in enumerate(messages, 1):
        await clone_message(client, msg, dest, posted, origin_id, dest_id, total, i)
        await asyncio.sleep(1) # Delay segurança
        
    print(f"\n🎉 CLONAGEM COMPLETA!")
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
