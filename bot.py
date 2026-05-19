import os
import json
import gspread
from datetime import datetime
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Config
TOKEN = os.environ["TELEGRAM_TOKEN"]
SHEET_ID = os.environ["SHEET_ID"]
GSPREAD_JSON = os.environ["GSPREAD_JSON"]

# Google Sheets
creds = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(creds)
sheet = gc.open_by_key(SHEET_ID)

# Flask pra manter o Render vivo
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return 'Bot DRE Granja Online'

@flask_app.route('/webhook', methods=['POST'])
def webhook():
    application.update_queue.put(Update.de_json(request.get_json(force=True), application.bot))
    return 'ok'

# Telegram Bot
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salve! Bot Dre Granja no ar 🐔\n\n"
        "Financeiro:\n"
        "/despesa Item Categoria Valor\n"
        "/venda Item Categoria Valor\n"
        "/resumo\n\n"
        "Produção:\n"
        "/producao Ovos Mort RacaoKg Receita Custos Desp [Obs]"
    )

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
        
        await update.message.reply_text(f"✅ Produção lançada!\nOvos: {ovos} | Mort: {mort} | Ração: {racao}kg")
    except Exception as e:
        await update.message.reply_text(f"❌ Erro: {str(e)}")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("producao", producao))

if __name__ == "__main__":
    application.run_polling()
