import os
import json
import logging
import asyncio
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

flask_app = Flask(__name__)
bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

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
    await update.message.reply_text(
        "Salve! Bot Dre Granja no ar 🐔\n\n"
        "Comandos:\n"
        "/despesa Item Categoria Valor\n"
        "Ex: /despesa Milho Racao 100,50\n\n"
        "/venda Item Categoria Valor\n"
        "Ex: /venda OvosCaipira VendaOvos 200\n\n"
        "/resumo"
    )

async def despesa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sheet = get_sheet()
    if not sheet:
        await update.message.reply_text("Erro: Planilha não conectada.")
        return
    try:
        item = context.args[0]
        categoria = context.args[1]
        valor = float(context.args[2].replace(',', '.'))
        data = datetime.now().strftime('%d/%m/%Y %H:%M')
        sheet.append_row([data, item, categoria, "Despesa", valor])
        await update.message.reply_text(f"Despesa {item} [{categoria}] de R$ {valor:.2f} lançada!")
    except IndexError:
        await update.message.reply_text("Use: /despesa Item Categoria Valor\nEx: /despesa Milho Racao 100,50")
    except ValueError:
        await update.message.reply_text("Valor inválido. Use número: 100,50")
    except Exception as e:
        logger.error(f"Erro despesa: {e}")
        await update.message.reply_text(f"Deu erro: {e}")

async def venda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sheet = get_sheet()
    if not sheet:
        await update.message.reply_text("Erro: Planilha não conectada.")
        return
    try:
        item = context.args[0]
        categoria = context.args[1]
        valor = float(context.args[2].replace(',', '.'))
        data = datetime.now().strftime('%d/%m/%Y %H:%M')
        sheet.append_row([data, item, categoria, "Venda", valor])
        await update.message.reply_text(f"Venda {item} [{categoria}] de R$ {valor:.2f} lançada!")
    except IndexError:
        await update.message.reply_text("Use: /venda Item Categoria Valor\nEx: /venda OvosCaipira VendaOvos 200")
    except ValueError:
        await update.message.reply_text("Valor inválido. Use número: 200")
    except Exception as e:
        logger.error(f"Erro venda: {e}")
        await update.message.reply_text(f"Deu erro: {e}")

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sheet = get_sheet()
    if not sheet:
        await update.message.reply_text("Erro: Planilha não conectada.")
        return
    try:
        dados = sheet.get_all_records()
        def parse_valor(v):
            try:
                return float(str(v).replace(',', '.'))
            except:
                return 0.0

        total_venda = sum([parse_valor(d.get('Valor', 0)) for d in dados if d.get('Tipo') == 'Venda'])
        total_despesa = sum([parse_valor(d.get('Valor', 0)) for d in dados if d.get('Tipo') == 'Despesa'])
        saldo = total_venda - total_despesa

        cat_despesas = {}
        for d in dados:
            if d.get('Tipo') == 'Despesa':
                cat = d.get('Categoria', 'Sem Categoria')
                cat_despesas[cat] = cat_despesas.get(cat, 0) + parse_valor(d.get('Valor', 0))

        texto_cat = "\n".join([f"{cat}: R$ {val:.2f}" for cat, val in cat_despesas.items()])

        await update.message.reply_text(
            f"Resumo DRE Granja:\n\n"
            f"Vendas: R$ {total_venda:.2f}\n"
            f"Despesas: R$ {total_despesa:.2f}\n"
            f"Saldo: R$ {saldo:.2f}\n\n"
            f"Despesas por Categoria:\n{texto_cat if texto_cat else 'Nenhuma'}"
        )
    except Exception as e:
        logger.error(f"Erro no resumo: {e}")
        await update.message.reply_text(f"Erro ao gerar resumo: {e}")

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("despesa", despesa))
bot_app.add_handler(CommandHandler("venda", venda))
bot_app.add_handler(CommandHandler("resumo", resumo))

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

async def setup():
    await bot_app.initialize()
    await bot_app.start()

asyncio.get_event_loop().run_until_complete(setup())
