import os
import json
import asyncio
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

# ===== RODA O BOT =====
async def run_bot():
    print("Iniciando função run_bot...")
    TOKEN = os.environ.get('TELEGRAM_TOKEN')

    if not TOKEN:
        print("ERRO FATAL: TELEGRAM_TOKEN não encontrada nas variáveis de ambiente!")
        return

    print(f"Token encontrado, começando com: {TOKEN[:10]}...")

    try:
        application = ApplicationBuilder().token(TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("add", add))

        print("Bot do Telegram iniciando...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        print("Application started - Bot online!")

        while True:
            await asyncio.sleep(3600)

    except Exception as e:
        print(f"ERRO AO INICIAR BOT: {e}")

# ===== INICIA TUDO =====
if __name__ == '__main__':
    Thread(target=run_flask, daemon=True).start()
    asyncio.run(run_bot())
