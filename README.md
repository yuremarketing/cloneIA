# 🚀 CloneIA - Telegram Channel Cloner

CloneIA é uma ferramenta de código aberto em Python desenvolvida para **clonar canais e grupos do Telegram de forma 100% automatizada**, conseguindo até mesmo copiar mídias (fotos, vídeos, PDFs) de **Canais Protegidos** (com restrição de encaminhamento).

## ⚠️ Como funciona?
Diferente de scripts antigos que falham ao tentar "encaminhar" mensagens de canais protegidos, o CloneIA automatiza o fluxo real de um usuário: ele faz o **Download** do arquivo para o seu computador (com barra de progresso em tempo real) e depois faz o **Upload** limpo como uma nova mensagem para o canal de destino.

---

## 🛠️ Requisitos
- Python 3.8 ou superior instalado.
- Conta no Telegram (para extrair os dados da API).

## 🚀 Instalação Passo a Passo

### Passo 1: Clone o Repositório
Baixe este projeto para o seu computador:
```bash
git clone https://github.com/yuremarketing/cloneIA.git
cd cloneIA
```

### Passo 2: Instale as Bibliotecas
Instale as dependências executando:
```bash
pip install -r requirements.txt
```

### Passo 3: Pegue suas chaves do Telegram
Você precisa das chaves `API_ID` e `API_HASH` da sua conta do Telegram. É grátis e rápido:
1. Acesse [my.telegram.org](https://my.telegram.org) e faça login com seu número.
2. Clique em **API development tools**.
3. Preencha os campos básicos (o nome não importa).
4. Copie o **App api_id** e o **App api_hash**.

### Passo 4: Configure o Script
1. Renomeie o arquivo `.env.example` para `.env`
2. Abra o arquivo `.env` e cole suas chaves lá:
```env
TELEGRAM_API_ID=1234567
TELEGRAM_API_HASH=abcdef123456789
```

---

## ▶️ Como Usar

Para iniciar a clonagem, basta rodar o script no seu terminal/CMD:

```bash
python cloneia.py
```

O script vai abrir um menu interativo e perguntar:
1. **ID de Origem**: O ID do canal ou grupo de onde você quer copiar.
2. **ID de Destino**: O ID do canal ou grupo novo que você criou para receber os arquivos.
3. **ID do Tópico (Opcional)**: Caso o grupo use o sistema de Tópicos (Fóruns), digite o ID do tópico específico. Se não souber ou quiser o canal todo, apenas aperte `Enter`.

### 🛡️ Sobre a Autenticação
Na **primeira vez** que você rodar o script, ele pedirá o seu número de telefone e o código de confirmação do Telegram (e senha de 2 Fatores, se você tiver). Depois disso, ele vai criar um arquivo seguro `.session` e não vai mais pedir senha. **NUNCA COMPARTILHE ESSE ARQUIVO COM NINGUÉM!**

---

## 💡 Dicas e Segurança
- O Telegram tem limites de download. Se você estiver baixando muitos GIGABYTES, o próprio Telegram vai reduzir a sua velocidade ou pedir para aguardar alguns minutos. O script cuida disso automaticamente, basta deixar a tela aberta.
- O programa salva onde parou! Se você fechar o terminal sem querer, ao abrir de novo ele vai ler a pasta `clone_cache` e continuar a partir do vídeo em que parou, pulando os que já foram.

*Feito com ☕ e Python.*
