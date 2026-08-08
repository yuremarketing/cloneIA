#!/usr/bin/env python3
"""
🔍 CloneIA Server Monitor - Monitora o servidor em tempo real
Faz as mesmas requisições que o navegador faria e mostra tudo no terminal.
"""
import requests
import time
import sys
import json
from datetime import datetime

BASE_URL = "https://cloneia-dashboard.onrender.com"

ENDPOINTS = [
    {"path": "/", "label": "Página Principal"},
    {"path": "/api/auth/status", "label": "Auth Status"},
    {"path": "/api/chats", "label": "Lista de Chats"},
    {"path": "/api/progress", "label": "Progresso"},
]

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

def check_endpoint(session, endpoint):
    path = endpoint["path"]
    label = endpoint["label"]
    url = f"{BASE_URL}{path}"
    
    try:
        start = time.time()
        res = session.get(url, timeout=15)
        elapsed = (time.time() - start) * 1000  # ms
        
        status = res.status_code
        if status == 200:
            color = GREEN
        elif status == 404:
            color = YELLOW
        else:
            color = RED
        
        print(f"  {color}{BOLD}{status}{RESET} {label:20s} {elapsed:6.0f}ms", end="")
        
        # Se for JSON, mostra o conteúdo resumido
        if path.startswith("/api/"):
            try:
                data = res.json()
                # Resumo inteligente
                if path == "/api/auth/status":
                    auth = data.get("authorized", "?")
                    keys = data.get("has_keys", "?")
                    auth_color = GREEN if auth else RED
                    print(f"  → {auth_color}authorized={auth}{RESET}, has_keys={keys}", end="")
                elif path == "/api/chats":
                    if data.get("success"):
                        n = len(data.get("chats", []))
                        print(f"  → {GREEN}{n} chats encontrados{RESET}", end="")
                    else:
                        err = data.get("error", "desconhecido")
                        print(f"  → {RED}ERRO: {err}{RESET}", end="")
                elif path == "/api/progress":
                    status_val = data.get("status", "?")
                    msg = data.get("message", "")
                    mc = data.get("msg_current", 0)
                    mt = data.get("msg_total", 0)
                    pct = data.get("percent", 0)
                    if status_val == "running":
                        print(f"  → {CYAN}[{mc}/{mt}] {pct}% - {msg}{RESET}", end="")
                    elif status_val == "error":
                        print(f"  → {RED}ERRO: {msg}{RESET}", end="")
                    elif status_val == "completed":
                        print(f"  → {GREEN}✅ {msg}{RESET}", end="")
                    else:
                        print(f"  → {YELLOW}{status_val}: {msg}{RESET}", end="")
            except:
                size = len(res.content)
                print(f"  → {size} bytes", end="")
        else:
            size = len(res.content)
            print(f"  → {size} bytes (HTML)", end="")
        
        print()  # newline
        return True
        
    except requests.exceptions.Timeout:
        print(f"  {RED}{BOLD}TIMEOUT{RESET} {label:20s}  → Servidor não respondeu em 15s")
        return False
    except requests.exceptions.ConnectionError:
        print(f"  {RED}{BOLD}OFFLINE{RESET} {label:20s}  → Servidor fora do ar ou hibernando")
        return False
    except Exception as e:
        print(f"  {RED}{BOLD}ERRO{RESET}    {label:20s}  → {e}")
        return False


def main():
    mode = "once"
    interval = 5
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--live":
            mode = "live"
        if len(sys.argv) > 2:
            try:
                interval = int(sys.argv[2])
            except:
                pass

    session = requests.Session()
    session.headers.update({
        "User-Agent": "CloneIA-Monitor/1.0"
    })

    if mode == "once":
        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f" {BLUE}{BOLD}🔍 CloneIA Server Monitor{RESET}")
        print(f" {CYAN}URL: {BASE_URL}{RESET}")
        print(f" {CYAN}Hora: {datetime.now().strftime('%H:%M:%S')}{RESET}")
        print(f"{BOLD}{'='*60}{RESET}\n")
        
        for ep in ENDPOINTS:
            check_endpoint(session, ep)
        
        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f" Dica: Use {YELLOW}python3 monitor.py --live{RESET} para monitorar em tempo real")
        print(f" Dica: Use {YELLOW}python3 monitor.py --live 3{RESET} para atualizar a cada 3 segundos")
        print(f"{BOLD}{'='*60}{RESET}\n")
    
    else:
        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f" {BLUE}{BOLD}🔍 CloneIA Server Monitor - MODO LIVE{RESET}")
        print(f" {CYAN}URL: {BASE_URL}{RESET}")
        print(f" {CYAN}Intervalo: {interval}s | Ctrl+C para parar{RESET}")
        print(f"{BOLD}{'='*60}{RESET}")
        
        try:
            while True:
                now = datetime.now().strftime('%H:%M:%S')
                print(f"\n{BOLD}[{now}]{RESET}")
                for ep in ENDPOINTS:
                    check_endpoint(session, ep)
                time.sleep(interval)
        except KeyboardInterrupt:
            print(f"\n\n{YELLOW}Monitor encerrado.{RESET}\n")


if __name__ == "__main__":
    main()
