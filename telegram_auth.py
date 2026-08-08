import os
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneNumberInvalidError
from pathlib import Path

SESSION = 'cloneia_session'

async def check_auth_status(api_id, api_hash):
    if not api_id or not api_hash:
        return False
    
    # Se o arquivo de sessão não existir fisicamente, não tenta conectar (para não criar arquivo atoa)
    if not Path(f"{SESSION}.session").exists():
        return False

    client = TelegramClient(SESSION, api_id, api_hash)
    try:
        await client.connect()
        is_authorized = await client.is_user_authorized()
        await client.disconnect()
        return is_authorized
    except Exception:
        return False

async def send_otp(phone, api_id, api_hash):
    if not api_id or not api_hash:
        return {"success": False, "error": "API ID e API Hash são obrigatórios."}
        
    client = TelegramClient(SESSION, api_id, api_hash)
    await client.connect()
    try:
        sent = await client.send_code_request(phone)
        return {"success": True, "phone_code_hash": sent.phone_code_hash}
    except PhoneNumberInvalidError:
        return {"success": False, "error": "Número de telefone inválido. Use o formato internacional (+551199999999)"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        await client.disconnect()

async def verify_otp(phone, code, phone_code_hash, api_id, api_hash):
    client = TelegramClient(SESSION, api_id, api_hash)
    await client.connect()
    try:
        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
        return {"success": True}
    except SessionPasswordNeededError:
        return {"success": False, "error": "Conta com verificação em duas etapas (2FA). O sistema atual ainda não suporta 2FA, desative temporariamente para logar."}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        await client.disconnect()
