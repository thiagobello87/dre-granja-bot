import os
import json
import logging
from datetime import datetime

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']

def get_sheet():
    try:
        creds_json = os.environ['GOOGLE_CREDS_JSON'].strip()
        creds_dict = json.loads(creds_json)
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client.open("DRE-Granja-Dados").worksheet("MOVIMENTACOES")
    except Exception as e:
        logger.error(f"ERRO PLANILHA: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salve! Bot Dre Granja no ar 🐔\n\n/despesa Racao 350,50\n/venda Ovos 1200\n/resumo")

async def despesa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sheet = get_sheet()
    if not sheet:
        await update.message.reply_text("Erro: Planilha não conectada.")
        return
    try:
        item, valor = context.args[0], float(context.args[1].replace(',', '.'))
        data = datetime.now().strftime('%d/%m/%Y %H:%M')
        sheet.append_row([data, item, "Despesa", valor])
        await update.message.reply_text(f"Despesa {item} de R$ {valor:.2f} lançada!")
    except:
        await update.message.reply_text("Use: /despesa Item Valor")

async def venda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sheet = get_sheet()
    if not sheet:
        await update.message.reply_text("Erro: Planilha não conectada.")
        return
    try:
        item, valor = context.args[0], float(context.args[1].replace(',', '.'))
        data = datetime.now().strftime('%d/%m/%Y %H:%M')
        sheet.append_row([data, item, "Venda", valor])
        await update.message.reply_text(f"Venda {item} de R$ {valor:.2f} lançada!")
    except:
        await update.message.reply_text("Use: /venda Item Valor")

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sheet = get_sheet()
    if not sheet:
        await update.message.reply_text("Erro: Planilha não conectada.")
        return
    dados = sheet.get_all_records()
    tv = sum([float(d['Valor']) for d in dados if d['Tipo'] == 'Venda'])
    td = sum([float(d['Valor']) for d in dados if d['Tipo'] == 'Despesa'])
    await update.message.reply_text(f"Vendas: R$ {tv:.2f}\nDespesas: R$ {td:.2f}\nSaldo: R$ {tv-td:.2f}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("despesa", despesa))
    app.add_handler(CommandHandler("venda", venda))
    app.add_handler(CommandHandler("resumo", resumo))
    app.run_polling()

if __name__ == '__main__':
    main()
