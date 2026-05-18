import os
import json
import asyncio
from flask import Flask
from threading import Thread
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ===== FLASK =====
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Dre Granja online!"

# ===== PLANILHA =====
def conectar_planilha():
    try:
        print("Conectando na planilha...")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_json = os.environ.get('GCP_CREDS')
        if not creds_json:
            print("ERRO: GCP_CREDS não encontrada")
            return None
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

# ===== COMANDOS =====
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

# ===== BOT COM LOOP PRÓPRIO + FIX DE SIGNAL =====
async def run_bot_async():
    print("1. Iniciando bot async...")
    TOKEN = os.environ.get('TELEGRAM_TOKEN').strip()
    print(f"2. Token: [{TOKEN[:10]}...] Tamanho: {len(TOKEN)}")

    print("3. Criando Application...")
    application = ApplicationBuilder().token(TOKEN).build()

    print("4. Adicionando handlers...")
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("despesa", despesa))
    application.add_handler(CommandHandler("venda", venda))
    application.add_handler(CommandHandler("resumo", resumo))

    print("5. Bot iniciando polling...")
    # FIX: Desliga signal handlers pq não estamos na main thread
    await application.run_polling(
        drop_pending_updates=True,
        stop_signals=None
    )

def run_bot_thread():
    # Cria loop novo só pra essa thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot_async())

# ===== START =====
if __name__ == '__main__':
    print("Iniciando Thread do Bot...")
    bot_thread = Thread(target=run_bot_thread, daemon=True)
    bot_thread.start()

    print("Iniciando Flask no principal...")
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
