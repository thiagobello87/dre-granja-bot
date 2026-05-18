import os
import json
import threading
from flask import Flask
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ===== DUMMY SERVER PRO RENDER NÃO MATAR O BOT =====
app = Flask('')

@app.route('/')
def home():
    return "Bot Dre Granja tá online!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask).start()
# ===================================================

# ===== CONFIG GOOGLE SHEETS =====
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_json = os.environ.get('GCP_CREDS')
creds_dict = json.loads(creds_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# COLOCA O NOME DA SUA PLANILHA AQUI
sheet = client.open("Planilha Dre Granja").sheet1
# =================================

# ===== COMANDOS DO BOT =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salve! Bot Dre Granja no ar. Manda /add pra adicionar cliente.")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        nome = context.args[0]
        valor = context.args[1]
        sheet.append_row([nome, valor])
        await update.message.reply_text(f"Cliente {nome} adicionado com R${valor}")
    except:
        await update.message.reply_text("Usa assim: /add NomeDaPessoa 150")

# ===== INICIA O BOT =====
TOKEN = os.environ.get('TELEGRAM_TOKEN')
application = ApplicationBuilder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", add))

application.run_polling()
