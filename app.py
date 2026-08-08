import os
import json
import subprocess
from flask import Flask, render_template, jsonify, request
from pathlib import Path

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

    if not origin or not dest:
        return jsonify({"success": False, "error": "ID de Origem e Destino são obrigatórios."})

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
