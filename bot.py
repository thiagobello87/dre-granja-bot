import os
import json
import asyncio
from flask import Flask
from threading import Thread
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ===== FLASK PRO RENDER NÃO MATAR O SERVIÇO =====
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Dre Granja online!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# ===== CONECTA GOOGLE SHEETS =====
def conectar_planilha():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_json = os.environ.get('GCP_CREDS')

        if not creds_json:
            raise ValueError("Variável GCP_CREDS não encontrada")

        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        # >>> TROCA AQUI PELO NOME EXATO DA SUA PLANILHA <<<
        nome_planilha = "DRE-Granja-Dados"
        return client.open(nome_planilha).sheet1

    except Exception as e:
        print(f"ERRO AO CONECTAR PLANILHA: {e}")
        return None

sheet = conectar_planilha()

# ===== COMANDOS DO TELEGRAM =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if sheet:
        await update.message.reply_text("Salve! Bot Dre Granja no ar. Usa /add Nome 150")
    else:
        await update.message.reply_text("Bot on, mas erro na planilha. Checa os logs do Render.")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not sheet:
        await update.message.reply_text("Erro: Planilha não conectada. Chama o dev.")
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
    TOKEN = os.environ.get('TELEGRAM_TOKEN')
    if not TOKEN:
        raise ValueError("Variável TELEGRAM_TOKEN não encontrada")

    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add))

    print("Bot do Telegram iniciando...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    Thread(target=run_flask, daemon=True).start()
    asyncio.run(run_bot())
