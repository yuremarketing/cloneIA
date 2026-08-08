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

@app.route('/api/auth/status')
def auth_status():
    is_auth = asyncio.run(telegram_auth.check_auth_status())
    return jsonify({"authorized": is_auth})

@app.route('/api/auth/send', methods=['POST'])
def auth_send():
    phone = request.json.get('phone')
    if not phone:
        return jsonify({"success": False, "error": "Telefone é obrigatório."})
    result = asyncio.run(telegram_auth.send_otp(phone))
    return jsonify(result)

@app.route('/api/auth/verify', methods=['POST'])
def auth_verify():
    phone = request.json.get('phone')
    code = request.json.get('code')
    phone_code_hash = request.json.get('phone_code_hash')
    if not all([phone, code, phone_code_hash]):
        return jsonify({"success": False, "error": "Dados incompletos."})
    
    result = asyncio.run(telegram_auth.verify_otp(phone, code, phone_code_hash))
    return jsonify(result)


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

    # Salva os filtros no config.json
    CONFIG_FILE = Path('config.json')
    CONFIG_FILE.write_text(json.dumps(filters))

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
