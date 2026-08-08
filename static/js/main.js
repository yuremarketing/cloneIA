document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('clone-form');
    const setupView = document.getElementById('setup-view');
    const progressView = document.getElementById('progress-view');
    const statsPanel = document.getElementById('stats-panel');
    
    // Elements to update
    const elAction = document.getElementById('stat-action');
    const elTraffic = document.getElementById('stat-traffic');
    const elMsgs = document.getElementById('stat-msgs');
    const elCurrentMsg = document.getElementById('current-message');
    const elProgText = document.getElementById('progress-text');
    const elProgPercent = document.getElementById('progress-percent');
    const elProgBar = document.getElementById('progress-bar');
    
    // Auth elements
    const loginModal = document.getElementById('login-modal');
    const step1 = document.getElementById('login-step-1');
    const step2 = document.getElementById('login-step-2');
    const btnSendCode = document.getElementById('btn-send-code');
    const btnVerifyCode = document.getElementById('btn-verify-code');
    const phoneInput = document.getElementById('phone_number');
    const codeInput = document.getElementById('otp_code');
    
    let pollingInterval = null;
    let currentPhoneHash = null;

    // ============================================================
    // 🔴 SISTEMA DE NOTIFICAÇÕES VISUAIS (Toast)
    // Nunca mais um erro vai ficar escondido no console!
    // ============================================================
    function createToastContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = `
                position: fixed; top: 20px; right: 20px; z-index: 99999;
                display: flex; flex-direction: column; gap: 10px;
                max-width: 420px; pointer-events: none;
            `;
            document.body.appendChild(container);
        }
        return container;
    }

    function showToast(message, type = 'error') {
        const container = createToastContainer();
        const toast = document.createElement('div');
        
        const colors = {
            error:   { bg: '#ff2244', icon: 'fa-circle-exclamation' },
            warning: { bg: '#ff9900', icon: 'fa-triangle-exclamation' },
            success: { bg: '#00cc66', icon: 'fa-circle-check' },
            info:    { bg: '#3399ff', icon: 'fa-circle-info' }
        };
        const c = colors[type] || colors.error;
        
        toast.style.cssText = `
            background: ${c.bg}; color: #fff; padding: 14px 20px;
            border-radius: 12px; font-family: 'Inter', sans-serif;
            font-size: 14px; font-weight: 600; pointer-events: auto;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
            display: flex; align-items: center; gap: 10px;
            animation: slideIn 0.3s ease-out;
            cursor: pointer;
        `;
        toast.innerHTML = `<i class="fa-solid ${c.icon}"></i> ${message}`;
        toast.onclick = () => toast.remove();
        
        container.appendChild(toast);
        
        // Auto-remove após 8 segundos
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.animation = 'fadeOut 0.3s ease-in';
                setTimeout(() => toast.remove(), 300);
            }
        }, 8000);
    }

    // Injetar animações CSS
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        @keyframes fadeOut { from { opacity: 1; } to { opacity: 0; } }
    `;
    document.head.appendChild(style);

    // ============================================================
    // 🛡️ CAPTURADOR GLOBAL DE ERROS
    // Qualquer erro JS que acontecer, aparece na tela.
    // ============================================================
    window.addEventListener('error', (e) => {
        showToast(`Erro JS: ${e.message}`, 'error');
    });
    window.addEventListener('unhandledrejection', (e) => {
        showToast(`Erro não tratado: ${e.reason}`, 'error');
    });

    // ============================================================
    // 🔐 AUTENTICAÇÃO
    // ============================================================
    async function checkAuth() {
        try {
            const res = await fetch('/api/auth/status');
            if (!res.ok) {
                showToast(`Servidor retornou erro ${res.status}. Tente recarregar a página.`, 'error');
                return;
            }
            const data = await res.json();
            if (!data.authorized) {
                loginModal.style.display = 'flex';
                if (data.has_keys) {
                    document.getElementById('api_credentials_group').style.display = 'none';
                }
                showToast('Sessão expirada. Faça login novamente.', 'warning');
            } else {
                showToast('Conectado ao Telegram!', 'success');
                fetchChats();
            }
        } catch (e) {
            showToast('Falha ao conectar com o servidor. Verifique se o site está no ar.', 'error');
        }
    }
    checkAuth();
    
    // ============================================================
    // 📋 BUSCA DE CHATS
    // ============================================================
    async function fetchChats() {
        try {
            const res = await fetch('/api/chats');
            if (!res.ok) {
                showToast(`Erro ao buscar chats: servidor retornou ${res.status}`, 'error');
                return;
            }
            const data = await res.json();
            if (data.success && data.chats) {
                const datalist = document.getElementById('chat-list');
                datalist.innerHTML = '';
                data.chats.forEach(chat => {
                    const option = document.createElement('option');
                    const identifier = chat.username ? `@${chat.username}` : chat.id;
                    option.value = `${chat.title} | ${identifier}`;
                    datalist.appendChild(option);
                });
                showToast(`${data.chats.length} grupos/canais carregados!`, 'info');
            } else if (data.error) {
                // Se deu "Unauthorized", reabre o login
                if (data.error.toLowerCase().includes('unauthorized') || data.error.toLowerCase().includes('não autorizado')) {
                    loginModal.style.display = 'flex';
                    showToast('Sessão do Telegram expirou. Faça login novamente.', 'warning');
                } else {
                    showToast(`Erro ao carregar chats: ${data.error}`, 'error');
                }
            }
        } catch (e) {
            showToast('Falha de rede ao buscar lista de chats.', 'error');
        }
    }

    // ============================================================
    // 📲 ENVIO DE CÓDIGO
    // ============================================================
    btnSendCode.addEventListener('click', async () => {
        const phone = phoneInput.value.trim();
        const apiId = document.getElementById('api_id').value.trim();
        const apiHash = document.getElementById('api_hash').value.trim();
        
        if(!phone) {
            showToast('Digite o número com DDI (+55...)', 'warning');
            return;
        }
        
        // Se a div de credenciais estiver visível, exige os campos
        if (document.getElementById('api_credentials_group').style.display !== 'none') {
            if(!apiId || !apiHash) {
                showToast('API ID e API Hash são obrigatórios para a primeira configuração.', 'warning');
                return;
            }
        }
        
        btnSendCode.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
        btnSendCode.disabled = true;

        const payload = { phone };
        if (apiId) payload.api_id = apiId;
        if (apiHash) payload.api_hash = apiHash;

        try {
            const res = await fetch('/api/auth/send', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (data.success) {
                currentPhoneHash = data.phone_code_hash;
                step1.style.display = 'none';
                step2.style.display = 'block';
                showToast('Código enviado! Verifique seu Telegram.', 'success');
            } else {
                showToast(data.error, 'error');
            }
        } catch (e) {
            showToast('Falha ao enviar código. Servidor fora do ar?', 'error');
        }
        btnSendCode.innerHTML = 'ENVIAR CÓDIGO';
        btnSendCode.disabled = false;
    });

    // ============================================================
    // ✅ VERIFICAÇÃO DO CÓDIGO
    // ============================================================
    btnVerifyCode.addEventListener('click', async () => {
        const phone = phoneInput.value.trim();
        const code = codeInput.value.trim();
        const apiId = document.getElementById('api_id').value.trim();
        const apiHash = document.getElementById('api_hash').value.trim();
        
        if(!code) {
            showToast('Digite o código recebido.', 'warning');
            return;
        }
        
        btnVerifyCode.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
        btnVerifyCode.disabled = true;

        const payload = { phone, code, phone_code_hash: currentPhoneHash };
        if (apiId) payload.api_id = apiId;
        if (apiHash) payload.api_hash = apiHash;

        try {
            const res = await fetch('/api/auth/verify', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (data.success) {
                loginModal.style.display = 'none';
                showToast('Autenticado com sucesso!', 'success');
                fetchChats();
            } else {
                showToast(data.error, 'error');
            }
        } catch (e) {
            showToast('Falha na verificação. Servidor fora do ar?', 'error');
        }
        btnVerifyCode.innerHTML = 'ENTRAR';
        btnVerifyCode.disabled = false;
    });

    // ============================================================
    // 🚀 INICIAR CLONAGEM
    // ============================================================
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        let origin = document.getElementById('origin').value.trim();
        let dest = document.getElementById('dest').value.trim();
        
        if (origin.includes(' | ')) {
            origin = origin.split(' | ')[1];
        }
        if (dest.includes(' | ')) {
            dest = dest.split(' | ')[1];
        }
        
        const topic = document.getElementById('topic').value.trim();

        // Enterprise Filters
        const filters = {
            f_text: document.getElementById('f_text').checked,
            f_photo: document.getElementById('f_photo').checked,
            f_video: document.getElementById('f_video').checked,
            f_document: document.getElementById('f_document').checked,
            f_audio: document.getElementById('f_audio').checked,
            remove_links: document.getElementById('remove_links').checked,
            remove_mentions: document.getElementById('remove_mentions').checked,
            blacklist: document.getElementById('blacklist').value,
            replace_from: document.getElementById('replace_from').value,
            replace_to: document.getElementById('replace_to').value,
            signature: document.getElementById('signature').value
        };

        const btn = document.getElementById('btn-start');
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Iniciando...';
        btn.disabled = true;

        try {
            const res = await fetch('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ origin, dest, topic, filters })
            });
            const data = await res.json();
            
            if(data.success) {
                setupView.style.display = 'none';
                statsPanel.style.display = 'grid';
                progressView.style.display = 'block';
                showToast('Clonagem iniciada!', 'success');
                startPolling();
            } else {
                showToast('Erro ao iniciar: ' + data.error, 'error');
                btn.innerHTML = '<span>INICIAR CLONAGEM</span><i class="fa-solid fa-bolt"></i>';
                btn.disabled = false;
            }
        } catch (err) {
            showToast('Erro de conexão com o servidor. Ele pode ter reiniciado.', 'error');
            btn.innerHTML = '<span>INICIAR CLONAGEM</span><i class="fa-solid fa-bolt"></i>';
            btn.disabled = false;
        }
    });

    // ============================================================
    // 📊 POLLING DE PROGRESSO
    // ============================================================
    let fetchErrors = 0;

    async function fetchProgress() {
        try {
            const res = await fetch('/api/progress');
            if (!res.ok) {
                fetchErrors++;
                if (fetchErrors >= 5) {
                    clearInterval(pollingInterval);
                    showToast('Servidor não responde. Polling interrompido.', 'error');
                }
                return;
            }
            fetchErrors = 0; // Reset no contador de erros

            const data = await res.json();
            
            if (data.status) {
                // Update stats
                elAction.innerText = data.action || data.status;
                elTraffic.innerText = `${data.current_mb} MB`;
                elMsgs.innerText = `${data.msg_current} / ${data.msg_total}`;
                
                // Update center view
                elCurrentMsg.innerText = data.message;
                
                // Update bar
                if (data.total_mb > 0) {
                    elProgText.innerText = `${data.current_mb} MB / ${data.total_mb} MB`;
                    elProgPercent.innerText = `${data.percent}%`;
                    elProgBar.style.width = `${data.percent}%`;
                } else {
                    elProgText.innerText = '';
                    elProgPercent.innerText = '';
                    elProgBar.style.width = `0%`;
                }

                if (data.status === 'completed') {
                    clearInterval(pollingInterval);
                    elProgBar.style.width = `100%`;
                    elProgBar.style.background = 'linear-gradient(90deg, #00ff88, #00b35f)';
                    elProgBar.style.boxShadow = '0 0 15px #00ff88';
                    elCurrentMsg.innerHTML = '<i class="fa-solid fa-circle-check" style="color:#00ff88;"></i> Concluído!';
                    showToast('Clonagem concluída com sucesso!', 'success');
                }
                
                if (data.status === 'error') {
                    clearInterval(pollingInterval);
                    elProgBar.style.width = `100%`;
                    elProgBar.style.background = 'linear-gradient(90deg, #ff2244, #cc0033)';
                    elProgBar.style.boxShadow = '0 0 15px #ff2244';
                    elCurrentMsg.innerHTML = `<i class="fa-solid fa-circle-exclamation" style="color:#ff2244;"></i> ${data.message}`;
                    showToast(`Erro na clonagem: ${data.message}`, 'error');
                }
            }
        } catch (err) {
            fetchErrors++;
            if (fetchErrors >= 5) {
                clearInterval(pollingInterval);
                showToast('Conexão perdida com o servidor. Recarregue a página.', 'error');
            }
        }
    }

    function startPolling() {
        fetchErrors = 0;
        if(pollingInterval) clearInterval(pollingInterval);
        pollingInterval = setInterval(fetchProgress, 1000);
    }
});
