import os
import json
from flask import Flask
from threading import Thread
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ===== FLASK PRA MANTER O RENDER ACORDADO =====
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Dre Granja online!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# ===== CONEXÃO COM A PLANILHA =====
def conectar_planilha():
    try:
        print("Conectando na planilha...")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_json = os.environ.get('GCP_CREDS')
        if not creds_json:
            print("ERRO: GCP_CREDS não encontrada")
            return None
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        nome_planilha = "DRE-Granja-Dados"
        sheet = client.open(nome_planilha).sheet1
        print("Planilha conectada com sucesso!")
        return sheet
    except Exception as e:
        print(f"ERRO AO CONECTAR PLANILHA: {e}")
        return None

sheet = conectar_planilha()

# ===== COMANDOS DO BOT =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if sheet:
        await update.message.reply_text("Salve! Bot Dre Granja no ar. Usa /add Nome 150")
    else:
        await update.message.reply_text("Bot on, mas erro na planilha. Checa os logs do Render.")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not sheet:
        await update.message.reply_text("Erro: Planilha não conectada.")
        return
    try:
        nome = context.args[0]
        valor = context.args[1]
        sheet.append_row([nome, valor])
        await update.message.reply_text(f"Boa! {nome} adicionado com R${valor}")
    except IndexError:
        await update.message.reply_text("Formato errado. Usa: /add NomeDaPessoa 150")
    except Exception as e:
        await update.message.reply_text(f"Deu ruim ao salvar: {str(e)}")

# ===== RODA O BOT - SEM ASYNCIO.RUN =====
def run_bot():
    print("1. Iniciando função run_bot...")
    TOKEN = os.environ.get('TELEGRAM_TOKEN')

    if not TOKEN:
        print("ERRO FATAL: TELEGRAM_TOKEN não encontrada!")
        return

    TOKEN = TOKEN.strip()
    print(f"2. Token: [{TOKEN[:10]}...] Tamanho: {len(TOKEN)}")

    print("3. Criando Application...")
    application = ApplicationBuilder().token(TOKEN).build()

    print("4. Adicionando handlers...")
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add))

    print("5. Bot iniciando polling...")
    application.run_polling(drop_pending_updates=True) # Ele gerencia o loop sozinho

# ===== INICIA TUDO =====
if __name__ == '__main__':
    Thread(target=run_flask, daemon=True).start()
    run_bot() # SEM ASYNCIO.RUN()
