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
    
    let pollingInterval = null;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const origin = document.getElementById('origin').value;
        const dest = document.getElementById('dest').value;
        const topic = document.getElementById('topic').value;

        const btn = document.getElementById('btn-start');
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Iniciando...';
        btn.disabled = true;

        try {
            const res = await fetch('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ origin, dest, topic })
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
