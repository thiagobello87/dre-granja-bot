import os
import json
import threading
from datetime import datetime
from flask import Flask
import gspread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Pega as variáveis do Render
TOKEN = os.environ["TELEGRAM_TOKEN"]
SHEET_ID = os.environ["SHEET_ID"]
GSPREAD_JSON = os.environ["GSPREAD_JSON"]

# Conecta na planilha
creds = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(creds)
sheet = gc.open_by_key(SHEET_ID)

# Cria o Flask pra enganar o Render
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return 'Bot DRE Granja Online'

# Cria o bot do Telegram
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salve! Bot Dre Granja no ar 🐔\n\n"
        "Use: /producao Ovos Mort RacaoKg Receita Custos Desp [Obs]\n"
        "Ex: /producao 750 2 165 900 230 60 Ração cara"
    )

async def producao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 7:
            await update.message.reply_text(
                "Faltou dado. Uso correto:\n"
                "/producao Ovos Mort RacaoKg Receita Custos Desp [Obs]\n"
                "Ex: /producao 750 2 165 900 230 60 Obs"
            )
            return

        ovos = int(args[0])
        mort = int(args[1])
        racao = float(args[2])
        receita = float(args[3])
        custos = float(args[4])
        desp = float(args[5])
        obs = " ".join(args[6:]) if len(args) > 6 else ""

        ws = sheet.worksheet("DIARIO")
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        ws.append_row([agora, ovos, mort, racao, receita, custos, desp, obs])

        await update.message.reply_text(
            f"✅ Lançamento feito!\n"
            f"Ovos: {ovos} | Mortes: {mort}\n"
            f"Ração: {racao}kg | Receita: R${receita}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Deu erro: {str(e)}")

# Adiciona os comandos no bot
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("producao", producao))

# Função que roda o bot em paralelo
def run_bot():
    application.run_polling()

# Inicia o bot quando o arquivo roda
threading.Thread(target=run_bot, daemon=True).start()
