import os
import json
from datetime import datetime
import gspread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ["TELEGRAM_TOKEN"]
SHEET_ID = os.environ["SHEET_ID"]
GSPREAD_JSON = os.environ["GSPREAD_JSON"]
URL = "https://dre-granja-bot.onrender.com"

creds = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(creds)
sheet = gc.open_by_key(SHEET_ID)

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

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("producao", producao))

    # PTB sobe o servidor e já cuida da porta
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        url_path=TOKEN,
        webhook_url=f"{URL}/{TOKEN}"
    )

if __name__ == "__main__":
    main()
