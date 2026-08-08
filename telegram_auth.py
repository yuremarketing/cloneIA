import os
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneNumberInvalidError
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
SESSION = 'cloneia_session'

async def check_auth_status():
    if not API_ID or not API_HASH:
        return False
    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.connect()
    is_authorized = await client.is_user_authorized()
    await client.disconnect()
    return is_authorized

async def send_otp(phone):
    client = TelegramClient(SESSION, API_ID, API_HASH)
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

async def verify_otp(phone, code, phone_code_hash):
    client = TelegramClient(SESSION, API_ID, API_HASH)
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
