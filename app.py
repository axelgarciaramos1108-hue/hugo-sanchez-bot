import os
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📚 Escuela", callback_data="escuela")],
        [InlineKeyboardButton("💳 Tarjetas", callback_data="tarjetas")],
        [InlineKeyboardButton("💰 Préstamos", callback_data="prestamos")],
        [InlineKeyboardButton("🔁 Pagos Recurrentes", callback_data="recurrentes")],
        [InlineKeyboardButton("👥 Suscripciones", callback_data="suscripciones")],
        [InlineKeyboardButton("📊 Resumen", callback_data="resumen")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Hola Axel. Soy Hugo Sánchez.\n\n¿Qué quieres gestionar hoy?",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(
        f"Recibí: {text}\n\nAún estoy en fase inicial. Pronto entenderé lenguaje natural 😎"
    )

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot iniciado...")
    app.run_polling()

if __name__ == "__main__":
    main()
