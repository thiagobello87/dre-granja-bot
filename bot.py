import os
import json
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import asyncio

TOKEN = os.environ['TELEGRAM_TOKEN']
SHEET_ID = os.environ['SHEET_ID']
GOOGLE_CREDS = json.loads(os.environ['GOOGLE_CREDS_JSON'])

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDS, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID)
aba_mov = sheet.worksheet('MOVIMENTACOES')
aba_diario = sheet.worksheet('DIARIO')

app = Flask(__name__)
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

async def despesa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 3:
            await update.message.reply_text("Use: /despesa Item Categoria Valor")
            return
        valor = float(args[-1].replace(',', '.'))
        categoria = args[-2]
        item = ' '.join(args[:-2])
        linha = [datetime.now().strftime('%d/%m/%Y %H:%M:%S'), item, categoria, 'Despesa', valor]
        aba_mov.append_row(linha)
        await update.message.reply_text(f"Despesa {item} [{categoria}] de R$ {valor:.2f} lançada!")
    except Exception as e:
        await update.message.reply_text(f"Erro: {str(e)}")

async def venda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 3:
            await update.message.reply_text("Use: /venda Item Categoria Valor")
            return
        valor = float(args[-1].replace(',', '.'))
        categoria = args[-2]
        item = ' '.join(args[:-2])
        linha = [datetime.now().strftime('%d/%m/%Y %H:%M:%S'), item, categoria, 'Venda', valor]
        aba_mov.append_row(linha)
        await update.message.reply_text(f"Venda {item} [{categoria}] de R$ {valor:.2f} lançada!")
    except Exception as e:
        await update.message.reply_text(f"Erro: {str(e)}")

async def producao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 7:
            await update.message.reply_text(
                "Use: /producao Ovos Mort RacaoKg Receita Custos Desp [Obs]\n"
                "Ex: /producao 684 2 165.8 800 200 0 Coleta normal"
            )
            return

        ovos = int(args[0])
        mortalidade = int(args[1])
        racao_kg = float(args[2].replace(',', '.'))
        receita = float(args[3].replace(',', '.'))
        custos = float(args[4].replace(',', '.'))
        despesas = float(args[5].replace(',', '.'))
        obs = ' '.join(args[6:]) if len(args) > 6 else ''

        nova_linha = [
            datetime.now().strftime('%d/%m/%Y'),
            ovos,
            mortalidade,
            racao_kg,
            receita,
            custos,
            despesas,
            obs
        ]

        aba_diario.append_row(nova_linha)

        await update.message.reply_text(
            f"Produção lançada!\n"
            f"Ovos: {ovos} | Mort: {mortalidade}\n"
            f"Ração: {racao_kg}kg | Receita: R$ {receita:.2f}\n"
            f"Custos: R$ {custos:.2f} | Desp: R$ {despesas:.2f}"
        )
    except Exception as e:
        await update.message.reply_text(f"Erro: {str(e)}")

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dados = aba_mov.get_all_records()
        if not dados:
            await update.message.reply_text("Nenhum lançamento ainda.")
            return
        total_vendas = sum(float(row['Valor']) for row in dados if row['Tipo'] == 'Venda')
        total_despesas = sum(float(row['Valor']) for row in dados if row['Tipo'] == 'Despesa')
        saldo = total_vendas - total_despesas
        msg = f"Resumo Geral\nVendas: R$ {total_vendas:.2f}\nDespesas: R$ {total_despesas:.2f}\nSaldo: R$ {saldo:.2f}"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"Erro: {str(e)}")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("despesa", despesa))
application.add_handler(CommandHandler("venda", venda))
application.add_handler(CommandHandler("producao", producao))
application.add_handler(CommandHandler("resumo", resumo))

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run(application.process_update(update))
    return 'ok', 200

@app.route('/')
def index():
    return 'Bot Dre Granja Online', 200

if __name__ == '__main__':
    app.run(port=5000)
