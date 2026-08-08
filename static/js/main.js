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

    // Check Auth Status on Load
    async function checkAuth() {
        try {
            const res = await fetch('/api/auth/status');
            const data = await res.json();
            if (!data.authorized) {
                loginModal.style.display = 'flex';
                if (data.has_keys) {
                    document.getElementById('api_credentials_group').style.display = 'none';
                }
            } else {
                fetchChats();
            }
        } catch (e) {
            console.error('Failed to check auth', e);
        }
    }
    checkAuth();
    
    // Fetch and populate chats
    async function fetchChats() {
        try {
            const res = await fetch('/api/chats');
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
            }
        } catch (e) {
            console.error('Failed to fetch chats', e);
        }
    }

    // Send Code
    btnSendCode.addEventListener('click', async () => {
        const phone = phoneInput.value.trim();
        const apiId = document.getElementById('api_id').value.trim();
        const apiHash = document.getElementById('api_hash').value.trim();
        
        if(!phone) return alert("Digite o número com DDI (+55...)");
        
        // Se a div de credenciais estiver visível, exige os campos
        if (document.getElementById('api_credentials_group').style.display !== 'none') {
            if(!apiId || !apiHash) return alert("API ID e API Hash são obrigatórios para a primeira configuração.");
        }
        
        btnSendCode.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
        btnSendCode.disabled = true;

        const payload = { phone };
        if (apiId) payload.api_id = apiId;
        if (apiHash) payload.api_hash = apiHash;

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
        } else {
            alert(data.error);
        }
        btnSendCode.innerHTML = 'ENVIAR CÓDIGO';
        btnSendCode.disabled = false;
    });

    // Verify Code
    btnVerifyCode.addEventListener('click', async () => {
        const phone = phoneInput.value.trim();
        const code = codeInput.value.trim();
        const apiId = document.getElementById('api_id').value.trim();
        const apiHash = document.getElementById('api_hash').value.trim();
        
        if(!code) return alert("Digite o código recebido.");
        
        btnVerifyCode.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
        btnVerifyCode.disabled = true;

        const payload = { phone, code, phone_code_hash: currentPhoneHash };
        if (apiId) payload.api_id = apiId;
        if (apiHash) payload.api_hash = apiHash;

        const res = await fetch('/api/auth/verify', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.success) {
            loginModal.style.display = 'none';
            alert("Autenticado com sucesso!");
            fetchChats();
        } else {
            alert(data.error);
        }
        btnVerifyCode.innerHTML = 'ENTRAR';
        btnVerifyCode.disabled = false;
    });

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
                startPolling();
            } else {
                alert('Erro: ' + data.error);
                btn.innerHTML = '<span>INICIAR CLONAGEM</span><i class="fa-solid fa-bolt"></i>';
                btn.disabled = false;
            }
        } catch (err) {
            alert('Erro de conexão com o servidor.');
            btn.innerHTML = '<span>INICIAR CLONAGEM</span><i class="fa-solid fa-bolt"></i>';
            btn.disabled = false;
        }
    });

    async function fetchProgress() {
        try {
            const res = await fetch('/api/progress');
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

                if (data.status === 'completed' || data.status === 'error') {
                    clearInterval(pollingInterval);
                    elProgBar.style.width = `100%`;
                    if (data.status === 'completed') {
                        elProgBar.style.background = 'linear-gradient(90deg, #00ff88, #00b35f)';
                        elProgBar.style.boxShadow = '0 0 15px #00ff88';
                        elCurrentMsg.innerHTML = '<i class="fa-solid fa-circle-check" style="color:#00ff88;"></i> Concluído!';
                    }
                }
            }
        } catch (err) {
            console.error('Falha ao buscar progresso', err);
        }
    }

    function startPolling() {
        if(pollingInterval) clearInterval(pollingInterval);
        pollingInterval = setInterval(fetchProgress, 1000);
    }
});
