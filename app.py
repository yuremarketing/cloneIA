import os
import json
import subprocess
import asyncio
from flask import Flask, render_template, jsonify, request
from pathlib import Path
import telegram_auth
app = Flask(__name__)
PROGRESS_FILE = Path('progress.json')

# Inicializa o progress.json se não existir
if not PROGRESS_FILE.exists():
    PROGRESS_FILE.write_text(json.dumps({
        "status": "idle",
        "message": "Sistema pronto",
        "action": "",
        "current_mb": 0,
        "total_mb": 0,
        "percent": 0,
        "msg_current": 0,
        "msg_total": 0
    }))

@app.route('/')
def index():
    return render_template('index.html')

def get_config():
    CONFIG_FILE = Path('config.json')
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except:
            return {}
    return {}

def save_config(data):
    CONFIG_FILE = Path('config.json')
    current = get_config()
    current.update(data)
    CONFIG_FILE.write_text(json.dumps(current))

@app.route('/api/auth/status')
def auth_status():
    config = get_config()
    api_id = config.get('TELEGRAM_API_ID')
    api_hash = config.get('TELEGRAM_API_HASH')
    
    is_auth = False
    if api_id and api_hash:
        try:
            is_auth = asyncio.run(telegram_auth.check_auth_status(api_id, api_hash))
        except Exception:
            is_auth = False
            
    return jsonify({"authorized": is_auth, "has_keys": bool(api_id and api_hash)})

@app.route('/api/auth/send', methods=['POST'])
def auth_send():
    phone = request.json.get('phone')
    api_id = request.json.get('api_id')
    api_hash = request.json.get('api_hash')
    
    if not phone or not api_id or not api_hash:
        return jsonify({"success": False, "error": "Telefone, API ID e API Hash são obrigatórios."})
        
    try:
        api_id = int(api_id)
    except ValueError:
        return jsonify({"success": False, "error": "API ID deve ser um número."})
        
    result = asyncio.run(telegram_auth.send_otp(phone, api_id, api_hash))
    return jsonify(result)

@app.route('/api/auth/verify', methods=['POST'])
def auth_verify():
    phone = request.json.get('phone')
    code = request.json.get('code')
    phone_code_hash = request.json.get('phone_code_hash')
    api_id = request.json.get('api_id')
    api_hash = request.json.get('api_hash')
    
    if not all([phone, code, phone_code_hash, api_id, api_hash]):
        return jsonify({"success": False, "error": "Dados incompletos."})
    
    try:
        api_id = int(api_id)
    except:
        pass
        
    result = asyncio.run(telegram_auth.verify_otp(phone, code, phone_code_hash, api_id, api_hash))
    
    if result.get("success"):
        # Salva as credenciais permanentemente no config.json após sucesso
        save_config({
            'TELEGRAM_API_ID': api_id,
            'TELEGRAM_API_HASH': api_hash
        })
        
    return jsonify(result)

@app.route('/api/chats', methods=['GET'])
def get_chats():
    config = get_config()
    api_id = config.get('TELEGRAM_API_ID')
    api_hash = config.get('TELEGRAM_API_HASH')
    
    if not api_id or not api_hash:
        return jsonify({"success": False, "error": "Chaves não configuradas"})
        
    try:
        result = asyncio.run(telegram_auth.get_user_chats(api_id, api_hash))
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": f"Falha ao buscar chats: {str(e)}"})


@app.route('/api/progress')
def get_progress():
    try:
        if PROGRESS_FILE.exists():
            data = json.loads(PROGRESS_FILE.read_text())
            return jsonify(data)
    except:
        pass
    return jsonify({"status": "error", "message": "Não foi possível ler o status."})

@app.route('/api/start', methods=['POST'])
def start_cloning():
    data = request.json
    origin = data.get('origin')
    dest = data.get('dest')
    topic = data.get('topic', '')
    filters = data.get('filters', {})

    if not origin or not dest:
        return jsonify({"success": False, "error": "ID de Origem e Destino são obrigatórios."})

    # Salva os filtros preservando as credenciais no config.json
    save_config(filters)

    # Reseta o progresso
    PROGRESS_FILE.write_text(json.dumps({
        "status": "starting",
        "message": "Inicializando motor...",
        "action": "",
        "current_mb": 0,
        "total_mb": 0,
        "percent": 0,
        "msg_current": 0,
        "msg_total": 0
    }))

    # Inicia o script em background
    args = ["python3", "cloneia.py", str(origin), str(dest)]
    if topic:
        args.append(str(topic))
        
    subprocess.Popen(args)
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
