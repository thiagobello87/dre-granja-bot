import os
import json
from datetime import datetime
from flask import Flask, request
import gspread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ["TELEGRAM_TOKEN"]
SHEET_ID = os.environ["SHEET_ID"]
GSPREAD_JSON = os.environ["GSPREAD_JSON"]

creds = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(creds)
sheet = gc.open_by_key(SHEET_ID)

flask_app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

@flask_app.route('/')
def home():
    return 'Bot DRE Granja Online'

@flask_app.route('/webhook', methods=['POST'])
async def webhook():
    await application.process_update(
        Update.de_json(request.get_json(force=True), application.bot)
    )
    return 'ok'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salve! Bot Dre Granja no ar 🐔\n\n/producao Ovos Mort RacaoKg Receita Custos Desp [Obs]")

async def producao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 7:
            await update.message.reply_text("Uso: /producao Ovos Mort RacaoKg Receita Custos Desp [Obs]")
            return
        ovos, mort, racao, receita, custos, desp = args[:6]
        obs = " ".join(args[6:]) if len(args) > 6 else ""
        ws = sheet.worksheet("DIARIO")
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        ws.append_row([agora, int(ovos), int(mort), float(racao), float(receita), float(custos), float(desp), obs])
        await update.message.reply_text(f"✅ Lançado! Ovos: {ovos} | Mortes: {mort}")
    except Exception as e:
        await update.message.reply_text(f"❌ Erro: {e}")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("producao", producao))
