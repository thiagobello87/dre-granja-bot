import os
import json
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime

TOKEN = os.environ.get("TELEGRAM_TOKEN")
SEU_TELEGRAM_ID = 1162972058
SHEET_NAME = "DRE-Granja-Dados"

def connect_gsheet():
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds_json = os.environ.get("GCP_CREDS")
    creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=scopes)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME)

def to_numeric_br(val):
    return pd.to_numeric(str(val).replace(',', '.'), errors='coerce')

def check_auth(update: Update):
    return update.effective_user.id == SEU_TELEGRAM_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_auth(update): 
        await update.message.reply_text("Acesso negado.")
        return
    await update.message.reply_text("🐔 DRE Granja Bot online!\n\n/lancar ovos mort racao receita custos despesas obs\n/dre - Resumo total\n/ajuda")

async def lancar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_auth(update):
        await update.message.reply_text("Acesso negado.")
        return
    try:
        args = context.args
        if len(args) < 7: raise ValueError("Formato: /lancar 684 2 165.8 800 200 0 texto")
        ovos, mort, racao, receita, custos, despesas = map(lambda x: x.replace(',', '.'), args[:6])
        obs = " ".join(args[6:])
        data = datetime.now().strftime('%Y-%m-%d')
        ss = connect_gsheet()
        ws = ss.worksheet('DIARIO')
        ws.append_row([data, ovos, mort, racao, receita, custos, despesas, obs])
        await update.message.reply_text(f"✅ Lançamento salvo {datetime.now().strftime('%d/%m/%Y')}\nOvos: {ovos} | Mort: {mort} | Ração: {racao}Kg")
    except Exception as e:
        await update.message.reply_text(f"❌ Erro: {e}\nFormato: /lancar 684 2 165.8 800 200 0 observação")

async def dre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_auth(update): return
    ss = connect_gsheet()
    df_d = pd.DataFrame(ss.worksheet('DIARIO').get_all_records())
    df_c = pd.DataFrame(ss.worksheet('CONFIG').get_all_records())
    if df_d.empty:
        await update.message.reply_text("Sem lançamentos ainda.")
        return
    preco_racao = to_numeric_br(df_c['Preco_Racao_Kg'].iloc[-1])
    for col in ['Ovos_Coletados', 'Consumo_Racao_Kg', 'Receita_Venda_Ovos', 'Custos_Dia', 'Despesas_Dia']:
        df_d[col] = df_d[col].apply(to_numeric_br).fillna(0)
    rec = df_d['Receita_Venda_Ovos'].sum()
    cus_racao = (df_d['Consumo_Racao_Kg'] * preco_racao).sum()
    cus_total = cus_racao + df_d['Custos_Dia'].sum()
    desp = df_d['Despesas_Dia'].sum()
    lucro = rec - cus_total - desp
    await update.message.reply_text(f"📊 DRE TOTAL\n\nReceita: R$ {rec:.2f}\nCustos: R$ {cus_total:.2f}\n- Ração: R$ {cus_racao:.2f}\nDespesas: R$ {desp:.2f}\nLucro: R$ {lucro:.2f}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ajuda", start))
    app.add_handler(CommandHandler("lancar", lancar))
    app.add_handler(CommandHandler("dre", dre))
    print("Bot rodando...")
    app.run_polling()