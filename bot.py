import os
import json
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get('TELEGRAM_TOKEN').strip()
URL = "https://dre-granja-bot.onrender.com"
PORT = int(os.environ.get('PORT', 10000))

def conectar_planilha():
    try:
        print("Conectando na planilha...")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_json = os.environ.get('GCP_CREDS')
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        planilha = client.open("DRE-Granja-Dados")
        print("Planilha conectada com sucesso!")
        return planilha
    except Exception as e:
        print(f"ERRO AO CONECTAR PLANILHA: {e}")
        return None

planilha = conectar_planilha()

def moeda(valor):
    return f"R$ {float(valor):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = """Salve! Bot Dre Granja no ar 🐔

Comandos:
/despesa Racao 350,50
/venda Ovos 1200
/resumo"""
    await update.message.reply_text(texto)

async def despesa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not planilha:
        await update.message.reply_text("Erro: Planilha não conectada.")
        return
    try:
        item = context.args[0]
        valor = float(context.args[1].replace(',', '.'))
        data = datetime.now().strftime('%d/%m/%Y %H:%M')
        aba = planilha.worksheet('MOVIMENTACOES')
        aba.append_row([data, 'DESPESA', item, valor])
        await update.message.reply_text(f"Despesa: {item} = {moeda(valor)}")
    except IndexError:
        await update.message.reply_text("Uso: /despesa Racao 350,50")
    except Exception as e:
        await update.message.reply_text(f"Erro: {str(e)}")

async def venda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not planilha:
        await update.message.reply_text("Erro: Planilha não conectada.")
        return
    try:
        item = context.args[0]
        valor = float(context.args[1].replace(',', '.'))
        data = datetime.now().strftime('%d/%m/%Y %H:%M')
        aba = planilha.worksheet('MOVIMENTACOES')
        aba.append_row([data, 'RECEITA', item, valor])
        await update.message.reply_text(f"Venda: {item} = {moeda(valor)} 💰")
    except IndexError:
        await update.message.reply_text("Uso: /venda Ovos 1200")
    except Exception as e:
        await update.message.reply_text(f"Erro: {str(e)}")

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not planilha:
        await update.message.reply_text("Erro: Planilha não conectada.")
        return
    try:
        aba = planilha.worksheet('MOVIMENTACOES')
        dados = aba.get_all_values()[1:]
        total_vendas = sum([float(linha[3]) for linha in dados if len(linha) > 3 and linha[1] == 'RECEITA'])
        total_despesas = sum([float(linha[3]) for linha in dados if len(linha) > 3 and linha[1] == 'DESPESA'])
        lucro = total_vendas - total_despesas
        texto = f"""**RESUMO DRE**
Receitas: {moeda(total_vendas)}
Despesas: {moeda(total_despesas)}

**Lucro: {moeda(lucro)}**"""
        await update.message.reply_text(texto)
    except Exception as e:
        await update.message.reply_text(f"Erro ao gerar resumo: {str(e)}")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("despesa", despesa))
    application.add_handler(CommandHandler("venda", venda))
    application.add_handler(CommandHandler("resumo", resumo))

    print("Iniciando webhook...")
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{URL}/{TOKEN}",
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()
