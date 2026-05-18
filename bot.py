import os
import json
import logging
from datetime import datetime

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
PORT = int(os.environ.get('PORT', 10000))

# --- PLANILHA ---
def conectar_planilha():
    logger.info("Conectando na planilha...")
    try:
        creds_json = os.environ['GOOGLE_CREDS_JSON'].strip()
        creds_dict = json.loads(creds_json)
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("DRE-Granja-Dados").worksheet("MOVIMENTACOES")
        logger.info("Planilha conectada com sucesso!")
        return sheet
    except Exception as e:
        logger.error(f"ERRO AO CONECTAR PLANILHA: {e}")
        return None

SHEET = conectar_planilha()

# --- FLASK + PTB ---
flask_app = Flask(__name__)
bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

# --- COMANDOS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salve! Bot Dre Granja no ar 🐔\n\n"
        "Comandos:\n"
        "/despesa Racao 350,50\n"
        "/venda Ovos 1200\n"
        "/resumo"
    )

async def despesa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not SHEET:
        await update.message.reply_text("Erro: Planilha não conectada. Checa as credenciais.")
        return
    try:
        item = context.args[0]
        valor = float(context.args[1].replace(',', '.'))
        data = datetime.now().strftime('%d/%m/%Y %H:%M')
        SHEET.append_row([data, item, "Despesa", valor])
        await update.message.reply_text(f"Despesa {item} de R$ {valor:.2f} lançada!")
    except (IndexError, ValueError):
        await update.message.reply_text("Use: /despesa Item Valor\nEx: /despesa Racao 350,50")

async def venda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not SHEET:
        await update.message.reply_text("Erro: Planilha não conectada. Checa as credenciais.")
        return
    try:
        item = context.args[0]
        valor = float(context.args[1].replace(',', '.'))
        data = datetime.now().strftime('%d/%m/%Y %H:%M')
        SHEET.append_row([data, item, "Venda", valor])
        await update.message.reply_text(f"Venda {item} de R$ {valor:.2f} lançada!")
    except (IndexError, ValueError):
        await update.message.reply_text("Use: /venda Item Valor\nEx: /venda Ovos 1200")

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not SHEET:
        await update.message.reply_text("Erro: Planilha não conectada. Checa as credenciais.")
        return
    try:
        dados = SHEET.get_all_records()
        total_venda = sum([float(d['Valor']) for d in dados if d['Tipo'] == 'Venda'])
        total_despesa = sum([float(d['Valor']) for d in dados if d['Tipo'] == 'Despesa'])
        saldo = total_venda - total_despesa
        await update.message.reply_text(
            f"Resumo DRE Granja:\n\n"
            f"Vendas: R$ {total_venda:.2f}\n"
            f"Despesas: R$ {total_despesa:.2f}\n"
            f"Saldo: R$ {saldo:.2f}"
        )
    except Exception as e:
        logger.error(f"Erro no resumo: {e}")
        await update.message.reply_text("Erro ao gerar resumo.")

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("despesa", despesa))
bot_app.add_handler(CommandHandler("venda", venda))
bot_app.add_handler(CommandHandler("resumo", resumo))

# --- ROTAS ---
@flask_app.route('/webhook', methods=['POST'])
async def webhook():
    await bot_app.process_update(Update.de_json(request.get_json(force=True), bot_app.bot))
    return 'ok'

@flask_app.route('/setwebhook', methods=['GET'])
async def set_webhook():
    url = f"{os.environ.get('RENDER_EXTERNAL_URL')}/webhook"
    await bot_app.bot.set_webhook(url=url)
    return f"Webhook setado: {url}"

@flask_app.route('/')
def index():
    return 'Bot no ar!'

# --- INICIALIZAÇÃO CORRETA PTB 21.6 ---
async def setup():
    await bot_app.initialize()
    await bot_app.start()

bot_app.job_queue # força criação da job_queue
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(setup())

if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=PORT)
